"""Rehearsal supervisor — the authoritative gate.

The supervisor receives the validated plan and any validator
diagnostics. It produces a :class:`MissionRehearsalDecision`. The
runtime refuses to enter the ``rehearsing`` state unless the
decision is ``approved``.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Mapping

from .models import (
    MissionRehearsalDecision,
    MissionRehearsalPlan,
    RehearsalDecisionStatus,
    RehearsalSafetyStatus,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def review_plan(
    plan: MissionRehearsalPlan,
    *,
    validation_diagnostics: Iterable[Mapping[str, object]] = (),
    operator: str = "",
    decided_at_utc: str | None = None,
) -> MissionRehearsalDecision:
    """Return an authoritative decision for the supplied plan.

    The supervisor does not re-run the validator. It treats every
    validator rejection as a binding rejection and adds its own
    layer of policy on top (e.g. blocked risk band).
    """

    timestamp = decided_at_utc or _now_iso()
    diagnostics = tuple(validation_diagnostics)

    rejection_reasons = tuple(
        str(d.get("code", ""))
        for d in diagnostics
        if isinstance(d, Mapping) and d.get("severity") == "rejection"
    )
    has_validator_rejection = bool(rejection_reasons)

    rationale: list[str] = [
        "Supervisor authority is preserved; no motion runs without this approval.",
    ]
    if has_validator_rejection:
        rationale.append("Validator rejected the plan; supervisor cannot approve.")
    if plan.risk_band == "blocked":
        rationale.append(
            "Risk band 'blocked' indicates the plan cannot be approved."
        )
        rejection_reasons = rejection_reasons + ("safety_blocked",)
    elif plan.risk_band == "restricted":
        rationale.append(
            "Risk band 'restricted' requires human review before approval."
        )

    if rejection_reasons or plan.risk_band == "blocked":
        return MissionRehearsalDecision(
            decision_id=f"decision-{plan.mission_id}",
            decision_status=RehearsalDecisionStatus.REJECTED.value,
            safety_status=RehearsalSafetyStatus.UNSAFE_REJECTED.value,
            rationale=tuple(rationale),
            rejected_reasons=tuple(dict.fromkeys(rejection_reasons)),
            allowed_topics=plan.requested_topics,
            forbidden_topics=plan.forbidden_topics,
            requires_human_review=True,
            decided_at_utc=timestamp,
        )

    if plan.risk_band == "restricted":
        return MissionRehearsalDecision(
            decision_id=f"decision-{plan.mission_id}",
            decision_status=RehearsalDecisionStatus.NEEDS_REVIEW.value,
            safety_status=RehearsalSafetyStatus.REQUIRES_REVIEW.value,
            rationale=tuple(rationale),
            rejected_reasons=(),
            allowed_topics=plan.requested_topics,
            forbidden_topics=plan.forbidden_topics,
            requires_human_review=True,
            decided_at_utc=timestamp,
        )

    rationale.append(
        "Bounded motion, allowed topics, and stop condition verified."
    )
    if operator:
        rationale.append(f"Approving operator: {operator}")

    return MissionRehearsalDecision(
        decision_id=f"decision-{plan.mission_id}",
        decision_status=RehearsalDecisionStatus.APPROVED.value,
        safety_status=(
            RehearsalSafetyStatus.SAFE.value
            if plan.risk_band == "low"
            else RehearsalSafetyStatus.GUARDED.value
        ),
        rationale=tuple(rationale),
        rejected_reasons=(),
        allowed_topics=plan.requested_topics,
        forbidden_topics=plan.forbidden_topics,
        requires_human_review=False,
        decided_at_utc=timestamp,
    )
