"""Bridge from rehearsal runtime to an analytics artefact.

The analytics artefact is per-rehearsal: it counts approvals,
rejections, aborts, completions, supervisor rejections, validator
rejections, and asserts deterministic replay stability. No
probabilistic analytics; no AI conclusions.
"""

from __future__ import annotations

from typing import Iterable, Mapping

from .models import (
    MissionRehearsalAnalyticsResult,
    MissionRehearsalDecision,
    MissionRehearsalEvent,
    MissionRehearsalRuntime,
    RehearsalDecisionStatus,
    RehearsalEventType,
    RehearsalStatus,
)


def build_analytics_result(
    *,
    runtime: MissionRehearsalRuntime,
    decision: MissionRehearsalDecision,
    validation_diagnostics: Iterable[Mapping[str, object]] = (),
) -> MissionRehearsalAnalyticsResult:
    diagnostics = tuple(validation_diagnostics)
    approved = decision.decision_status == RehearsalDecisionStatus.APPROVED.value
    rejected = (
        runtime.final_status == RehearsalStatus.REJECTED.value
        or not approved
    )
    aborted = runtime.final_status == RehearsalStatus.ABORTED.value
    completed = runtime.final_status == RehearsalStatus.COMPLETED.value
    validator_rejection = any(
        isinstance(d, Mapping) and d.get("severity") == "rejection"
        for d in diagnostics
    )

    deterministic_stable = bool(runtime.deterministic_hash)
    notes: list[str] = [
        "Counts reflect this single rehearsal; aggregate analytics roll "
        "up across many rehearsals in programme review.",
    ]
    if not approved:
        notes.append("Supervisor rejection short-circuited the rehearsal.")
    if validator_rejection:
        notes.append("Validator rejection short-circuited the rehearsal.")

    return MissionRehearsalAnalyticsResult(
        mission_id=runtime.mission_id,
        rehearsal_count=1,
        approved_count=1 if approved and not validator_rejection else 0,
        rejected_count=1 if rejected else 0,
        aborted_count=1 if aborted else 0,
        completed_count=1 if completed else 0,
        supervisor_rejection_count=0 if approved else 1,
        validator_rejection_count=1 if validator_rejection else 0,
        deterministic_replay_stable=deterministic_stable,
        notes=tuple(notes),
    )
