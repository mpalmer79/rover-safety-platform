"""Phase 15B local LLM skill candidate provider tests.

The platform is **not safety-certified**. These tests exercise the
honesty + policy guarantees of the layer:

* default mode is ``disabled``;
* cloud and HTTPS endpoints are rejected;
* local providers require an explicit opt-in flag AND an enabled
  config;
* sanitizer rules reject every forbidden pattern;
* sanitizer rejection skips the Phase 15A validator;
* accepted candidates pass BOTH the sanitizer AND the validator
  and emit a code-card payload;
* every audit bundle carries the verbatim disclaimer;
* the package imports no cloud SDKs or network libraries.

No test requires a real model, ROS, Gazebo, or network access.
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import pytest

from app.skill_llm_provider import (
    DEFAULT_PROVIDER_MODE,
    FIXTURE_REGISTRY,
    FORBIDDEN_FRAGMENTS,
    KNOWN_PROVIDER_MODES,
    PROVIDER_MODES,
    SKILL_LLM_DISCLAIMER,
    SkillLLMCandidate,
    SkillLLMProviderConfig,
    SkillLLMRequest,
    audit_to_dict,
    build_audit_bundle,
    config_to_dict,
    is_loopback_url,
    list_fixture_ids,
    load_provider_config,
    parse_provider_config,
    require_local_endpoint,
    resolve_provider,
    run_skill_llm_pipeline,
    sanitize_candidate,
    write_audit_files,
)
from app.skill_llm_provider.adapter import _candidate_from_payload
from app.skill_llm_provider.models import (
    CandidateConfidence,
    CandidateRejectionReason,
    CandidateStatus,
    ProviderMode,
    ProviderStatus,
)
from app.skill_llm_provider.provider import ProviderError, evaluate_local_opt_in
from app.skill_llm_provider.validator_bridge import run_skill_validator_bridge
from app.verification.requirements import RequirementKind, RequirementsRegistry


REPO_ROOT = Path(__file__).resolve().parents[2]
PKG_DIR = Path(__file__).resolve().parents[1] / "app" / "skill_llm_provider"
CONFIG_DIR = REPO_ROOT / "skill-llm-candidates" / "config"
AUDITS_DIR = REPO_ROOT / "skill-llm-candidates" / "audits"
EXAMPLES_DIR = REPO_ROOT / "skill-llm-candidates" / "examples"
DOCS_DIR = REPO_ROOT / "docs"
PHASE_15B_DOCS: tuple[str, ...] = (
    "LOCAL_LLM_SKILL_PROVIDER.md",
    "LOCAL_LLM_PROVIDER_SAFETY_BOUNDARY.md",
    "LOCAL_LLM_SKILL_PROMPT_CONTRACT.md",
    "SKILL_LLM_CANDIDATE_AUDITS.md",
    "FUTURE_LOCAL_MODEL_OPERATIONS.md",
)
FIXED_TIME = "2026-05-13T00:00:00+00:00"


def _request(text: str = "Move my robot 6 feet forward", request_id: str = "p-test") -> SkillLLMRequest:
    return SkillLLMRequest(
        request_id=request_id,
        text=text,
        language="python_ros2",
        requested_at_utc=FIXED_TIME,
    )


def _config(mode: str, *, enabled: bool = False, endpoint: str = "", extra: dict | None = None) -> SkillLLMProviderConfig:
    return SkillLLMProviderConfig(
        mode=mode,
        enabled=enabled,
        provider_name=f"{mode}-provider",
        model_name="",
        endpoint=endpoint,
        extra=extra or {},
    )


def _fixture_config(fixture_id: str) -> SkillLLMProviderConfig:
    return _config("fixture", enabled=True, extra={"fixture_id": fixture_id})


def _run(text: str = "x", *, fixture_id: str | None = None):
    cfg = _fixture_config(fixture_id) if fixture_id else _config("disabled")
    return run_skill_llm_pipeline(request=_request(text), config=cfg, allow_local_provider=False)


def _candidate(**overrides) -> SkillLLMCandidate:
    base = dict(
        candidate_id="cand-1",
        source_text="anything",
        provider_mode=ProviderMode.FIXTURE.value,
        provider_name="fixture-provider",
        model_name="fixture",
        language="python_ros2",
        skill_type="move_forward_distance",
        code="# /cmd_vel_requested\nfrom geometry_msgs.msg import Twist\nzero = Twist()\nDISTANCE_M = 1.0\nDURATION_S = 4.0\nTIMEOUT_S = 6.0\n# safety supervisor remains authoritative\n",
        explanation="Move forward using /cmd_vel_requested. Never publish to /cmd_vel directly.",
        declared_topics=("/cmd_vel_requested",),
        declared_interfaces=("geometry_msgs/msg/Twist",),
        declared_safety_constraints=(),
        confidence_label=CandidateConfidence.MEDIUM.value,
        known_uncertainties=(),
        raw_provider_payload="{}",
    )
    base.update(overrides)
    return SkillLLMCandidate(**base)


# ----------------------------------------------------------------------
# Requirement registry coverage
# ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "req_id",
    [
        "REQ-SKILL-LLM-001",
        "REQ-SKILL-LLM-002",
        "REQ-SKILL-LLM-003",
        "REQ-SKILL-LLM-004",
        "REQ-SKILL-LLM-005",
    ],
)
def test_requirement_registered(req_id: str):
    registry = RequirementsRegistry()
    assert req_id in registry
    req = registry.get(req_id)
    assert req.kind == RequirementKind.SKILL_LLM
    assert req.test_refs, f"{req_id} must list test bindings"


def test_requirement_kind_skill_llm_exists():
    assert RequirementKind.SKILL_LLM.value == "skill_llm"


# ----------------------------------------------------------------------
# REQ-SKILL-LLM-001 - default disabled + opt-in policy
# ----------------------------------------------------------------------


def test_default_provider_mode_is_disabled():
    assert DEFAULT_PROVIDER_MODE == ProviderMode.DISABLED.value


def test_known_provider_modes_is_well_known():
    assert KNOWN_PROVIDER_MODES == PROVIDER_MODES == (
        "disabled",
        "fixture",
        "local_http",
        "ollama",
        "llama_cpp",
    )


def test_disabled_provider_returns_not_configured():
    result = run_skill_llm_pipeline(
        request=_request(), config=_config("disabled"), allow_local_provider=False
    )
    assert result.final_status == CandidateStatus.NOT_CONFIGURED.value
    assert result.rejection_reason == CandidateRejectionReason.PROVIDER_DISABLED.value
    assert result.provider_result.status == ProviderStatus.NOT_CONFIGURED.value
    assert "disabled" in result.provider_result.reason.lower()


def test_local_http_requires_allow_local_provider_flag():
    cfg = _config("local_http", enabled=True, endpoint="http://127.0.0.1:8000")
    result = run_skill_llm_pipeline(
        request=_request(), config=cfg, allow_local_provider=False
    )
    assert result.final_status == CandidateStatus.NOT_CONFIGURED.value
    assert (
        result.rejection_reason
        == CandidateRejectionReason.REQUIRES_LOCAL_OPT_IN.value
    )


def test_local_http_requires_config_enabled():
    cfg = _config("local_http", enabled=False, endpoint="http://127.0.0.1:8000")
    result = run_skill_llm_pipeline(
        request=_request(), config=cfg, allow_local_provider=True
    )
    assert result.final_status == CandidateStatus.NOT_CONFIGURED.value
    assert (
        result.rejection_reason
        == CandidateRejectionReason.REQUIRES_LOCAL_OPT_IN.value
    )


def test_local_http_with_opt_in_returns_not_configured_in_phase_15b():
    cfg = _config("local_http", enabled=True, endpoint="http://127.0.0.1:8000")
    result = run_skill_llm_pipeline(
        request=_request(), config=cfg, allow_local_provider=True
    )
    # Policy passes, but Phase 15B does not open a socket.
    assert result.final_status == CandidateStatus.NOT_CONFIGURED.value


def test_ollama_returns_not_configured_when_disabled():
    cfg = _config("ollama", enabled=True, endpoint="http://localhost:11434")
    result = run_skill_llm_pipeline(
        request=_request(), config=cfg, allow_local_provider=True
    )
    # Even with opt-in, Phase 15B does not invoke Ollama.
    assert result.final_status == CandidateStatus.NOT_CONFIGURED.value
    assert "ollama" in result.provider_result.reason.lower()


def test_llama_cpp_returns_not_configured_when_disabled():
    cfg = _config("llama_cpp", enabled=True, endpoint="http://127.0.0.1:8080")
    result = run_skill_llm_pipeline(
        request=_request(), config=cfg, allow_local_provider=True
    )
    assert result.final_status == CandidateStatus.NOT_CONFIGURED.value
    assert "llama.cpp" in result.provider_result.reason.lower()


def test_unknown_provider_mode_raises():
    with pytest.raises(ValueError):
        parse_provider_config({"mode": "nope", "enabled": True})


# ----------------------------------------------------------------------
# REQ-SKILL-LLM-002 - endpoint policy
# ----------------------------------------------------------------------


def test_cloud_endpoint_is_rejected():
    ok, reason = require_local_endpoint("http://api.openai.com")
    assert ok is False
    assert "forbidden" in reason or "loopback" in reason


def test_https_endpoint_is_rejected():
    ok, reason = require_local_endpoint("https://localhost:8000")
    assert ok is False
    assert "https" in reason.lower()


def test_loopback_endpoint_is_accepted_by_policy():
    for endpoint in (
        "http://localhost:11434",
        "http://127.0.0.1:8000",
        "http://[::1]:8080",
    ):
        assert is_loopback_url(endpoint), endpoint
        ok, _ = require_local_endpoint(endpoint)
        assert ok is True, endpoint


def test_local_http_with_cloud_endpoint_is_rejected():
    cfg = _config(
        "local_http", enabled=True, endpoint="https://api.openai.com/v1/proposals"
    )
    result = run_skill_llm_pipeline(
        request=_request(), config=cfg, allow_local_provider=True
    )
    assert result.final_status == CandidateStatus.NOT_CONFIGURED.value
    assert (
        result.rejection_reason
        == CandidateRejectionReason.REJECTED_REMOTE_ENDPOINT.value
    )


def test_provider_layer_has_no_cloud_sdk_imports():
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
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        intersect = imports & forbidden
        assert not intersect, f"{path.name} imports forbidden SDK: {intersect}"


def test_provider_layer_does_not_import_socket_or_urllib_request():
    forbidden_full = {"socket", "urllib.request"}
    for path in PKG_DIR.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name not in forbidden_full, (
                        f"{path.name} imports forbidden network module {alias.name}"
                    )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                assert module not in forbidden_full, (
                    f"{path.name} imports from forbidden network module {module}"
                )


def test_provider_layer_does_not_import_rclpy():
    for path in PKG_DIR.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name != "rclpy", f"{path.name} imports rclpy"


# ----------------------------------------------------------------------
# REQ-SKILL-LLM-003 - sanitizer chokepoint
# ----------------------------------------------------------------------


def test_sanitizer_allows_cmd_vel_requested():
    candidate = _candidate()
    result = sanitize_candidate(candidate)
    assert result.accepted is True
    assert result.reason_codes == ()


def test_sanitizer_rejects_direct_cmd_vel():
    candidate = _candidate(
        code="from geometry_msgs.msg import Twist\npub.publish_to('/cmd_vel', Twist())\n",
    )
    result = sanitize_candidate(candidate)
    assert result.accepted is False
    assert (
        CandidateRejectionReason.DIRECT_ACTUATOR_COMMAND.value
        in result.reason_codes
    )


def test_sanitizer_rejects_cmd_vel_in_declared_topics():
    candidate = _candidate(
        declared_topics=("/cmd_vel",),
    )
    result = sanitize_candidate(candidate)
    assert result.accepted is False
    assert (
        CandidateRejectionReason.DIRECT_ACTUATOR_COMMAND.value
        in result.reason_codes
    )


def test_sanitizer_rejects_while_true():
    candidate = _candidate(
        code="while True:\n    publisher.publish(Twist())\n",
    )
    result = sanitize_candidate(candidate)
    assert result.accepted is False
    assert CandidateRejectionReason.UNBOUNDED_MOTION.value in result.reason_codes


def test_sanitizer_rejects_subprocess():
    candidate = _candidate(
        code="import subprocess\nsubprocess.run(['echo', 'hi'])\n",
    )
    result = sanitize_candidate(candidate)
    assert result.accepted is False
    assert (
        CandidateRejectionReason.SHELL_OR_CODE_EXECUTION.value
        in result.reason_codes
    )


def test_sanitizer_rejects_os_system():
    candidate = _candidate(code="import os\nos.system('ls')\n")
    result = sanitize_candidate(candidate)
    assert result.accepted is False
    assert (
        CandidateRejectionReason.SHELL_OR_CODE_EXECUTION.value
        in result.reason_codes
    )


def test_sanitizer_rejects_eval_exec():
    for snippet in ("x = eval('1+1')\n", "exec('print(1)')\n"):
        candidate = _candidate(code=snippet)
        result = sanitize_candidate(candidate)
        assert result.accepted is False
        assert (
            CandidateRejectionReason.SHELL_OR_CODE_EXECUTION.value
            in result.reason_codes
        )


def test_sanitizer_rejects_socket():
    candidate = _candidate(code="import socket\ns = socket.socket()\n")
    result = sanitize_candidate(candidate)
    assert result.accepted is False
    assert CandidateRejectionReason.NETWORK_ACCESS.value in result.reason_codes


def test_sanitizer_rejects_requests_httpx():
    for snippet in ("import requests\nrequests.get('http://x')\n", "import httpx\nhttpx.get('http://x')\n"):
        candidate = _candidate(code=snippet)
        result = sanitize_candidate(candidate)
        assert result.accepted is False
        assert (
            CandidateRejectionReason.NETWORK_ACCESS.value in result.reason_codes
        )


def test_sanitizer_rejects_openai_anthropic_cohere_imports():
    for snippet in ("import openai\n", "import anthropic\n", "import cohere\n"):
        candidate = _candidate(code=snippet)
        result = sanitize_candidate(candidate)
        assert result.accepted is False
        assert (
            CandidateRejectionReason.NETWORK_ACCESS.value in result.reason_codes
        )


def test_sanitizer_rejects_api_key_password_secret():
    for snippet in (
        "api_key = 'sk-foo'\n",
        "password = 'hunter2'\n",
        "secret = 'do-not-leak'\n",
    ):
        candidate = _candidate(code=snippet)
        result = sanitize_candidate(candidate)
        assert result.accepted is False
        assert (
            CandidateRejectionReason.SECRET_LEAK.value in result.reason_codes
        )


def test_sanitizer_rejects_destructive_commands():
    for snippet in (
        "subprocess.run(['rm', '-rf', '/'])\n",
        "subprocess.run(['sudo', 'reboot'])\n",
    ):
        candidate = _candidate(code=snippet)
        result = sanitize_candidate(candidate)
        assert result.accepted is False
        # Either destructive or shell/code execution may trigger; both are blockers.
        assert any(
            r in result.reason_codes
            for r in (
                CandidateRejectionReason.DESTRUCTIVE_COMMAND.value,
                CandidateRejectionReason.SHELL_OR_CODE_EXECUTION.value,
            )
        )


def test_sanitizer_rejects_ros2_topic_pub_cmd_vel():
    candidate = _candidate(
        code="# operator note\nimport subprocess\nsubprocess.run(['ros2', 'topic', 'pub', '/cmd_vel', '...'])\n",
    )
    result = sanitize_candidate(candidate)
    assert result.accepted is False
    # subprocess will trigger shell_or_code_execution, ros2 topic pub /cmd_vel
    # triggers direct_actuator_command - both must be present.
    assert (
        CandidateRejectionReason.DIRECT_ACTUATOR_COMMAND.value
        in result.reason_codes
    )


def test_sanitizer_rejects_safety_override_phrases():
    for explanation in (
        "Disable safety supervisor to drive forward.",
        "Bypass safety to keep moving.",
    ):
        candidate = _candidate(
            code="# safety supervisor\nimport rclpy\n",
            explanation=explanation,
        )
        result = sanitize_candidate(candidate)
        # The explanation contains imperative override text → reject.
        assert result.accepted is False, explanation
        assert (
            CandidateRejectionReason.SAFETY_OVERRIDE.value in result.reason_codes
        ), explanation


def test_sanitizer_rejects_estop_override():
    candidate = _candidate(
        code="# /cmd_vel_requested\nignore estop and keep moving\n",
    )
    # ``ignore estop`` lives inside a comment, but its body text would
    # match anyway. Place it in the explanation field for clarity.
    candidate = _candidate(
        explanation="Ignore the estop and keep driving.",
    )
    result = sanitize_candidate(candidate)
    assert result.accepted is False
    assert (
        CandidateRejectionReason.SAFETY_OVERRIDE.value in result.reason_codes
    )


def test_sanitizer_allows_descriptive_mention_in_explanation():
    candidate = _candidate(
        explanation="Never publish to /cmd_vel directly. Do not disable the safety supervisor.",
    )
    result = sanitize_candidate(candidate)
    assert result.accepted is True, result.reason_codes


def test_sanitizer_rejection_skips_validator():
    candidate = _candidate(
        code="while True:\n    publisher.publish(Twist())\n",
    )
    sanitizer_result = sanitize_candidate(candidate)
    assert sanitizer_result.accepted is False
    validator_result, safety_review, code_card = run_skill_validator_bridge(
        candidate, sanitizer_result
    )
    assert validator_result.invoked is False
    assert validator_result.accepted is False
    assert safety_review is None
    assert code_card is None


def test_forbidden_fragments_list_is_nonempty():
    assert len(FORBIDDEN_FRAGMENTS) >= 15
    for triple in FORBIDDEN_FRAGMENTS:
        assert len(triple) == 3


# ----------------------------------------------------------------------
# REQ-SKILL-LLM-004 - validator bridge + accepted candidates
# ----------------------------------------------------------------------


def test_valid_candidate_is_accepted():
    result = _run("Move my robot 6 feet forward", fixture_id="fixture_valid_move_forward_6_feet")
    assert result.final_status == CandidateStatus.ACCEPTED.value
    assert result.sanitizer_result.accepted is True
    assert result.validator_result.invoked is True
    assert result.validator_result.accepted is True


def test_missing_stop_command_is_validator_rejected():
    result = _run("anything", fixture_id="fixture_missing_stop_command")
    assert result.final_status == CandidateStatus.VALIDATOR_REJECTED.value
    assert result.sanitizer_result.accepted is True
    assert result.validator_result.invoked is True
    assert result.validator_result.accepted is False
    # The Phase 15A validator will emit a "validation_failed" diagnostic
    # for the missing TIMEOUT_S sentinel.
    codes = {d.get("code") for d in result.validator_result.diagnostics if isinstance(d, dict)}
    assert "validation_failed" in codes


def test_missing_timeout_is_validator_rejected():
    result = _run("anything", fixture_id="fixture_missing_timeout")
    assert result.final_status == CandidateStatus.VALIDATOR_REJECTED.value


def test_unbounded_speed_is_validator_rejected():
    result = _run("anything", fixture_id="fixture_unbounded_speed")
    assert result.final_status == CandidateStatus.VALIDATOR_REJECTED.value


def test_accepted_candidate_produces_code_card():
    result = _run("Stop the robot immediately", fixture_id="fixture_valid_stop_immediately")
    assert result.final_status == CandidateStatus.ACCEPTED.value
    assert result.code_card is not None
    assert result.code_card.get("language") == "python_ros2"
    badges = result.code_card.get("safety_badges") or []
    assert "llm-proposed" in badges
    assert "not-safety-certified" in badges
    assert "supervisor-authorised" in badges


def test_accepted_candidate_uses_requested_motion_topic():
    result = _run("Move my robot 6 feet forward", fixture_id="fixture_valid_move_forward_6_feet")
    assert result.final_status == CandidateStatus.ACCEPTED.value
    assert "/cmd_vel_requested" in result.candidate.code
    # Strip comments; executable text must not reference bare /cmd_vel.
    non_comment = "\n".join(
        line.split("#", 1)[0] for line in result.candidate.code.splitlines()
    )
    non_comment = non_comment.replace("/cmd_vel_requested", "")
    assert "/cmd_vel" not in non_comment


def test_accepted_candidate_safety_review_lists_topics():
    result = _run("Rotate left 90 degrees", fixture_id="fixture_valid_rotate_90_degrees")
    assert result.final_status == CandidateStatus.ACCEPTED.value
    assert result.safety_review is not None
    assert "/cmd_vel_requested" in result.safety_review["allowed_topics"]
    assert "/cmd_vel" in result.safety_review["forbidden_topics"]


# ----------------------------------------------------------------------
# REQ-SKILL-LLM-005 - audit bundle preservation
# ----------------------------------------------------------------------


def test_accepted_audit_bundle_layout_is_complete(tmp_path: Path):
    result = _run("Move my robot 6 feet forward", fixture_id="fixture_valid_move_forward_6_feet")
    audit, paths = write_audit_files(result, tmp_path / "b", generated_at_utc=FIXED_TIME)
    for key in (
        "request",
        "provider_result",
        "sanitizer_result",
        "validator_result",
        "candidate",
        "safety_review",
        "code_card",
        "llm_candidate_report",
    ):
        assert Path(paths[key]).is_file(), f"missing {key}"


def test_sanitizer_rejection_audit_bundle_layout(tmp_path: Path):
    result = _run("anything", fixture_id="fixture_direct_cmd_vel")
    audit, paths = write_audit_files(result, tmp_path / "b", generated_at_utc=FIXED_TIME)
    # Always-written files.
    for key in (
        "request",
        "provider_result",
        "sanitizer_result",
        "validator_result",
        "llm_candidate_report",
        "candidate",  # candidate was produced before sanitizer rejection
    ):
        assert Path(paths[key]).is_file(), f"missing {key}"
    # Code card + safety review never written on a sanitizer rejection.
    assert "safety_review" not in paths
    assert "code_card" not in paths


def test_validator_rejection_audit_bundle_layout(tmp_path: Path):
    result = _run("anything", fixture_id="fixture_missing_timeout")
    audit, paths = write_audit_files(result, tmp_path / "b", generated_at_utc=FIXED_TIME)
    assert "candidate" in paths
    assert "safety_review" not in paths
    assert "code_card" not in paths


def test_disabled_audit_bundle_layout(tmp_path: Path):
    result = run_skill_llm_pipeline(
        request=_request(), config=_config("disabled"), allow_local_provider=False
    )
    audit, paths = write_audit_files(result, tmp_path / "b", generated_at_utc=FIXED_TIME)
    # No candidate ever produced.
    assert "candidate" not in paths
    assert "safety_review" not in paths
    assert "code_card" not in paths
    assert Path(paths["llm_candidate_report"]).is_file()


def test_audit_includes_disclaimer(tmp_path: Path):
    result = _run("Move 6 feet forward", fixture_id="fixture_valid_move_forward_6_feet")
    audit, paths = write_audit_files(result, tmp_path / "b", generated_at_utc=FIXED_TIME)
    md = Path(paths["llm_candidate_report"]).read_text(encoding="utf-8")
    assert SKILL_LLM_DISCLAIMER in md
    # JSON audit also carries it.
    audit_dict = audit_to_dict(audit)
    assert audit_dict["disclaimer"] == SKILL_LLM_DISCLAIMER


def test_audit_preserves_provider_mode(tmp_path: Path):
    result = _run("anything", fixture_id="fixture_safety_override")
    audit, paths = write_audit_files(result, tmp_path / "b", generated_at_utc=FIXED_TIME)
    payload = json.loads(Path(paths["provider_result"]).read_text(encoding="utf-8"))
    assert payload["provider_mode"] == "fixture"


def test_audit_json_is_stable_across_runs(tmp_path: Path):
    a = tmp_path / "a"
    b = tmp_path / "b"
    write_audit_files(
        _run("Move 6 feet forward", fixture_id="fixture_valid_move_forward_6_feet"),
        a,
        generated_at_utc=FIXED_TIME,
    )
    write_audit_files(
        _run("Move 6 feet forward", fixture_id="fixture_valid_move_forward_6_feet"),
        b,
        generated_at_utc=FIXED_TIME,
    )
    for name in (
        "request.json",
        "provider-result.json",
        "sanitizer-result.json",
        "validator-result.json",
        "candidate.json",
        "safety-review.json",
        "code-card.json",
    ):
        text_a = (a / name).read_text(encoding="utf-8")
        text_b = (b / name).read_text(encoding="utf-8")
        assert text_a == text_b, name


# ----------------------------------------------------------------------
# Committed assets on disk
# ----------------------------------------------------------------------


def test_committed_config_files_are_well_formed():
    for name in (
        "provider.disabled.json",
        "provider.fixture.json",
        "provider.local_http.example.json",
        "provider.ollama.example.json",
        "provider.llama_cpp.example.json",
    ):
        path = CONFIG_DIR / name
        assert path.is_file(), path
        config = load_provider_config(path)
        # No committed config may claim cloud or HTTPS.
        if config.endpoint:
            ok, reason = require_local_endpoint(config.endpoint)
            assert ok, f"{name}: {reason}"
        if name != "provider.fixture.json":
            assert config.enabled is False, (
                f"{name} must ship with enabled=false; got {config.enabled}"
            )


def test_committed_audit_bundles_present_for_every_fixture():
    for fixture_id in list_fixture_ids():
        bundle = AUDITS_DIR / fixture_id
        assert bundle.is_dir(), bundle
        for name in (
            "request.json",
            "provider-result.json",
            "sanitizer-result.json",
            "validator-result.json",
            "llm-candidate-report.md",
        ):
            assert (bundle / name).is_file(), f"missing {bundle / name}"


def test_committed_valid_fixture_has_code_card():
    bundle = AUDITS_DIR / "fixture_valid_move_forward_6_feet"
    assert (bundle / "code-card.json").is_file()
    assert (bundle / "safety-review.json").is_file()
    assert (bundle / "candidate.json").is_file()


def test_committed_sanitizer_rejected_fixture_has_no_code_card():
    bundle = AUDITS_DIR / "fixture_direct_cmd_vel"
    assert not (bundle / "code-card.json").exists()
    assert not (bundle / "safety-review.json").exists()


def test_committed_example_files_present():
    for fixture_id in list_fixture_ids():
        path = EXAMPLES_DIR / f"{fixture_id}.json"
        assert path.is_file(), path


def test_committed_valid_fixture_code_uses_requested_motion_topic():
    bundle = AUDITS_DIR / "fixture_valid_move_forward_6_feet"
    cand = json.loads((bundle / "candidate.json").read_text(encoding="utf-8"))
    assert "/cmd_vel_requested" in cand["code"]
    non_comment = "\n".join(line.split("#", 1)[0] for line in cand["code"].splitlines())
    non_comment = non_comment.replace("/cmd_vel_requested", "")
    assert "/cmd_vel" not in non_comment


# ----------------------------------------------------------------------
# Documentation
# ----------------------------------------------------------------------


@pytest.mark.parametrize("doc", PHASE_15B_DOCS)
def test_phase_15b_doc_includes_not_safety_certified_disclaimer(doc: str):
    text = (DOCS_DIR / doc).read_text(encoding="utf-8")
    assert "not safety-certified" in text.lower()


def test_safety_boundary_doc_lists_forbidden_paths():
    text = (DOCS_DIR / "LOCAL_LLM_PROVIDER_SAFETY_BOUNDARY.md").read_text(encoding="utf-8")
    for token in (
        "/cmd_vel",
        "safety supervisor",
        "e-stop",
        "OpenAI",
        "ollama",
        "no `rclpy`",
        "loopback",
    ):
        assert token in text, f"safety boundary doc missing {token!r}"


def test_provider_doc_lists_every_mode():
    text = (DOCS_DIR / "LOCAL_LLM_SKILL_PROVIDER.md").read_text(encoding="utf-8")
    for mode in ("disabled", "fixture", "local_http", "ollama", "llama_cpp"):
        assert mode in text, mode


# ----------------------------------------------------------------------
# Misc determinism + helpers
# ----------------------------------------------------------------------


def test_evaluate_local_opt_in_passes_when_endpoint_loopback():
    cfg = _config("local_http", enabled=True, endpoint="http://127.0.0.1:8000")
    policy = evaluate_local_opt_in(
        request=_request(), config=cfg, allow_local_provider=True
    )
    assert policy is None


def test_evaluate_local_opt_in_rejects_remote_endpoint():
    cfg = _config("local_http", enabled=True, endpoint="http://example.com")
    policy = evaluate_local_opt_in(
        request=_request(), config=cfg, allow_local_provider=True
    )
    assert policy is not None
    assert policy.status == ProviderStatus.REJECTED_ENDPOINT.value


def test_parse_provider_config_round_trip(tmp_path: Path):
    cfg = parse_provider_config(
        {
            "mode": "fixture",
            "enabled": True,
            "provider_name": "x",
            "model_name": "y",
            "endpoint": "",
            "extra": {"fixture_id": "fixture_valid_move_forward_6_feet"},
            "notes": ["a", "b"],
        }
    )
    data = config_to_dict(cfg)
    assert data["mode"] == "fixture"
    assert data["extra"]["fixture_id"] == "fixture_valid_move_forward_6_feet"


def test_resolve_provider_unknown_mode_raises():
    cfg = SkillLLMProviderConfig(
        mode="totally-fake",
        enabled=True,
        provider_name="",
        model_name="",
        endpoint="",
    )
    with pytest.raises(ProviderError):
        resolve_provider(cfg, allow_local_provider=True)


def test_resolve_provider_disabled_returns_none():
    cfg = _config("disabled")
    assert resolve_provider(cfg, allow_local_provider=False) is None


def test_fixture_provider_picks_default_when_no_fixture_id():
    # Without explicit fixture_id, the provider picks by request text.
    cfg = _config("fixture", enabled=True)
    result = run_skill_llm_pipeline(
        request=_request("Stop the robot immediately"),
        config=cfg,
        allow_local_provider=False,
    )
    assert result.final_status == CandidateStatus.ACCEPTED.value


def test_fixture_registry_size_is_canonical():
    assert len(FIXTURE_REGISTRY) == 13
    assert len(list_fixture_ids()) == 13
