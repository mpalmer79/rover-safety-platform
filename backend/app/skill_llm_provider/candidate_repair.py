"""Deterministic repair suggestions for LLM-proposed skills.

Phase 19 repair surface is **suggestion only**. We never auto-fix
unsafe code; we never promote a rejected candidate to accepted.
The suggestions exist so an operator can read a candidate, see
exactly what is wrong, and edit the source themselves.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import (
    CandidateRejectionReason,
    SkillLLMCandidate,
    SkillLLMSanitizerResult,
    SkillLLMValidationResult,
)


REPAIR_STATUS_SUGGESTION_ONLY: str = "suggestion_only"
REPAIR_STATUS_NOT_APPLICABLE: str = "not_applicable"
REPAIR_STATUS_REQUIRES_HUMAN_REVIEW: str = "requires_human_review"


@dataclass(frozen=True)
class RepairSuggestion:
    """One suggested edit, in plain English, plus a pseudocode hint."""

    code: str
    title: str
    rationale: str
    hint: str
    status: str = REPAIR_STATUS_SUGGESTION_ONLY


@dataclass(frozen=True)
class RepairBundle:
    candidate_id: str
    status: str = REPAIR_STATUS_SUGGESTION_ONLY
    suggestions: tuple[RepairSuggestion, ...] = ()


def _looks_like_unbounded_loop(code: str) -> bool:
    return "while true" in code.lower() or "while 1" in code.lower()


def _publishes_cmd_vel_directly(code: str) -> bool:
    return "publish(\"/cmd_vel\"" in code or "publish('/cmd_vel'" in code


def _missing_stop_command(code: str) -> bool:
    code_lower = code.lower()
    return all(
        token not in code_lower
        for token in ("twist()", "linear.x = 0", "publish_zero", "stop_command")
    )


def _missing_timeout(code: str) -> bool:
    code_lower = code.lower()
    return all(
        token not in code_lower
        for token in ("timeout", "monotonic", "deadline", "elapsed")
    )


def suggest_repairs(
    candidate: SkillLLMCandidate,
    sanitizer: SkillLLMSanitizerResult,
    validator: SkillLLMValidationResult,
) -> RepairBundle:
    """Return a deterministic list of repair suggestions.

    The function never modifies ``candidate``. It returns a bundle
    with status ``suggestion_only`` (or ``not_applicable`` when no
    repair is needed). For rejections that cannot be repaired
    safely (shell execution, network access, safety override) the
    bundle's status escalates to ``requires_human_review``.
    """

    suggestions: list[RepairSuggestion] = []
    requires_human_review = False
    code = candidate.code or ""

    if _publishes_cmd_vel_directly(code):
        suggestions.append(
            RepairSuggestion(
                code="repair.use_cmd_vel_requested",
                title="Publish to /cmd_vel_requested instead of /cmd_vel",
                rationale=(
                    "Only the safety supervisor is allowed to publish "
                    "to /cmd_vel. Skills must request motion via "
                    "/cmd_vel_requested so the supervisor can clamp + "
                    "approve the command."
                ),
                hint=(
                    "publisher = node.create_publisher(Twist, "
                    "'/cmd_vel_requested', 10)"
                ),
            )
        )
        requires_human_review = True

    if _missing_stop_command(code):
        suggestions.append(
            RepairSuggestion(
                code="repair.append_stop_command",
                title="Append a final zero-Twist stop command",
                rationale=(
                    "Every skill must end with a zero Twist publication "
                    "so the supervisor sees an explicit stop request."
                ),
                hint=(
                    "stop = Twist(); stop.linear.x = 0.0; stop.angular.z = 0.0\n"
                    "publisher.publish(stop)"
                ),
            )
        )

    if _missing_timeout(code):
        suggestions.append(
            RepairSuggestion(
                code="repair.add_bounded_timeout",
                title="Add a bounded timeout derived from distance / speed",
                rationale=(
                    "An open-ended loop without a deadline cannot be "
                    "rehearsed deterministically. Compute "
                    "duration = bounded_distance_m / bounded_speed_mps "
                    "and stop when monotonic() - start > duration."
                ),
                hint=(
                    "deadline = time.monotonic() + bounded_distance_m / max(0.05, bounded_speed_mps)"
                ),
            )
        )

    if _looks_like_unbounded_loop(code):
        suggestions.append(
            RepairSuggestion(
                code="repair.bound_loop",
                title="Replace `while True:` with a bounded-deadline loop",
                rationale=(
                    "Unbounded loops are forbidden. Wrap motion logic "
                    "in `while time.monotonic() < deadline:` so the "
                    "rehearsal terminates."
                ),
                hint=(
                    "while time.monotonic() < deadline:\n"
                    "    # publish bounded request\n"
                    "    rate.sleep()"
                ),
            )
        )

    # Categorical escalation: certain rejection reasons can never be
    # auto-repaired and need a reviewer to evaluate intent.
    escalation_reasons = {
        CandidateRejectionReason.SHELL_OR_CODE_EXECUTION.value,
        CandidateRejectionReason.NETWORK_ACCESS.value,
        CandidateRejectionReason.SAFETY_OVERRIDE.value,
        CandidateRejectionReason.DESTRUCTIVE_COMMAND.value,
    }
    for reason in sanitizer.reason_codes:
        if reason in escalation_reasons:
            requires_human_review = True
            suggestions.append(
                RepairSuggestion(
                    code=f"escalate.{reason}",
                    title=f"Human review required for {reason}",
                    rationale=(
                        "This rejection cannot be auto-repaired. A "
                        "reviewer must inspect the prompt + the model "
                        "output and decide whether to retry with a "
                        "stricter prompt or discard the candidate."
                    ),
                    hint="(no automatic edit available)",
                    status=REPAIR_STATUS_REQUIRES_HUMAN_REVIEW,
                )
            )

    if not suggestions:
        return RepairBundle(
            candidate_id=candidate.candidate_id,
            status=REPAIR_STATUS_NOT_APPLICABLE,
        )

    status = (
        REPAIR_STATUS_REQUIRES_HUMAN_REVIEW
        if requires_human_review
        else REPAIR_STATUS_SUGGESTION_ONLY
    )
    return RepairBundle(
        candidate_id=candidate.candidate_id,
        status=status,
        suggestions=tuple(suggestions),
    )


def repair_bundle_to_dict(bundle: RepairBundle) -> dict[str, object]:
    return {
        "candidate_id": bundle.candidate_id,
        "status": bundle.status,
        "suggestions": [
            {
                "code": s.code,
                "title": s.title,
                "rationale": s.rationale,
                "hint": s.hint,
                "status": s.status,
            }
            for s in bundle.suggestions
        ],
    }


__all__ = [
    "REPAIR_STATUS_NOT_APPLICABLE",
    "REPAIR_STATUS_REQUIRES_HUMAN_REVIEW",
    "REPAIR_STATUS_SUGGESTION_ONLY",
    "RepairBundle",
    "RepairSuggestion",
    "repair_bundle_to_dict",
    "suggest_repairs",
]
