"""Phase 7 replay review tests.

Tests run without ROS / Gazebo / Foxglove. They exercise:

* bag indexing — missing dir, metadata-only, MCAP/db3 detection,
  topic inventory parsing, no fabrication when metadata is unreadable;
* manifest generation — expected topics, missing-topic reporting,
  static-only handling;
* marker generation — first fault, safety transitions, partial
  alignment, never-fabricated;
* Foxglove session — valid JSON, panel hints, layout pointer, no
  runtime dependency;
* validator + aggregate status — missing bag, partial, complete,
  static-only;
* CLIs — build, validate, list;
* GitHub workflow shape — self-hosted, dispatch-only.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import pytest

import yaml


_REPO_ROOT = Path(__file__).resolve().parents[2]
_TOOLS_DIR = _REPO_ROOT / "rover_ws" / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))


from app.replay_review import (  # noqa: E402
    BagArtifact,
    BagIndex,
    EXPECTED_REPLAY_TOPICS,
    FoxglovePanelHint,
    FoxgloveSession,
    REPLAY_CERTIFICATION_DISCLAIMER,
    ReplayEvidenceOrigin,
    ReplayExecutionStatus,
    ReplayMarker,
    ReplayReviewManifest,
    ReplayValidationStatus,
    aggregate_status,
    alignment_status,
    build_foxglove_session,
    build_manifest,
    build_markers,
    build_replay_review,
    build_report,
    candidate_bag_roots,
    default_replay_topics,
    index_bag_candidates,
    index_bag_directory,
    is_bag_file,
    merge_inventory,
    render_manifest_md,
    render_report_md,
    validate_replay_review,
    write_session,
)


CANONICAL_INCIDENT_DIR = _REPO_ROOT / "incidents" / "canonical-stale-lidar"
CANONICAL_LAYOUT = _REPO_ROOT / "foxglove" / "layouts" / "incident-review-layout.json"


# ---------------------------------------------------------------------------
# Bag indexing.
# ---------------------------------------------------------------------------


def test_bag_index_missing_dir(tmp_path: Path) -> None:
    index = index_bag_directory(tmp_path / "ghost")
    assert index.status == ReplayExecutionStatus.MISSING_BAG
    assert any("does not exist" in n for n in index.notes)
    assert not index.has_bag_chunks
    assert not index.has_metadata


def test_bag_index_empty_dir(tmp_path: Path) -> None:
    bag_root = tmp_path / "bags"
    bag_root.mkdir()
    index = index_bag_directory(bag_root)
    assert index.status == ReplayExecutionStatus.MISSING_BAG
    assert any("no bag chunks" in n for n in index.notes)


def test_bag_index_detects_mcap(tmp_path: Path) -> None:
    bag_root = tmp_path / "bags"
    bag_root.mkdir()
    (bag_root / "rosbag.mcap").write_bytes(b"fake bag content")
    index = index_bag_directory(bag_root)
    assert index.has_bag_chunks
    assert any(a.kind == "mcap" for a in index.artifacts)
    # metadata absent -> partial.
    assert index.status == ReplayExecutionStatus.PARTIAL


def test_bag_index_detects_db3_and_metadata(tmp_path: Path) -> None:
    bag_root = tmp_path / "bags"
    bag_root.mkdir()
    (bag_root / "rosbag.db3").write_bytes(b"fake bag content")
    (bag_root / "metadata.yaml").write_text(
        "rosbag2_bagfile_information:\n"
        "  starting_time:\n"
        "    nanoseconds_since_epoch: 1000000000\n"
        "  duration:\n"
        "    nanoseconds: 5000000000\n"
        "  topics_with_message_count:\n"
        "    - topic_metadata:\n"
        "        name: /safety/state\n"
        "      message_count: 100\n"
        "    - topic_metadata:\n"
        "        name: /cmd_vel_authorized\n"
        "      message_count: 50\n",
        encoding="utf-8",
    )
    index = index_bag_directory(bag_root)
    assert index.has_bag_chunks
    assert index.has_metadata
    assert index.status == ReplayExecutionStatus.READY
    assert index.inventory_topics == ("/safety/state", "/cmd_vel_authorized")
    assert index.message_counts["/safety/state"] == 100
    assert index.start_time_ns == 1_000_000_000
    assert index.end_time_ns == 6_000_000_000


def test_bag_index_metadata_only(tmp_path: Path) -> None:
    bag_root = tmp_path / "bags"
    bag_root.mkdir()
    (bag_root / "metadata.yaml").write_text(
        "rosbag2_bagfile_information: {}\n", encoding="utf-8"
    )
    index = index_bag_directory(bag_root)
    assert index.has_metadata
    assert not index.has_bag_chunks
    assert index.status == ReplayExecutionStatus.PARTIAL


def test_bag_index_does_not_fabricate_inventory(tmp_path: Path) -> None:
    """An unreadable metadata.yaml must not invent topics."""

    bag_root = tmp_path / "bags"
    bag_root.mkdir()
    (bag_root / "rosbag.mcap").write_bytes(b"")
    (bag_root / "metadata.yaml").write_text("not: valid: yaml: ::: !!", encoding="utf-8")
    index = index_bag_directory(bag_root)
    assert index.inventory_topics == ()


def test_is_bag_file() -> None:
    assert is_bag_file(Path("foo.mcap"))
    assert is_bag_file(Path("foo.db3"))
    assert not is_bag_file(Path("metadata.yaml"))
    assert not is_bag_file(Path("foo.txt"))


def test_candidate_bag_roots_lists_documented_locations(tmp_path: Path) -> None:
    candidates = candidate_bag_roots(
        incident_dir=tmp_path / "incident",
        runtime_run_dir=tmp_path / "runtime",
        runs_root=tmp_path / "runs",
        run_id="x",
    )
    names = {p.name for p in candidates}
    assert "bags" in names
    assert any("incident" in str(c) for c in candidates)
    assert any("runtime" in str(c) for c in candidates)
    assert any("runs" in str(c) for c in candidates)


def test_merge_inventory_dedupes() -> None:
    a = BagIndex(bag_root=Path("/a"), inventory_topics=("/x", "/y"))
    b = BagIndex(bag_root=Path("/b"), inventory_topics=("/y", "/z"))
    merged = merge_inventory([a, b])
    assert merged == ("/x", "/y", "/z")


# ---------------------------------------------------------------------------
# Manifest.
# ---------------------------------------------------------------------------


def _fake_incident(
    *,
    incident_id: str = "test",
    evidence_status: str = "complete",
    safety_states: tuple[str, ...] = ("ACTIVE_NORMAL", "SAFE_STOP"),
    timeline_entries: Optional[list[dict]] = None,
    cause_confidence: str = "direct",
) -> dict:
    if timeline_entries is None:
        timeline_entries = [
            {
                "category": "fault_injection",
                "event_type": "fault_injection.fired",
                "attributes": {"fault_type": "stale_lidar", "fault_id": "f1"},
                "evidence_origin": "scenario-evidence",
                "sim_time_ns": 1_000_000_000,
                "relative_time_ms": 0,
                "raw_reference": "evt-001",
                "source_file": "events.jsonl",
                "safety_state": "BOOT",
            },
            {
                "category": "safety_transition",
                "event_type": "safety_transition.entered",
                "attributes": {"to_state": "SAFE_STOP"},
                "evidence_origin": "scenario-evidence",
                "sim_time_ns": 2_000_000_000,
                "relative_time_ms": 1000,
                "raw_reference": "evt-002",
                "source_file": "events.jsonl",
                "safety_state": "SAFE_STOP",
            },
            {
                "category": "motion_arbitration",
                "event_type": "motion_arbitration.summary",
                "attributes": {"zeroed_count": 5, "request_count": 10},
                "evidence_origin": "scenario-evidence",
                "sim_time_ns": None,
                "relative_time_ms": None,
                "raw_reference": "command-audit.json",
                "source_file": "command-audit.json",
                "safety_state": None,
            },
        ]
    return {
        "incident_id": incident_id,
        "run_id": "rid-x",
        "scenario_id": "sid-x",
        "evidence_status": evidence_status,
        "safety_states": list(safety_states),
        "outcome": "safe_stop_success",
        "cause": {"label": "stale_lidar_chain", "confidence": cause_confidence},
        "timeline": {
            "first_fault_index": 0,
            "first_safety_transition_index": 1,
            "first_command_intervention_index": 2,
            "terminal_index": 1,
            "entries": timeline_entries,
        },
    }


def test_manifest_lists_expected_topics() -> None:
    incident = _fake_incident()
    manifest = build_manifest(
        incident=incident,
        bag_indices=(),
        foxglove_layout_path="foxglove/layouts/incident-review-layout.json",
        foxglove_session_path="foxglove-session.json",
        timeline_marker_count=4,
    )
    names = {t.name for t in manifest.expected_topics}
    for required in (
        "/cmd_vel_authorized",
        "/safety/state",
        "/safety/events",
        "/system/health",
    ):
        assert required in names


def test_manifest_records_missing_topics(tmp_path: Path) -> None:
    incident = _fake_incident()
    bag_root = tmp_path / "bags"
    bag_root.mkdir()
    (bag_root / "rosbag.mcap").write_bytes(b"")
    (bag_root / "metadata.yaml").write_text(
        "rosbag2_bagfile_information:\n"
        "  topics_with_message_count:\n"
        "    - topic_metadata:\n"
        "        name: /safety/state\n"
        "      message_count: 1\n",
        encoding="utf-8",
    )
    bag_indices = index_bag_candidates([bag_root])
    manifest = build_manifest(
        incident=incident,
        bag_indices=bag_indices,
        foxglove_layout_path=str(CANONICAL_LAYOUT),
        foxglove_session_path="foxglove-session.json",
        timeline_marker_count=2,
    )
    assert "/cmd_vel_authorized" in manifest.missing_topics
    assert "/safety/state" not in manifest.missing_topics


def test_manifest_no_missing_topics_when_no_inventory_observed() -> None:
    """A manifest with no bag inventory must not synthesize missing topics."""

    incident = _fake_incident()
    manifest = build_manifest(
        incident=incident,
        bag_indices=(),
        foxglove_layout_path="x",
        foxglove_session_path="y",
        timeline_marker_count=0,
    )
    assert manifest.missing_topics == ()


def test_manifest_static_only_keeps_static_only_status() -> None:
    incident = _fake_incident(
        evidence_status="static_only",
        timeline_entries=[],
    )
    manifest = build_manifest(
        incident=incident,
        bag_indices=(),
        foxglove_layout_path="x",
        foxglove_session_path="y",
        timeline_marker_count=0,
    )
    assert manifest.bag_status == ReplayExecutionStatus.STATIC_ONLY


def test_manifest_includes_known_limitations() -> None:
    incident = _fake_incident()
    manifest = build_manifest(
        incident=incident,
        bag_indices=(),
        foxglove_layout_path="x",
        foxglove_session_path="y",
        timeline_marker_count=0,
    )
    assert manifest.known_limitations
    # The disclaimer is markdown-bolded ("**not** safety-certified");
    # check the underlying phrase rather than the exact substring.
    assert any("safety-certified" in line.lower() for line in manifest.known_limitations)


def test_manifest_md_renders_disclaimer_and_sections() -> None:
    incident = _fake_incident()
    manifest = build_manifest(
        incident=incident,
        bag_indices=(),
        foxglove_layout_path="x",
        foxglove_session_path="y",
        timeline_marker_count=0,
    )
    md = render_manifest_md(manifest)
    assert "Replay Review Manifest" in md
    assert "not safety-certified" in md
    assert "Expected topics" in md


# ---------------------------------------------------------------------------
# Markers.
# ---------------------------------------------------------------------------


def test_markers_preserve_evidence_origin() -> None:
    incident = _fake_incident()
    markers = build_markers(incident=incident)
    assert any(m.marker_id == "first_fault" for m in markers)
    assert all(m.evidence_origin == ReplayEvidenceOrigin.SCENARIO_EVIDENCE for m in markers)
    assert any(m.alignment == "exact" for m in markers)


def test_markers_partial_alignment_when_sim_time_missing() -> None:
    """A timeline entry without sim_time_ns must yield ``alignment=partial`` when relative time exists."""

    incident = _fake_incident(
        timeline_entries=[
            {
                "category": "fault_injection",
                "event_type": "fault_injection.fired",
                "attributes": {"fault_type": "stale_lidar"},
                "evidence_origin": "scenario-evidence",
                "sim_time_ns": None,
                "relative_time_ms": 100,
                "raw_reference": "evt-001",
                "source_file": "events.jsonl",
                "safety_state": "BOOT",
            },
            {
                "category": "safety_transition",
                "event_type": "safety_transition.entered",
                "attributes": {"to_state": "SAFE_STOP"},
                "evidence_origin": "scenario-evidence",
                "sim_time_ns": None,
                "relative_time_ms": 1100,
                "raw_reference": "evt-002",
                "source_file": "events.jsonl",
                "safety_state": "SAFE_STOP",
            },
        ]
    )
    markers = build_markers(incident=incident)
    assert markers
    assert all(m.alignment == "partial" for m in markers)


def test_markers_never_fabricated() -> None:
    """If the timeline indices are absent, no marker is emitted."""

    incident = {
        "incident_id": "x",
        "evidence_status": "missing",
        "outcome": "inconclusive",
        "safety_states": [],
        "timeline": {
            "entries": [],
            "first_fault_index": None,
            "first_safety_transition_index": None,
            "first_command_intervention_index": None,
            "terminal_index": None,
        },
    }
    markers = build_markers(incident=incident)
    assert markers == []


def test_alignment_status_aggregates() -> None:
    a = ReplayMarker(
        marker_id="a",
        label="a",
        description="a",
        timeline_index=0,
        relative_time_ms=0,
        sim_time_ns=1,
        source_event_id="x",
        source_file="y",
        confidence="direct",
        evidence_origin=ReplayEvidenceOrigin.SCENARIO_EVIDENCE,
        alignment="exact",
    )
    b = ReplayMarker(
        marker_id="b",
        label="b",
        description="b",
        timeline_index=1,
        relative_time_ms=10,
        sim_time_ns=None,
        source_event_id="x",
        source_file="y",
        confidence="moderate",
        evidence_origin=ReplayEvidenceOrigin.SCENARIO_EVIDENCE,
        alignment="partial",
    )
    assert alignment_status([a]) == "exact"
    assert alignment_status([a, b]) == "partial"
    assert alignment_status([]) == "no_markers"


# ---------------------------------------------------------------------------
# Foxglove session.
# ---------------------------------------------------------------------------


def test_foxglove_session_is_valid_json(tmp_path: Path) -> None:
    incident = _fake_incident()
    markers = build_markers(incident=incident)
    session = build_foxglove_session(
        incident_id="x",
        layout_path="foxglove/layouts/incident-review-layout.json",
        recommended_data_source="local file",
        markers=markers,
    )
    target = tmp_path / "session.json"
    write_session(session, path=target)
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["incident_id"] == "x"
    assert payload["schema_version"] == "rover-replay-review/1"


def test_foxglove_session_lists_expected_panels() -> None:
    incident = _fake_incident()
    markers = build_markers(incident=incident)
    session = build_foxglove_session(
        incident_id="x",
        layout_path="foxglove/layouts/incident-review-layout.json",
        recommended_data_source="local file",
        markers=markers,
    )
    panel_topics = {t for hint in session.panel_hints for t in hint.topics}
    for required in (
        "/safety/state",
        "/cmd_vel_authorized",
        "/cmd_vel_requested",
        "/system/health",
    ):
        assert required in panel_topics


def test_foxglove_session_does_not_require_runtime() -> None:
    """The session is plain JSON; no Foxglove import needed for tests."""

    payload = json.loads(CANONICAL_LAYOUT.read_text(encoding="utf-8"))
    assert "configById" in payload  # canonical Foxglove layout shape


# ---------------------------------------------------------------------------
# Validator + aggregate.
# ---------------------------------------------------------------------------


def _bundle_for_test(
    tmp_path: Path,
    *,
    bag_status: ReplayExecutionStatus,
    evidence_status: str = "complete",
):
    incident_dir = tmp_path / "incidents" / "x"
    incident_dir.mkdir(parents=True)
    incident = _fake_incident(evidence_status=evidence_status)
    (incident_dir / "incident-report.json").write_text(
        json.dumps(incident), encoding="utf-8"
    )
    (incident_dir / "timeline.json").write_text(
        json.dumps(incident["timeline"]), encoding="utf-8"
    )
    bag_indices = ()
    if bag_status == ReplayExecutionStatus.READY:
        bags_dir = incident_dir / "bags"
        bags_dir.mkdir()
        (bags_dir / "rosbag.mcap").write_bytes(b"")
        (bags_dir / "metadata.yaml").write_text(
            "rosbag2_bagfile_information:\n"
            "  topics_with_message_count:\n"
            + "".join(
                f"    - topic_metadata:\n        name: {t}\n      message_count: 1\n"
                for t in EXPECTED_REPLAY_TOPICS
            ),
            encoding="utf-8",
        )
        bag_indices = index_bag_candidates([bags_dir])
    elif bag_status == ReplayExecutionStatus.PARTIAL:
        bags_dir = incident_dir / "bags"
        bags_dir.mkdir()
        (bags_dir / "rosbag.mcap").write_bytes(b"")
        bag_indices = index_bag_candidates([bags_dir])
    layout_path = CANONICAL_LAYOUT
    manifest = build_manifest(
        incident=incident,
        bag_indices=bag_indices,
        foxglove_layout_path=str(layout_path),
        foxglove_session_path="foxglove-session.json",
        timeline_marker_count=4,
    )
    markers = tuple(build_markers(incident=incident))
    session = build_foxglove_session(
        incident_id=incident["incident_id"],
        layout_path=str(layout_path),
        recommended_data_source="local file",
        markers=markers,
    )
    return incident_dir, manifest, markers, session


def test_validator_flags_missing_bag(tmp_path: Path) -> None:
    incident_dir, manifest, markers, session = _bundle_for_test(
        tmp_path, bag_status=ReplayExecutionStatus.MISSING_BAG
    )
    results = validate_replay_review(
        incident_dir=incident_dir,
        manifest=manifest,
        session=session,
        markers=markers,
        layout_file=CANONICAL_LAYOUT,
    )
    assert any(
        r.name == "bag_artefacts_present"
        and r.status == ReplayValidationStatus.NOT_EXECUTED
        for r in results
    )
    aggregate = aggregate_status(manifest=manifest, validations=results)
    assert aggregate == ReplayExecutionStatus.MISSING_BAG


def test_validator_static_only_remains_static_only(tmp_path: Path) -> None:
    incident_dir, manifest, markers, session = _bundle_for_test(
        tmp_path,
        bag_status=ReplayExecutionStatus.STATIC_ONLY,
        evidence_status="static_only",
    )
    results = validate_replay_review(
        incident_dir=incident_dir,
        manifest=manifest,
        session=session,
        markers=markers,
        layout_file=CANONICAL_LAYOUT,
    )
    aggregate = aggregate_status(manifest=manifest, validations=results)
    assert aggregate == ReplayExecutionStatus.STATIC_ONLY


def test_validator_ready_when_bag_complete(tmp_path: Path) -> None:
    incident_dir, manifest, markers, session = _bundle_for_test(
        tmp_path, bag_status=ReplayExecutionStatus.READY
    )
    results = validate_replay_review(
        incident_dir=incident_dir,
        manifest=manifest,
        session=session,
        markers=markers,
        layout_file=CANONICAL_LAYOUT,
    )
    aggregate = aggregate_status(manifest=manifest, validations=results)
    assert aggregate in {
        ReplayExecutionStatus.READY,
        ReplayExecutionStatus.PARTIAL,
    }
    assert any(r.name == "expected_topics_present" for r in results)


def test_validator_partial_when_metadata_missing(tmp_path: Path) -> None:
    incident_dir, manifest, markers, session = _bundle_for_test(
        tmp_path, bag_status=ReplayExecutionStatus.PARTIAL
    )
    aggregate = aggregate_status(
        manifest=manifest,
        validations=validate_replay_review(
            incident_dir=incident_dir,
            manifest=manifest,
            session=session,
            markers=markers,
            layout_file=CANONICAL_LAYOUT,
        ),
    )
    assert aggregate == ReplayExecutionStatus.PARTIAL


def test_reporter_includes_status_section() -> None:
    incident = _fake_incident()
    manifest = build_manifest(
        incident=incident,
        bag_indices=(),
        foxglove_layout_path="x",
        foxglove_session_path="y",
        timeline_marker_count=0,
    )
    session = build_foxglove_session(
        incident_id="x",
        layout_path="x",
        recommended_data_source="",
        markers=(),
    )
    report = build_report(
        manifest=manifest,
        session=session,
        markers=(),
        validations=(),
        replay_execution_status=ReplayExecutionStatus.MISSING_BAG,
    )
    md = render_report_md(report)
    assert "Replay Review Report" in md
    assert REPLAY_CERTIFICATION_DISCLAIMER in md
    assert "Validation results" in md
    assert "Expected topics" in md
    assert "Operator checklist" in md


# ---------------------------------------------------------------------------
# Bundle orchestrator + canonical incident.
# ---------------------------------------------------------------------------


def test_build_replay_review_against_canonical_stale_lidar(tmp_path: Path) -> None:
    """End-to-end orchestrator run on the committed canonical bundle."""

    # Copy the canonical incident dir into tmp_path so the test does
    # not mutate the committed copy.
    src = CANONICAL_INCIDENT_DIR
    dst = tmp_path / "incident"
    dst.mkdir()
    for path in src.iterdir():
        if path.is_file():
            (dst / path.name).write_bytes(path.read_bytes())

    bundle = build_replay_review(incident_dir=dst)
    # No bag exists in tmp_path -> missing_bag.
    assert bundle.manifest.bag_status == ReplayExecutionStatus.MISSING_BAG
    assert bundle.report.replay_execution_status == ReplayExecutionStatus.MISSING_BAG
    assert bundle.report.evidence_origin in {
        ReplayEvidenceOrigin.SCENARIO_EVIDENCE,
        ReplayEvidenceOrigin.UNKNOWN,
    }
    # Bundle files written.
    for name in (
        "replay-review-manifest.json",
        "replay-review.md",
        "replay-markers.json",
        "foxglove-session.json",
        "replay-review-report.json",
        "replay-review-report.md",
    ):
        assert (dst / name).exists(), name


def test_build_replay_review_with_bag(tmp_path: Path) -> None:
    src = CANONICAL_INCIDENT_DIR
    dst = tmp_path / "incident"
    dst.mkdir()
    for path in src.iterdir():
        if path.is_file():
            (dst / path.name).write_bytes(path.read_bytes())

    # Plant a complete fake bag.
    bags = dst / "bags"
    bags.mkdir()
    (bags / "rosbag.mcap").write_bytes(b"")
    (bags / "metadata.yaml").write_text(
        "rosbag2_bagfile_information:\n"
        "  topics_with_message_count:\n"
        + "".join(
            f"    - topic_metadata:\n        name: {t}\n      message_count: 1\n"
            for t in EXPECTED_REPLAY_TOPICS
        ),
        encoding="utf-8",
    )
    bundle = build_replay_review(incident_dir=dst)
    assert bundle.manifest.bag_status == ReplayExecutionStatus.READY
    assert bundle.report.evidence_origin == ReplayEvidenceOrigin.BAG_BACKED
    assert not bundle.manifest.missing_topics


# ---------------------------------------------------------------------------
# CLIs.
# ---------------------------------------------------------------------------


def _import_cli(name: str):
    import importlib

    return importlib.import_module(name)


def test_cli_build_replay_review_bundle_writes_outputs(tmp_path: Path) -> None:
    src = CANONICAL_INCIDENT_DIR
    dst = tmp_path / "incident"
    dst.mkdir()
    for path in src.iterdir():
        if path.is_file():
            (dst / path.name).write_bytes(path.read_bytes())
    cli = _import_cli("build_replay_review_bundle")
    rc = cli.main(
        [
            "--incident",
            str(dst),
            "--foxglove-layout",
            str(CANONICAL_LAYOUT),
        ]
    )
    assert rc == 0
    assert (dst / "replay-review-manifest.json").exists()
    assert (dst / "replay-review-report.md").exists()


def test_cli_validate_replay_review(tmp_path: Path) -> None:
    src = CANONICAL_INCIDENT_DIR
    dst = tmp_path / "incident"
    dst.mkdir()
    for path in src.iterdir():
        if path.is_file():
            (dst / path.name).write_bytes(path.read_bytes())
    build_cli = _import_cli("build_replay_review_bundle")
    build_cli.main(
        ["--incident", str(dst), "--foxglove-layout", str(CANONICAL_LAYOUT)]
    )
    validate_cli = _import_cli("validate_replay_review")
    rc = validate_cli.main(
        ["--incident", str(dst), "--foxglove-layout", str(CANONICAL_LAYOUT)]
    )
    # Missing bag is not a "failed" - exit code is 0 even though
    # several checks returned not_executed.
    assert rc == 0


def test_cli_list_replay_reviews(tmp_path: Path) -> None:
    incidents_root = tmp_path / "incidents"
    src = CANONICAL_INCIDENT_DIR
    dst = incidents_root / "x"
    dst.mkdir(parents=True)
    for path in src.iterdir():
        if path.is_file():
            (dst / path.name).write_bytes(path.read_bytes())
    build_cli = _import_cli("build_replay_review_bundle")
    build_cli.main(
        ["--incident", str(dst), "--foxglove-layout", str(CANONICAL_LAYOUT)]
    )
    list_cli = _import_cli("list_replay_reviews")
    rc = list_cli.main(
        [
            "--incidents-root",
            str(incidents_root),
            "--md-out",
            str(tmp_path / "REPLAY_REVIEW_INDEX.md"),
        ]
    )
    assert rc == 0
    md = (tmp_path / "REPLAY_REVIEW_INDEX.md").read_text(encoding="utf-8")
    assert "Replay Review Index" in md


# ---------------------------------------------------------------------------
# GitHub workflow shape.
# ---------------------------------------------------------------------------


def test_replay_workflow_uses_self_hosted_runner() -> None:
    path = _REPO_ROOT / ".github" / "workflows" / "ros-jazzy-replay-review.yml"
    text = path.read_text(encoding="utf-8")
    assert "self-hosted" in text
    assert "ros-jazzy" in text


def test_replay_workflow_is_dispatch_only() -> None:
    path = _REPO_ROOT / ".github" / "workflows" / "ros-jazzy-replay-review.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    triggers = data.get("on") or data.get(True) or {}
    if isinstance(triggers, dict):
        keys = set(triggers.keys())
    elif isinstance(triggers, list):
        keys = set(triggers)
    else:
        keys = {triggers}
    assert "workflow_dispatch" in keys
    # No automatic push / PR triggers - live replay is opt-in only.
    assert "push" not in keys
    assert "pull_request" not in keys


# ---------------------------------------------------------------------------
# Defaults.
# ---------------------------------------------------------------------------


def test_default_replay_topics_match_expected_set() -> None:
    topics = default_replay_topics()
    names = tuple(t.name for t in topics)
    assert names == EXPECTED_REPLAY_TOPICS


def test_canonical_layout_committed() -> None:
    assert CANONICAL_LAYOUT.exists()
    payload = json.loads(CANONICAL_LAYOUT.read_text(encoding="utf-8"))
    assert "configById" in payload
