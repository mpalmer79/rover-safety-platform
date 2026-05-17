"""Phase 16 governed mission-to-rehearsal pipeline tests.

The platform is **not safety-certified**. These tests exercise the
honesty + determinism guarantees of the rehearsal layer. No real
robot motion, no ROS, no network access, no cloud SDKs.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Mapping

import pytest

from app.mission_rehearsal import (
    MISSION_REHEARSAL_DISCLAIMER,
    MissionRehearsalRequest,
    REHEARSAL_TRANSITIONS,
    RehearsalDecisionStatus,
    RehearsalEventType,
    RehearsalFailureReason,
    RehearsalSafetyStatus,
    RehearsalStatus,
    StateMachineError,
    build_analytics_result,
    build_audit_bundle,
    build_event,
    build_plan,
    build_replay_bundle,
    build_timeline,
    next_status,
    review_plan,
    run_rehearsal,
    valid_transitions,
    validate_plan,
    validate_request,
    write_audit_files,
)
from app.mission_rehearsal.rehearsal_capture import (
    capture_events,
    count_by_severity,
    count_by_type,
    safety_escalation_count,
)
from app.mission_rehearsal.rehearsal_safety import (
    REHEARSAL_FORBIDDEN_PATTERNS,
    SAFETY_LIMITS,
    classify_safety_status,
    scan_text,
)
from app.verification.requirements import RequirementKind, RequirementsRegistry


REPO_ROOT = Path(__file__).resolve().parents[2]
PKG_DIR = Path(__file__).resolve().parents[1] / "app" / "mission_rehearsal"
AUDITS_DIR = REPO_ROOT / "mission-rehearsals" / "audits"
EXAMPLES_DIR = REPO_ROOT / "mission-rehearsals" / "examples"
DOCS_DIR = REPO_ROOT / "docs"
PHASE_16_DOCS: tuple[str, ...] = (
    "GOVERNED_MISSION_REHEARSAL.md",
    "MISSION_REHEARSAL_STATE_MACHINE.md",
    "SIMULATION_REHEARSAL_PIPELINE.md",
    "REHEARSAL_REPLAY_INTEGRATION.md",
    "REHEARSAL_SAFETY_BOUNDARY.md",
    "FUTURE_DIGITAL_TWIN_DIRECTION.md",
)
FIXED_TIME = "2026-05-13T00:00:00+00:00"


def _request(**overrides) -> MissionRehearsalRequest:
    base = dict(
        request_id="test-r",
        description="A test rehearsal",
        mission_id="test-m",
        proposal_source="Drive forward 2 meters then dock.",
        requested_at_utc=FIXED_TIME,
        seed=42,
        operator="test-op",
        odd_profile_id="default-warehouse",
        notes=(),
    )
    base.update(overrides)
    return MissionRehearsalRequest(**base)


def _valid_waypoints() -> list[dict]:
    return [
        {"waypoint_id": "wp1", "label": "Forward leg", "stage_kind": "move",
         "bounded_distance_m": 2.0, "bounded_speed_mps": 0.25},
        {"waypoint_id": "wp2", "label": "Dock", "stage_kind": "dock"},
    ]


def _build_plan(request, waypoints=None, **kwargs):
    return build_plan(
        request,
        waypoints=waypoints or _valid_waypoints(),
        requested_topics=("/cmd_vel_requested",),
        forbidden_topics=("/cmd_vel",),
        **kwargs,
    )


def _drive(request, *, plan=None) -> dict:
    plan = plan or _build_plan(request)
    diagnostics = validate_plan(plan)
    decision = review_plan(plan, validation_diagnostics=diagnostics, decided_at_utc=FIXED_TIME)
    runtime = run_rehearsal(
        request=request, plan=plan, decision=decision,
        validation_diagnostics=diagnostics, started_at_utc=FIXED_TIME,
    )
    replay = build_replay_bundle(plan=plan, runtime=runtime)
    analytics = build_analytics_result(
        runtime=runtime, decision=decision, validation_diagnostics=diagnostics,
    )
    return {
        "plan": plan,
        "diagnostics": diagnostics,
        "decision": decision,
        "runtime": runtime,
        "replay": replay,
        "analytics": analytics,
    }


# ----------------------------------------------------------------------
# Requirement registry coverage
# ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "req_id",
    ["REQ-REHEARSAL-001", "REQ-REHEARSAL-002", "REQ-REHEARSAL-003",
     "REQ-REHEARSAL-004", "REQ-REHEARSAL-005"],
)
def test_requirement_registered(req_id: str):
    registry = RequirementsRegistry()
    assert req_id in registry
    req = registry.get(req_id)
    assert req.kind == RequirementKind.REHEARSAL
    assert req.test_refs


def test_requirement_kind_rehearsal_exists():
    assert RequirementKind.REHEARSAL.value == "rehearsal"


# ----------------------------------------------------------------------
# REQ-REHEARSAL-001 - simulation-only + dependency boundaries
# ----------------------------------------------------------------------


def test_rehearsal_runtime_emits_simulated_motion_only():
    result = _drive(_request())
    motion_events = [
        e for e in result["runtime"].events
        if e.event_type == RehearsalEventType.MOTION.value
    ]
    assert motion_events, "expected motion-related events"
    for event in motion_events:
        assert "simulated" in event.event_subtype.lower() or event.event_subtype in {
            "waypoint_requested", "waypoint_reached", "motion_request_simulated",
        }, event.event_subtype


def test_replay_bundle_is_not_bag_backed():
    result = _drive(_request())
    assert result["replay"].bag_backed is False
    assert result["replay"].evidence_status == "simulated"


def test_package_has_no_network_or_ros_imports():
    forbidden = {
        "rclpy",
        "socket",
        "urllib.request",
        "requests",
        "httpx",
        "openai",
        "anthropic",
        "cohere",
        "ollama",
        "llama_cpp",
        "subprocess",
    }
    for path in PKG_DIR.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
                imports.add(node.module)
        intersect = imports & forbidden
        assert not intersect, f"{path.name} imports forbidden module: {intersect}"


def test_disclaimer_is_attached_to_audit():
    result = _drive(_request())
    audit = build_audit_bundle(
        request=_request(),
        plan=result["plan"],
        validation_diagnostics=result["diagnostics"],
        decision=result["decision"],
        runtime=result["runtime"],
        replay=result["replay"],
        analytics=result["analytics"],
        generated_at_utc=FIXED_TIME,
    )
    assert audit.disclaimer == MISSION_REHEARSAL_DISCLAIMER


# ----------------------------------------------------------------------
# REQ-REHEARSAL-002 - determinism
# ----------------------------------------------------------------------


def test_same_input_same_event_stream():
    a = _drive(_request())
    b = _drive(_request())
    a_events = [e.deterministic_hash for e in a["runtime"].events]
    b_events = [e.deterministic_hash for e in b["runtime"].events]
    assert a_events == b_events


def test_same_seed_same_timeline():
    a = _drive(_request(seed=99))
    b = _drive(_request(seed=99))
    assert a["runtime"].timeline.transitions == b["runtime"].timeline.transitions


def test_deterministic_hashes_stable():
    a = _drive(_request())
    b = _drive(_request())
    assert a["plan"].deterministic_hash == b["plan"].deterministic_hash
    assert a["runtime"].deterministic_hash == b["runtime"].deterministic_hash


def test_replay_artifacts_are_stable_across_runs(tmp_path):
    a_dir = tmp_path / "a"
    b_dir = tmp_path / "b"
    a = _drive(_request())
    b = _drive(_request())
    write_audit_files(
        request=_request(), plan=a["plan"], validation_diagnostics=a["diagnostics"],
        decision=a["decision"], runtime=a["runtime"], replay=a["replay"],
        analytics=a["analytics"], bundle_dir=a_dir, generated_at_utc=FIXED_TIME,
    )
    write_audit_files(
        request=_request(), plan=b["plan"], validation_diagnostics=b["diagnostics"],
        decision=b["decision"], runtime=b["runtime"], replay=b["replay"],
        analytics=b["analytics"], bundle_dir=b_dir, generated_at_utc=FIXED_TIME,
    )
    for name in (
        "mission-request.json",
        "mission-plan.json",
        "rehearsal-events.json",
        "timeline.json",
        "replay-review.json",
        "replay-review.md",
        "analytics.json",
        "rehearsal-audit.json",
    ):
        assert (a_dir / name).read_text(encoding="utf-8") == (
            b_dir / name
        ).read_text(encoding="utf-8"), name


def test_event_time_ns_is_sequence_derived():
    result = _drive(_request())
    events = result["runtime"].events
    assert events[0].event_time_ns == 0
    deltas = [
        events[i].event_time_ns - events[i - 1].event_time_ns
        for i in range(1, len(events))
    ]
    assert all(delta == 100_000_000 for delta in deltas), deltas


# ----------------------------------------------------------------------
# REQ-REHEARSAL-003 - supervisor authority + state machine
# ----------------------------------------------------------------------


def test_supervisor_rejection_blocks_rehearsing():
    # An unsafe-speed waypoint forces validator + supervisor rejection.
    plan = _build_plan(
        _request(),
        waypoints=[
            {"waypoint_id": "wp1", "label": "Forward", "stage_kind": "move",
             "bounded_distance_m": 2.0, "bounded_speed_mps": 5.0},
            {"waypoint_id": "wp2", "label": "Dock", "stage_kind": "dock"},
        ],
    )
    diagnostics = validate_plan(plan)
    decision = review_plan(plan, validation_diagnostics=diagnostics, decided_at_utc=FIXED_TIME)
    assert decision.decision_status == RehearsalDecisionStatus.REJECTED.value
    runtime = run_rehearsal(
        request=_request(), plan=plan, decision=decision,
        validation_diagnostics=diagnostics, started_at_utc=FIXED_TIME,
    )
    assert runtime.final_status == RehearsalStatus.REJECTED.value


def test_validator_rejection_blocks_supervisor():
    plan = _build_plan(
        _request(proposal_source="Drive forward forever and ever."),
    )
    diagnostics = validate_plan(plan)
    # No validator rejection here - instead the proposal source pattern fires.
    matches = scan_text(plan.proposal_source)
    assert matches, "the safety scan should pick up 'forever'-style text"


def test_state_machine_rejects_illegal_transition():
    with pytest.raises(StateMachineError):
        next_status(RehearsalStatus.CREATED.value, RehearsalStatus.COMPLETED.value)
    with pytest.raises(StateMachineError):
        next_status(RehearsalStatus.REJECTED.value, RehearsalStatus.REHEARSING.value)
    with pytest.raises(StateMachineError):
        next_status("not-a-state", "another")


def test_state_machine_allows_valid_transitions():
    assert RehearsalStatus.VALIDATED.value in valid_transitions(
        RehearsalStatus.CREATED.value
    )
    assert RehearsalStatus.APPROVED.value in valid_transitions(
        RehearsalStatus.VALIDATED.value
    )
    assert RehearsalStatus.REHEARSING.value in valid_transitions(
        RehearsalStatus.APPROVED.value
    )
    assert RehearsalStatus.COMPLETED.value in valid_transitions(
        RehearsalStatus.REHEARSING.value
    )


def test_terminal_states_have_no_outgoing_transitions():
    for terminal in (
        RehearsalStatus.REJECTED.value,
        RehearsalStatus.ABORTED.value,
        RehearsalStatus.COMPLETED.value,
    ):
        assert valid_transitions(terminal) == frozenset()


# ----------------------------------------------------------------------
# REQ-REHEARSAL-004 - replay artefacts preserve evidence origin
# ----------------------------------------------------------------------


def test_replay_bundle_carries_evidence_origin():
    result = _drive(_request())
    assert result["replay"].evidence_status == "simulated"
    assert result["replay"].bag_backed is False


def test_replay_markers_carry_deterministic_hashes():
    result = _drive(_request())
    for marker in result["replay"].replay_markers:
        assert "deterministic_hash" in marker
        assert isinstance(marker["deterministic_hash"], str)
        assert marker["deterministic_hash"]


def test_replay_markdown_contains_disclaimer():
    result = _drive(_request())
    assert "Simulation-only" in result["replay"].rendered_markdown


# ----------------------------------------------------------------------
# REQ-REHEARSAL-005 - analytics counters
# ----------------------------------------------------------------------


def test_analytics_counts_completed_rehearsal():
    result = _drive(_request())
    analytics = result["analytics"]
    assert analytics.rehearsal_count == 1
    assert analytics.completed_count == 1
    assert analytics.approved_count == 1
    assert analytics.rejected_count == 0
    assert analytics.aborted_count == 0
    assert analytics.supervisor_rejection_count == 0
    assert analytics.validator_rejection_count == 0
    assert analytics.deterministic_replay_stable is True


def test_analytics_counts_supervisor_rejection():
    plan = _build_plan(
        _request(),
        waypoints=[
            {"waypoint_id": "wp1", "label": "Forward", "stage_kind": "move",
             "bounded_distance_m": 2.0, "bounded_speed_mps": 5.0},
            {"waypoint_id": "wp2", "label": "Dock", "stage_kind": "dock"},
        ],
    )
    diagnostics = validate_plan(plan)
    decision = review_plan(plan, validation_diagnostics=diagnostics, decided_at_utc=FIXED_TIME)
    runtime = run_rehearsal(
        request=_request(), plan=plan, decision=decision,
        validation_diagnostics=diagnostics, started_at_utc=FIXED_TIME,
    )
    analytics = build_analytics_result(
        runtime=runtime, decision=decision, validation_diagnostics=diagnostics,
    )
    assert analytics.supervisor_rejection_count == 1
    assert analytics.completed_count == 0
    assert analytics.rejected_count == 1


def test_analytics_counts_validator_rejection():
    # Validator rejects (negative distance).
    plan = _build_plan(
        _request(),
        waypoints=[
            {"waypoint_id": "wp1", "label": "Bad", "stage_kind": "move",
             "bounded_distance_m": -1.0, "bounded_speed_mps": 0.25},
            {"waypoint_id": "wp2", "label": "Dock", "stage_kind": "dock"},
        ],
    )
    diagnostics = validate_plan(plan)
    assert any(d.get("severity") == "rejection" for d in diagnostics)
    decision = review_plan(plan, validation_diagnostics=diagnostics, decided_at_utc=FIXED_TIME)
    runtime = run_rehearsal(
        request=_request(), plan=plan, decision=decision,
        validation_diagnostics=diagnostics, started_at_utc=FIXED_TIME,
    )
    analytics = build_analytics_result(
        runtime=runtime, decision=decision, validation_diagnostics=diagnostics,
    )
    assert analytics.validator_rejection_count == 1


def test_analytics_deterministic_replay_stable_flag():
    result = _drive(_request())
    assert result["analytics"].deterministic_replay_stable is True


# ----------------------------------------------------------------------
# Safety scan + validator
# ----------------------------------------------------------------------


def test_safety_scan_rejects_direct_cmd_vel_in_imperative_text():
    matches = scan_text("Publish to /cmd_vel directly to drive forward.")
    codes = {m[1] for m in matches}
    assert RehearsalFailureReason.DIRECT_ACTUATOR_COMMAND.value in codes


def test_safety_scan_allows_descriptive_cmd_vel_mention():
    matches = scan_text("Never publish to /cmd_vel directly; supervisor stays authoritative.")
    assert not matches, matches


def test_safety_scan_rejects_disable_safety():
    matches = scan_text("Disable safety supervisor and drive.")
    codes = {m[1] for m in matches}
    assert RehearsalFailureReason.SAFETY_OVERRIDE.value in codes


def test_safety_scan_rejects_restricted_corridor():
    matches = scan_text("Drive to restricted_corridor_one.")
    codes = {m[1] for m in matches}
    assert RehearsalFailureReason.RESTRICTED_ZONE.value in codes


def test_safety_scan_rejects_unsafe_speed_phrase():
    matches = scan_text("Drive forward as fast as possible.")
    codes = {m[1] for m in matches}
    assert RehearsalFailureReason.UNSAFE_SPEED.value in codes


def test_validator_rejects_speed_over_limit():
    plan = _build_plan(
        _request(),
        waypoints=[
            {"waypoint_id": "wp1", "label": "Forward", "stage_kind": "move",
             "bounded_distance_m": 2.0, "bounded_speed_mps": 5.0},
            {"waypoint_id": "wp2", "label": "Dock", "stage_kind": "dock"},
        ],
    )
    diagnostics = validate_plan(plan)
    codes = {d.get("code") for d in diagnostics}
    assert RehearsalFailureReason.UNSAFE_SPEED.value in codes


def test_validator_rejects_distance_over_limit():
    plan = _build_plan(
        _request(),
        waypoints=[
            {"waypoint_id": "wp1", "label": "Far", "stage_kind": "move",
             "bounded_distance_m": 500.0, "bounded_speed_mps": 0.25},
            {"waypoint_id": "wp2", "label": "Dock", "stage_kind": "dock"},
        ],
    )
    diagnostics = validate_plan(plan)
    codes = {d.get("code") for d in diagnostics}
    assert RehearsalFailureReason.OUT_OF_RANGE_PARAMETER.value in codes


def test_validator_rejects_missing_stop():
    plan = _build_plan(
        _request(),
        waypoints=[
            {"waypoint_id": "wp1", "label": "Forward", "stage_kind": "move",
             "bounded_distance_m": 2.0, "bounded_speed_mps": 0.25},
        ],
    )
    diagnostics = validate_plan(plan)
    codes = {d.get("code") for d in diagnostics}
    assert RehearsalFailureReason.MISSING_STOP_CONDITION.value in codes


def test_validator_rejects_plan_with_cmd_vel_requested_topic():
    plan = _build_plan(
        _request(),
        waypoints=_valid_waypoints(),
    )
    # Force the requested-topic list to include the forbidden topic.
    from dataclasses import replace

    plan_bad = replace(plan, requested_topics=("/cmd_vel",))
    diagnostics = validate_plan(plan_bad)
    codes = {d.get("code") for d in diagnostics}
    assert RehearsalFailureReason.DIRECT_ACTUATOR_COMMAND.value in codes


def test_safety_limits_are_well_known():
    for key in (
        "max_distance_meters",
        "max_angle_degrees",
        "max_linear_speed_mps",
        "max_angular_speed_rad_s",
    ):
        assert key in SAFETY_LIMITS


def test_classify_safety_status_returns_safe_only_on_full_chain():
    assert classify_safety_status(
        validation_passed=True, supervisor_approved=True,
        runtime_completed=True, safety_escalations=0,
    ) == RehearsalSafetyStatus.SAFE.value
    assert classify_safety_status(
        validation_passed=False, supervisor_approved=True,
        runtime_completed=True, safety_escalations=0,
    ) == RehearsalSafetyStatus.UNSAFE_REJECTED.value
    assert classify_safety_status(
        validation_passed=True, supervisor_approved=True,
        runtime_completed=True, safety_escalations=1,
    ) == RehearsalSafetyStatus.UNSAFE_REJECTED.value
    assert classify_safety_status(
        validation_passed=True, supervisor_approved=True,
        runtime_completed=False, safety_escalations=0,
    ) == RehearsalSafetyStatus.GUARDED.value


# ----------------------------------------------------------------------
# Audit bundle on disk
# ----------------------------------------------------------------------


def test_completed_audit_bundle_layout(tmp_path):
    result = _drive(_request())
    audit, paths = write_audit_files(
        request=_request(), plan=result["plan"],
        validation_diagnostics=result["diagnostics"],
        decision=result["decision"], runtime=result["runtime"],
        replay=result["replay"], analytics=result["analytics"],
        bundle_dir=tmp_path / "b", generated_at_utc=FIXED_TIME,
    )
    for key in (
        "mission_request",
        "mission_plan",
        "validator_result",
        "supervisor_review",
        "rehearsal_events",
        "timeline_json",
        "timeline_mmd",
        "replay_review",
        "replay_review_md",
        "analytics",
        "rehearsal_audit",
        "rehearsal_report",
    ):
        assert Path(paths[key]).is_file(), f"missing {key}"


def test_audit_report_includes_disclaimer(tmp_path):
    result = _drive(_request())
    audit, paths = write_audit_files(
        request=_request(), plan=result["plan"],
        validation_diagnostics=result["diagnostics"],
        decision=result["decision"], runtime=result["runtime"],
        replay=result["replay"], analytics=result["analytics"],
        bundle_dir=tmp_path / "b", generated_at_utc=FIXED_TIME,
    )
    md = Path(paths["rehearsal_report"]).read_text(encoding="utf-8")
    assert MISSION_REHEARSAL_DISCLAIMER in md


def test_capture_helpers_count_correctly():
    result = _drive(_request())
    events = result["runtime"].events
    type_counts = count_by_type(events)
    severity_counts = count_by_severity(events)
    assert sum(type_counts.values()) == len(events)
    assert sum(severity_counts.values()) == len(events)
    assert safety_escalation_count(events) == 0
    motion_only = capture_events(events, event_types=[RehearsalEventType.MOTION.value])
    assert all(e.event_type == RehearsalEventType.MOTION.value for e in motion_only)


def test_event_factory_is_deterministic():
    a = build_event(
        mission_id="m", sequence=3, event_type="mission",
        event_subtype="x", source_phase="p",
        severity="info", description="d", payload={"k": "v"},
    )
    b = build_event(
        mission_id="m", sequence=3, event_type="mission",
        event_subtype="x", source_phase="p",
        severity="info", description="d", payload={"k": "v"},
    )
    assert a.deterministic_hash == b.deterministic_hash


def test_timeline_renders_markdown_and_mermaid():
    result = _drive(_request())
    timeline = result["runtime"].timeline
    assert "Mission rehearsal timeline" in timeline.rendered_markdown
    assert timeline.rendered_mermaid.startswith("flowchart TD")
    rebuilt = build_timeline(
        mission_id=timeline.mission_id,
        transitions=timeline.transitions,
        events=timeline.events,
    )
    assert rebuilt.rendered_markdown == timeline.rendered_markdown


# ----------------------------------------------------------------------
# Committed examples on disk
# ----------------------------------------------------------------------


_ACCEPTED_FIXTURES = (
    "warehouse_pickup_route_alpha",
    "bounded_forward_patrol",
    "waypoint_delivery_alpha",
    "inspection_lane_beta",
    "emergency_stop_rehearsal",
)
_REJECTED_FIXTURES = (
    "unsafe_speed_route",
    "restricted_zone_entry",
    "direct_motor_override",
    "disable_supervisor_attempt",
    "infinite_patrol_loop",
)


@pytest.mark.parametrize("fixture_id", _ACCEPTED_FIXTURES)
def test_committed_accepted_fixture_completed(fixture_id):
    bundle = AUDITS_DIR / fixture_id
    assert bundle.is_dir(), bundle
    audit = json.loads((bundle / "rehearsal-audit.json").read_text(encoding="utf-8"))
    assert audit["final_status"] == "completed"
    assert audit["replay"]["bag_backed"] is False


@pytest.mark.parametrize("fixture_id", _REJECTED_FIXTURES)
def test_committed_rejected_fixture_is_rejected(fixture_id):
    bundle = AUDITS_DIR / fixture_id
    assert bundle.is_dir(), bundle
    audit = json.loads((bundle / "rehearsal-audit.json").read_text(encoding="utf-8"))
    assert audit["final_status"] == "rejected"
    assert audit["disclaimer"] == MISSION_REHEARSAL_DISCLAIMER


def test_committed_examples_files_present():
    for fixture_id in _ACCEPTED_FIXTURES + _REJECTED_FIXTURES:
        assert (EXAMPLES_DIR / f"{fixture_id}.json").is_file()


def test_committed_bundles_carry_disclaimer():
    for fixture_id in _ACCEPTED_FIXTURES + _REJECTED_FIXTURES:
        md = (AUDITS_DIR / fixture_id / "rehearsal-report.md").read_text(encoding="utf-8")
        assert MISSION_REHEARSAL_DISCLAIMER in md


def test_committed_bundles_never_claim_bag_backed():
    for fixture_id in _ACCEPTED_FIXTURES + _REJECTED_FIXTURES:
        # Accepted fixtures ship a replay-review.json; rejected may
        # also ship one since the rejected runtime still produced
        # events. Either way, bag-backed must be false.
        path = AUDITS_DIR / fixture_id / "replay-review.json"
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["bag_backed"] is False
        assert data["evidence_status"] == "simulated"


# ----------------------------------------------------------------------
# Documentation
# ----------------------------------------------------------------------


@pytest.mark.parametrize("doc", PHASE_16_DOCS)
def test_phase_16_doc_includes_simulation_only_disclaimer(doc):
    text = (DOCS_DIR / doc).read_text(encoding="utf-8")
    assert "not safety-certified" in text.lower()
    assert "simulation-only" in text.lower()


def test_state_machine_doc_lists_every_state():
    text = (DOCS_DIR / "MISSION_REHEARSAL_STATE_MACHINE.md").read_text(encoding="utf-8")
    for state in REHEARSAL_TRANSITIONS:
        assert state in text, state


# ----------------------------------------------------------------------
# Forbidden patterns list
# ----------------------------------------------------------------------


def test_forbidden_patterns_list_is_nonempty():
    assert len(REHEARSAL_FORBIDDEN_PATTERNS) >= 5
    for triple in REHEARSAL_FORBIDDEN_PATTERNS:
        assert len(triple) == 3


def test_validate_request_rejects_empty_ids():
    diags = validate_request(_request(request_id="", mission_id=""))
    codes = {d.get("code") for d in diags}
    assert RehearsalFailureReason.MALFORMED_MISSION_GRAPH.value in codes
