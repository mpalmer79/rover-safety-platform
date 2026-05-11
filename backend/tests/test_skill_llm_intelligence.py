"""Phase 19 local LLM intelligence layer tests.

Honesty rules under test:
  - candidate ranking is deterministic;
  - validator outcome dominates the score;
  - overconfident-without-validation is penalised;
  - normalization preserves the raw payload;
  - repair suggestions are suggestion-only;
  - readiness checks never open sockets and reject remote endpoints;
  - the local provider remains disabled by default.
"""

from __future__ import annotations

import json
import socket
from pathlib import Path

import pytest

from app.skill_llm_provider import (
    CandidateRejectionReason,
    NORMALIZATION_STATUS_ACCEPTED,
    NORMALIZATION_STATUS_REJECTED,
    READINESS_DISABLED,
    READINESS_READY,
    READINESS_REJECTED_ENDPOINT,
    READINESS_REQUIRES_OPT_IN,
    REPAIR_STATUS_NOT_APPLICABLE,
    REPAIR_STATUS_REQUIRES_HUMAN_REVIEW,
    REPAIR_STATUS_SUGGESTION_ONLY,
    SkillLLMCandidate,
    SkillLLMProviderConfig,
    SkillLLMSanitizerResult,
    SkillLLMValidationResult,
    VERDICT_FAIL,
    VERDICT_OK,
    VERDICT_WARN,
    capability_to_dict,
    check_provider_readiness,
    critique_candidate,
    default_capability_registry,
    find_capability,
    normalization_result_to_dict,
    normalize_candidate_payload,
    rank_candidates,
    ranking_to_dict,
    repair_bundle_to_dict,
    suggest_repairs,
)


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------


def _make_candidate(
    cid: str,
    *,
    code: str = "",
    confidence: str = "medium",
    declared_topics: tuple[str, ...] = ("/cmd_vel_requested",),
    explanation: str = "explanation",
    known_uncertainties: tuple[str, ...] = (),
) -> SkillLLMCandidate:
    return SkillLLMCandidate(
        candidate_id=cid,
        source_text="src",
        provider_mode="fixture",
        provider_name="fixture",
        model_name="canonical-fixture",
        language="python_ros2",
        skill_type="move_forward_distance",
        code=code,
        explanation=explanation,
        declared_topics=declared_topics,
        declared_interfaces=("geometry_msgs/msg/Twist",),
        declared_safety_constraints=(),
        confidence_label=confidence,
        known_uncertainties=known_uncertainties,
        raw_provider_payload="{}",
    )


def _sanitizer(accepted: bool, *reasons: str) -> SkillLLMSanitizerResult:
    return SkillLLMSanitizerResult(
        status="accepted" if accepted else "rejected",
        accepted=accepted,
        reason_codes=tuple(reasons),
        blocked_fragments=(),
        notes=(),
        human_review_required=not accepted,
    )


def _validator(invoked: bool, accepted: bool, safety: str = "safe_after_validation") -> SkillLLMValidationResult:
    return SkillLLMValidationResult(
        invoked=invoked,
        accepted=accepted,
        diagnostics=(),
        skill_type="move_forward_distance",
        safety_status=safety,
    )


# ---------------------------------------------------------------------
# Ranking
# ---------------------------------------------------------------------


def test_ranking_is_deterministic_for_identical_inputs() -> None:
    triples = [
        (
            _make_candidate(
                "a",
                code=(
                    "import time\n"
                    "deadline = time.monotonic() + 5\n"
                    "publisher.publish(stop_command)\n"
                    "stop = Twist()\n"
                ),
            ),
            _sanitizer(True),
            _validator(True, True),
        ),
        (
            _make_candidate("b", code="while True: pass"),
            _sanitizer(False, CandidateRejectionReason.SHELL_OR_CODE_EXECUTION.value),
            _validator(False, False),
        ),
    ]
    r1 = rank_candidates(triples)
    r2 = rank_candidates(triples)
    assert tuple((r.candidate_id, r.score) for r in r1) == tuple(
        (r.candidate_id, r.score) for r in r2
    )


def test_validator_outcome_dominates_ranking() -> None:
    triples = [
        (
            _make_candidate(
                "valid",
                code="publisher.publish(Twist())\ndeadline = time.monotonic() + 1\n",
            ),
            _sanitizer(True),
            _validator(True, True),
        ),
        (
            _make_candidate(
                "rejected_but_pretty",
                code="publisher.publish(Twist())\ndeadline = time.monotonic() + 1\n",
                explanation="long detailed explanation with caveats",
                known_uncertainties=("hardware not modelled",),
            ),
            _sanitizer(True),
            _validator(True, False),
        ),
    ]
    ranked = rank_candidates(triples)
    assert ranked[0].candidate_id == "valid"
    assert ranked[1].candidate_id == "rejected_but_pretty"


def test_overconfident_without_validation_is_penalised() -> None:
    triples = [
        (
            _make_candidate(
                "overconfident",
                code="publisher.publish(Twist())\ndeadline = time.monotonic() + 1\n",
                confidence="overconfident",
            ),
            _sanitizer(True),
            _validator(True, False),
        ),
    ]
    ranked = rank_candidates(triples)
    signals = [b.signal for b in ranked[0].breakdown]
    assert "overconfident_without_validation" in signals


def test_sanitizer_rejection_dominates() -> None:
    triples = [
        (
            _make_candidate("sanitize_bad", code="import subprocess"),
            _sanitizer(False, CandidateRejectionReason.SHELL_OR_CODE_EXECUTION.value),
            _validator(False, False),
        ),
    ]
    ranked = rank_candidates(triples)
    assert ranked[0].score <= -100
    assert ranked[0].accepted is False


def test_ranking_serialises_to_dict() -> None:
    ranked = rank_candidates(
        [
            (
                _make_candidate("a"),
                _sanitizer(True),
                _validator(True, True),
            )
        ]
    )
    payload = ranking_to_dict(ranked[0])
    assert payload["candidate_id"] == "a"
    assert "breakdown" in payload


# ---------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------


def test_normalize_strips_markdown_fences() -> None:
    raw = '```json\n{"skill_type": "Move Forward"}\n```'
    result = normalize_candidate_payload(raw)
    assert result.status == NORMALIZATION_STATUS_ACCEPTED
    assert result.raw_payload == raw
    assert result.normalized["skill_type"] == "move_forward"
    assert any("markdown fences stripped" in w for w in result.warnings)


def test_normalize_extracts_json_from_prose() -> None:
    raw = 'Sure, here it is:\n{"skill_type": "stop now"}\nLet me know.'
    result = normalize_candidate_payload(raw)
    assert result.accepted
    assert result.normalized["skill_type"] == "stop_immediately"
    assert any("JSON object extracted" in w for w in result.warnings)


def test_normalize_rejects_invalid_json() -> None:
    raw = "not json at all"
    result = normalize_candidate_payload(raw)
    assert result.status == NORMALIZATION_STATUS_REJECTED
    assert "invalid_json" in result.reason_codes
    # The raw payload is preserved verbatim.
    assert result.raw_payload == raw


def test_normalize_rejects_empty_input() -> None:
    result = normalize_candidate_payload("")
    assert result.status == NORMALIZATION_STATUS_REJECTED
    assert "empty_payload" in result.reason_codes


def test_normalize_serialises_to_dict() -> None:
    result = normalize_candidate_payload('{"skill_type":"stop_immediately"}')
    payload = normalization_result_to_dict(result)
    assert payload["accepted"] is True
    assert payload["normalized"]["skill_type"] == "stop_immediately"


def test_normalize_aliases_topic_lists() -> None:
    result = normalize_candidate_payload(
        '{"declared_topics": ["cmd_vel_requested", "/cmd_vel"]}'
    )
    assert result.accepted
    assert result.normalized["declared_topics"] == ["/cmd_vel_requested", "/cmd_vel"]


# ---------------------------------------------------------------------
# Repair suggestions
# ---------------------------------------------------------------------


def test_repair_suggests_stop_command_when_missing() -> None:
    bundle = suggest_repairs(
        _make_candidate("c", code="publisher.publish(forward)\n"),
        _sanitizer(True),
        _validator(True, False),
    )
    titles = [s.title for s in bundle.suggestions]
    assert any("zero-Twist stop" in t for t in titles)
    assert bundle.status in {
        REPAIR_STATUS_SUGGESTION_ONLY,
        REPAIR_STATUS_REQUIRES_HUMAN_REVIEW,
    }


def test_repair_suggests_topic_change_when_direct_cmd_vel() -> None:
    bundle = suggest_repairs(
        _make_candidate(
            "c",
            code='publisher = node.create_publisher(Twist, "/cmd_vel", 10)\npublisher.publish("/cmd_vel", Twist())\n',
        ),
        _sanitizer(False, CandidateRejectionReason.DIRECT_ACTUATOR_COMMAND.value),
        _validator(False, False),
    )
    codes = [s.code for s in bundle.suggestions]
    assert "repair.use_cmd_vel_requested" in codes
    assert bundle.status == REPAIR_STATUS_REQUIRES_HUMAN_REVIEW


def test_repair_status_not_applicable_for_clean_candidate() -> None:
    clean = _make_candidate(
        "c",
        code=(
            "import time\n"
            "deadline = time.monotonic() + 5\n"
            "publisher.publish(Twist())\n"
        ),
    )
    bundle = suggest_repairs(clean, _sanitizer(True), _validator(True, True))
    assert bundle.status == REPAIR_STATUS_NOT_APPLICABLE
    assert bundle.suggestions == ()


def test_repair_escalates_human_review_for_unsafe_categories() -> None:
    bundle = suggest_repairs(
        _make_candidate("c", code="import subprocess\nsubprocess.run(['x'])\n"),
        _sanitizer(False, CandidateRejectionReason.SHELL_OR_CODE_EXECUTION.value),
        _validator(False, False),
    )
    assert bundle.status == REPAIR_STATUS_REQUIRES_HUMAN_REVIEW
    assert any(
        s.status == REPAIR_STATUS_REQUIRES_HUMAN_REVIEW for s in bundle.suggestions
    )


def test_repair_bundle_serialises_to_dict() -> None:
    bundle = suggest_repairs(
        _make_candidate("c", code="publisher.publish(twist)"),
        _sanitizer(True),
        _validator(True, False),
    )
    payload = repair_bundle_to_dict(bundle)
    assert payload["candidate_id"] == "c"
    assert isinstance(payload["suggestions"], list)


# ---------------------------------------------------------------------
# Provider readiness
# ---------------------------------------------------------------------


def test_disabled_provider_readiness_reports_disabled() -> None:
    config = SkillLLMProviderConfig(
        mode="disabled",
        enabled=False,
        provider_name="local",
        model_name="",
        endpoint="",
    )
    readiness = check_provider_readiness(config)
    assert readiness.status == READINESS_DISABLED
    assert readiness.execution_allowed is False


def test_remote_endpoint_is_rejected_even_when_enabled() -> None:
    config = SkillLLMProviderConfig(
        mode="local_http",
        enabled=True,
        provider_name="local-http",
        model_name="llama-3.1-8b-instruct.q4",
        endpoint="https://example.com/v1/chat",
    )
    readiness = check_provider_readiness(config)
    assert readiness.status == READINESS_REJECTED_ENDPOINT
    assert readiness.execution_allowed is False
    assert readiness.endpoint_is_local_only is False


def test_local_endpoint_requires_opt_in() -> None:
    config = SkillLLMProviderConfig(
        mode="local_http",
        enabled=False,
        provider_name="local-http",
        model_name="llama-3.1-8b-instruct.q4",
        endpoint="http://127.0.0.1:8080/completions",
    )
    readiness = check_provider_readiness(config)
    assert readiness.status == READINESS_REQUIRES_OPT_IN
    assert readiness.execution_allowed is False


def test_local_endpoint_ready_when_enabled_and_model_present() -> None:
    config = SkillLLMProviderConfig(
        mode="ollama",
        enabled=True,
        provider_name="ollama",
        model_name="phi-3.5-mini-instruct.q4",
        endpoint="http://localhost:11434/api/generate",
    )
    readiness = check_provider_readiness(config)
    assert readiness.status == READINESS_READY
    assert readiness.execution_allowed is True
    assert readiness.endpoint_is_local_only is True


def test_readiness_never_opens_a_socket(monkeypatch: pytest.MonkeyPatch) -> None:
    """Calls to socket.socket would raise; the readiness check must not."""

    def boom(*args: object, **kwargs: object) -> object:
        raise AssertionError(
            "readiness check must not construct a socket"
        )

    monkeypatch.setattr(socket, "socket", boom)
    monkeypatch.setattr(socket, "create_connection", boom)

    config = SkillLLMProviderConfig(
        mode="local_http",
        enabled=True,
        provider_name="local-http",
        model_name="phi-3.5",
        endpoint="http://127.0.0.1:8080/",
    )
    readiness = check_provider_readiness(config)
    assert readiness.status == READINESS_READY


# ---------------------------------------------------------------------
# Model capabilities
# ---------------------------------------------------------------------


def test_default_capability_registry_includes_canonical_fixture() -> None:
    registry = default_capability_registry()
    fixture = find_capability("canonical-fixture", registry)
    assert fixture is not None
    assert fixture.qualified is True


def test_find_capability_returns_none_for_unknown() -> None:
    assert find_capability("not-a-real-model") is None


def test_capability_to_dict_round_trips() -> None:
    fixture = find_capability("canonical-fixture")
    assert fixture is not None
    payload = capability_to_dict(fixture)
    assert payload["qualified"] is True
    assert payload["provider"] == "fixture"


# ---------------------------------------------------------------------
# Safety critique
# ---------------------------------------------------------------------


def test_critique_flags_direct_cmd_vel() -> None:
    critique = critique_candidate(
        _make_candidate(
            "c",
            code='publisher.publish("/cmd_vel", Twist())\n',
            declared_topics=("/cmd_vel",),
        ),
        _sanitizer(False, CandidateRejectionReason.DIRECT_ACTUATOR_COMMAND.value),
        _validator(False, False),
    )
    actuator = next(i for i in critique.items if i.category == "actuator_authority")
    assert actuator.verdict == VERDICT_FAIL
    assert critique.overall_verdict == VERDICT_FAIL


def test_critique_passes_for_clean_candidate() -> None:
    clean = _make_candidate(
        "c",
        code=(
            "import time\n"
            "deadline = time.monotonic() + 5\n"
            "publisher.publish(Twist())\n"
            "stop = Twist()\n"
            "publisher.publish(stop)\n"
        ),
        declared_topics=("/cmd_vel_requested",),
        known_uncertainties=("hardware not modelled",),
    )
    critique = critique_candidate(clean, _sanitizer(True), _validator(True, True))
    assert critique.overall_verdict in {VERDICT_OK, VERDICT_WARN}


def test_critique_warns_on_overconfident_no_uncertainty() -> None:
    candidate = _make_candidate(
        "c",
        code=(
            "import time\n"
            "deadline = time.monotonic() + 5\n"
            "publisher.publish(Twist())\n"
            "stop = Twist()\n"
        ),
        declared_topics=("/cmd_vel_requested",),
        confidence="overconfident",
    )
    critique = critique_candidate(candidate, _sanitizer(True), _validator(True, True))
    disclosure = next(
        i for i in critique.items if i.category == "uncertainty_disclosure"
    )
    assert disclosure.verdict == VERDICT_WARN
