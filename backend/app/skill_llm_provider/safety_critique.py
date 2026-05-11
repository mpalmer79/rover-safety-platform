"""Deterministic safety critiques for LLM-proposed skills.

The critique is a structured restatement of "why is this candidate
safe / not safe" derived from the sanitizer + validator outputs.
It is a reviewer aid, not a safety judgement; the validator
outcome remains authoritative.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import (
    CandidateRejectionReason,
    SkillLLMCandidate,
    SkillLLMSanitizerResult,
    SkillLLMValidationResult,
)


# Critique categories. Adding a new category requires adding a
# matching test in ``backend/tests/test_skill_llm_intelligence.py``.
CATEGORY_ACTUATOR_AUTHORITY: str = "actuator_authority"
CATEGORY_TIMEOUT_SAFETY: str = "timeout_safety"
CATEGORY_STOP_BEHAVIOR: str = "stop_behavior"
CATEGORY_TOPIC_BOUNDARY: str = "topic_boundary"
CATEGORY_DEPENDENCY_RISK: str = "dependency_risk"
CATEGORY_NETWORK_RISK: str = "network_risk"
CATEGORY_RUNTIME_EXECUTION_RISK: str = "runtime_execution_risk"
CATEGORY_UNCERTAINTY_DISCLOSURE: str = "uncertainty_disclosure"


CRITIQUE_CATEGORIES: tuple[str, ...] = (
    CATEGORY_ACTUATOR_AUTHORITY,
    CATEGORY_TIMEOUT_SAFETY,
    CATEGORY_STOP_BEHAVIOR,
    CATEGORY_TOPIC_BOUNDARY,
    CATEGORY_DEPENDENCY_RISK,
    CATEGORY_NETWORK_RISK,
    CATEGORY_RUNTIME_EXECUTION_RISK,
    CATEGORY_UNCERTAINTY_DISCLOSURE,
)


VERDICT_OK: str = "ok"
VERDICT_WARN: str = "warn"
VERDICT_FAIL: str = "fail"


@dataclass(frozen=True)
class CritiqueItem:
    category: str
    verdict: str
    summary: str
    detail: str = ""


@dataclass(frozen=True)
class SafetyCritique:
    candidate_id: str
    overall_verdict: str
    items: tuple[CritiqueItem, ...]


def _has(code: str, *needles: str) -> bool:
    lower = code.lower()
    return any(needle in lower for needle in needles)


def _critique_actuator(code: str) -> CritiqueItem:
    if "publish(\"/cmd_vel\"" in code or "publish('/cmd_vel'" in code:
        return CritiqueItem(
            CATEGORY_ACTUATOR_AUTHORITY,
            VERDICT_FAIL,
            "Skill publishes /cmd_vel directly",
            "Only the safety supervisor may publish /cmd_vel. Use /cmd_vel_requested.",
        )
    if "/cmd_vel_requested" in code:
        return CritiqueItem(
            CATEGORY_ACTUATOR_AUTHORITY,
            VERDICT_OK,
            "Skill uses /cmd_vel_requested",
            "The supervisor remains authoritative over /cmd_vel.",
        )
    return CritiqueItem(
        CATEGORY_ACTUATOR_AUTHORITY,
        VERDICT_WARN,
        "Skill does not declare an actuator topic",
        "Declare /cmd_vel_requested explicitly.",
    )


def _critique_timeout(code: str) -> CritiqueItem:
    if _has(code, "timeout", "monotonic", "deadline", "elapsed"):
        return CritiqueItem(
            CATEGORY_TIMEOUT_SAFETY, VERDICT_OK, "Bounded timeout present"
        )
    return CritiqueItem(
        CATEGORY_TIMEOUT_SAFETY,
        VERDICT_FAIL,
        "No bounded timeout",
        "A skill without a monotonic deadline cannot be rehearsed deterministically.",
    )


def _critique_stop(code: str) -> CritiqueItem:
    if _has(code, "twist()", "linear.x = 0", "publish_zero"):
        return CritiqueItem(
            CATEGORY_STOP_BEHAVIOR, VERDICT_OK, "Final zero-Twist stop present"
        )
    return CritiqueItem(
        CATEGORY_STOP_BEHAVIOR,
        VERDICT_FAIL,
        "No explicit stop command",
        "Skills must end with a zero-Twist publication.",
    )


def _critique_topic_boundary(code: str, declared: tuple[str, ...]) -> CritiqueItem:
    forbidden = {"/cmd_vel"}
    declared_set = set(declared)
    if declared_set & forbidden:
        return CritiqueItem(
            CATEGORY_TOPIC_BOUNDARY,
            VERDICT_FAIL,
            "Forbidden topic declared",
            f"Declared topics include {forbidden & declared_set}.",
        )
    if "/cmd_vel_requested" not in (declared_set | {"/cmd_vel_requested"} if "/cmd_vel_requested" in code else declared_set):
        return CritiqueItem(
            CATEGORY_TOPIC_BOUNDARY,
            VERDICT_WARN,
            "Topic allow-list not fully declared",
            "List requested topics so the supervisor can audit them.",
        )
    return CritiqueItem(
        CATEGORY_TOPIC_BOUNDARY, VERDICT_OK, "Topic boundary respected"
    )


def _critique_dependency(code: str) -> CritiqueItem:
    if "import subprocess" in code or "import os" in code:
        return CritiqueItem(
            CATEGORY_DEPENDENCY_RISK,
            VERDICT_FAIL,
            "Forbidden stdlib import",
            "subprocess / os imports are forbidden in skill candidates.",
        )
    return CritiqueItem(
        CATEGORY_DEPENDENCY_RISK, VERDICT_OK, "Dependencies look safe"
    )


def _critique_network(code: str) -> CritiqueItem:
    if "import socket" in code or "import requests" in code or "urlopen(" in code:
        return CritiqueItem(
            CATEGORY_NETWORK_RISK,
            VERDICT_FAIL,
            "Network access in skill",
            "Skills must not perform network I/O.",
        )
    return CritiqueItem(
        CATEGORY_NETWORK_RISK, VERDICT_OK, "No network access detected"
    )


def _critique_runtime(code: str, sanitizer: SkillLLMSanitizerResult) -> CritiqueItem:
    bad_reasons = {
        CandidateRejectionReason.SHELL_OR_CODE_EXECUTION.value,
        CandidateRejectionReason.DESTRUCTIVE_COMMAND.value,
        CandidateRejectionReason.SAFETY_OVERRIDE.value,
    }
    if set(sanitizer.reason_codes) & bad_reasons:
        return CritiqueItem(
            CATEGORY_RUNTIME_EXECUTION_RISK,
            VERDICT_FAIL,
            "Runtime execution risk",
            "Sanitizer flagged shell / safety-override / destructive command.",
        )
    return CritiqueItem(
        CATEGORY_RUNTIME_EXECUTION_RISK, VERDICT_OK, "No runtime execution risk"
    )


def _critique_uncertainty(candidate: SkillLLMCandidate) -> CritiqueItem:
    if candidate.known_uncertainties:
        return CritiqueItem(
            CATEGORY_UNCERTAINTY_DISCLOSURE,
            VERDICT_OK,
            "Model disclosed known uncertainties",
        )
    if candidate.confidence_label in {"high", "overconfident"}:
        return CritiqueItem(
            CATEGORY_UNCERTAINTY_DISCLOSURE,
            VERDICT_WARN,
            "Model claimed high confidence with no caveats",
            "Reviewer should look for hidden assumptions.",
        )
    return CritiqueItem(
        CATEGORY_UNCERTAINTY_DISCLOSURE, VERDICT_WARN, "No uncertainty disclosure"
    )


def critique_candidate(
    candidate: SkillLLMCandidate,
    sanitizer: SkillLLMSanitizerResult,
    validator: SkillLLMValidationResult,
) -> SafetyCritique:
    code = candidate.code or ""
    items = (
        _critique_actuator(code),
        _critique_timeout(code),
        _critique_stop(code),
        _critique_topic_boundary(code, candidate.declared_topics),
        _critique_dependency(code),
        _critique_network(code),
        _critique_runtime(code, sanitizer),
        _critique_uncertainty(candidate),
    )

    has_fail = any(item.verdict == VERDICT_FAIL for item in items)
    has_warn = any(item.verdict == VERDICT_WARN for item in items)
    if has_fail or not (validator.invoked and validator.accepted):
        overall = VERDICT_FAIL if has_fail else VERDICT_WARN
    elif has_warn:
        overall = VERDICT_WARN
    else:
        overall = VERDICT_OK
    return SafetyCritique(
        candidate_id=candidate.candidate_id,
        overall_verdict=overall,
        items=items,
    )


def critique_to_dict(critique: SafetyCritique) -> dict[str, object]:
    return {
        "candidate_id": critique.candidate_id,
        "overall_verdict": critique.overall_verdict,
        "items": [
            {
                "category": item.category,
                "verdict": item.verdict,
                "summary": item.summary,
                "detail": item.detail,
            }
            for item in critique.items
        ],
    }


__all__ = [
    "CATEGORY_ACTUATOR_AUTHORITY",
    "CATEGORY_DEPENDENCY_RISK",
    "CATEGORY_NETWORK_RISK",
    "CATEGORY_RUNTIME_EXECUTION_RISK",
    "CATEGORY_STOP_BEHAVIOR",
    "CATEGORY_TIMEOUT_SAFETY",
    "CATEGORY_TOPIC_BOUNDARY",
    "CATEGORY_UNCERTAINTY_DISCLOSURE",
    "CRITIQUE_CATEGORIES",
    "CritiqueItem",
    "SafetyCritique",
    "VERDICT_FAIL",
    "VERDICT_OK",
    "VERDICT_WARN",
    "critique_candidate",
    "critique_to_dict",
]
