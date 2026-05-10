"""Programme-level governance health rollup.

Six discipline categories are evaluated independently from the
loaded history and the drift report. The overall health is the
worst rating across them. Every discipline records the reasons +
triggering artefacts so the report shows exactly what produced the
rating.

Discipline rating order (worst -> best): concerning > weak >
acceptable > strong > unknown. ``unknown`` is reserved for
disciplines with no available evidence — a programme review on a
fresh repo should not report ``strong`` just because there's
nothing to find.
"""

from __future__ import annotations

from typing import Iterable

from app.programme_review.models import (
    DisciplineCategory,
    DisciplineRating,
    DisciplineResult,
    DriftReport,
    DriftSeverity,
    GovernanceHealth,
    GovernanceHealthReport,
    HistoryRecord,
    LoadedHistory,
)


_RATING_ORDER: dict[DisciplineRating, int] = {
    DisciplineRating.UNKNOWN: 0,
    DisciplineRating.STRONG: 1,
    DisciplineRating.ACCEPTABLE: 2,
    DisciplineRating.WEAK: 3,
    DisciplineRating.CONCERNING: 4,
}


def assess_governance_health(
    *,
    history: LoadedHistory,
    drift_report: DriftReport,
) -> GovernanceHealthReport:
    """Compose the governance health report."""

    disciplines = [
        _evidence_discipline(history),
        _replay_discipline(history, drift_report),
        _ci_discipline(history, drift_report),
        _traceability_discipline(history),
        _runtime_qualification_discipline(history),
        _review_completion_discipline(history),
    ]
    overall = _overall_from(disciplines)
    notes: list[str] = []
    if history.warnings:
        notes.append(
            f"loader emitted {len(history.warnings)} warning(s); see history"
        )
    return GovernanceHealthReport(
        overall=overall, disciplines=disciplines, notes=tuple(notes)
    )


# ---------------------------------------------------------------------------
# Per-discipline checks.
# ---------------------------------------------------------------------------


def _evidence_discipline(history: LoadedHistory) -> DisciplineResult:
    """Discipline category: evidence ingestion + completeness."""

    reasons: list[str] = []
    artefacts: list[str] = []

    if not history.reliability_impact and not history.replay_review:
        return DisciplineResult(
            category=DisciplineCategory.EVIDENCE,
            rating=DisciplineRating.UNKNOWN,
            reasons=("no reliability-impact bundles or replay reviews loaded",),
        )
    if history.warnings:
        reasons.append(
            f"loader recorded {len(history.warnings)} warning(s) — "
            "investigate before treating evidence as complete"
        )
        artefacts.extend(history.warnings[:3])
    # Static-only ratio across replay reviews.
    static_count = sum(
        1
        for record in history.replay_review
        if record.payload.get("bag_status") == "static_only"
    )
    total_reviews = len(history.replay_review)
    rating: DisciplineRating
    if total_reviews == 0:
        rating = DisciplineRating.UNKNOWN
        reasons.append("no replay-review reports inspected")
    elif static_count == total_reviews:
        rating = DisciplineRating.WEAK
        reasons.append(
            f"all {total_reviews} replay-review report(s) are static-only"
        )
    elif static_count > total_reviews / 2:
        rating = DisciplineRating.ACCEPTABLE
        reasons.append(
            f"{static_count}/{total_reviews} replay reviews are static-only"
        )
    else:
        rating = DisciplineRating.STRONG
        reasons.append(
            f"replay-review coverage diversified: {static_count}/{total_reviews} "
            "static-only"
        )
    if not reasons:
        reasons.append("evidence ingestion clean")
    return DisciplineResult(
        category=DisciplineCategory.EVIDENCE,
        rating=rating,
        reasons=tuple(reasons),
        triggering_artifacts=tuple(artefacts),
    )


def _replay_discipline(
    history: LoadedHistory, drift_report: DriftReport
) -> DisciplineResult:
    """Discipline category: replay quality + drift."""

    if not history.replay_analytics and not history.replay_review:
        return DisciplineResult(
            category=DisciplineCategory.REPLAY,
            rating=DisciplineRating.UNKNOWN,
            reasons=("no replay analytics or review history loaded",),
        )
    severity = drift_report.severity
    reasons: list[str] = []
    artefacts: list[str] = []
    if severity == DriftSeverity.CRITICAL_REGRESSION:
        rating = DisciplineRating.CONCERNING
        reasons.append("drift report carries critical regression(s)")
        for finding in drift_report.findings:
            if finding.severity == DriftSeverity.CRITICAL_REGRESSION:
                artefacts.append(finding.label)
    elif severity == DriftSeverity.REGRESSION:
        rating = DisciplineRating.WEAK
        reasons.append("drift report carries a regression")
    elif severity == DriftSeverity.WARNING:
        rating = DisciplineRating.ACCEPTABLE
        reasons.append("drift report carries warnings only")
    else:
        rating = DisciplineRating.STRONG
        reasons.append("no significant drift detected")
    return DisciplineResult(
        category=DisciplineCategory.REPLAY,
        rating=rating,
        reasons=tuple(reasons),
        triggering_artifacts=tuple(artefacts),
    )


def _ci_discipline(
    history: LoadedHistory, drift_report: DriftReport
) -> DisciplineResult:
    """Discipline category: CI gate outcomes."""

    if not history.reliability_impact:
        return DisciplineResult(
            category=DisciplineCategory.CI,
            rating=DisciplineRating.UNKNOWN,
            reasons=("no reliability-impact bundles loaded",),
        )
    pass_count = warning_count = failure_count = not_executed_count = 0
    for record in history.reliability_impact:
        gate = record.payload.get("gate_decision") or {}
        status = gate.get("status")
        if status == "passed":
            pass_count += 1
        elif status == "warning":
            warning_count += 1
        elif status == "failed":
            failure_count += 1
        else:
            not_executed_count += 1
    reasons = [
        f"gate counts: passed={pass_count} warning={warning_count} "
        f"failed={failure_count} not_executed={not_executed_count}"
    ]
    if failure_count == 0 and warning_count == 0:
        rating = DisciplineRating.STRONG
    elif failure_count == 0 and warning_count <= pass_count:
        rating = DisciplineRating.ACCEPTABLE
    elif failure_count == 0:
        rating = DisciplineRating.WEAK
        reasons.append("warnings outweigh passes")
    elif failure_count <= 1:
        rating = DisciplineRating.WEAK
        reasons.append("one or more gate failures recorded")
    else:
        rating = DisciplineRating.CONCERNING
        reasons.append("repeated gate failures across history")
    return DisciplineResult(
        category=DisciplineCategory.CI,
        rating=rating,
        reasons=tuple(reasons),
    )


def _traceability_discipline(history: LoadedHistory) -> DisciplineResult:
    """Discipline category: requirement traceability coverage."""

    if not history.reliability_impact:
        return DisciplineResult(
            category=DisciplineCategory.TRACEABILITY,
            rating=DisciplineRating.UNKNOWN,
            reasons=("no reliability-impact bundles loaded",),
        )
    coverage_counts: list[int] = []
    for record in history.reliability_impact:
        impacts = record.payload.get("requirement_impacts", [])
        if not isinstance(impacts, list):
            continue
        ids: set[str] = set()
        for entry in impacts:
            if isinstance(entry, dict):
                for rid in entry.get("requirement_ids", []) or []:
                    if isinstance(rid, str):
                        ids.add(rid)
        coverage_counts.append(len(ids))
    reasons: list[str] = []
    if not coverage_counts:
        return DisciplineResult(
            category=DisciplineCategory.TRACEABILITY,
            rating=DisciplineRating.UNKNOWN,
            reasons=("no requirement impacts found in history",),
        )
    latest = coverage_counts[-1]
    reasons.append(
        f"latest reliability-impact bundle mapped {latest} requirement id(s)"
    )
    if latest >= 5:
        rating = DisciplineRating.STRONG
    elif latest >= 1:
        rating = DisciplineRating.ACCEPTABLE
    else:
        rating = DisciplineRating.WEAK
        reasons.append(
            "no requirement ids mapped in the latest bundle; classifier may need work"
        )
    if any(c > latest for c in coverage_counts[:-1]):
        rating = (
            DisciplineRating.WEAK
            if rating == DisciplineRating.ACCEPTABLE
            else rating
        )
        reasons.append("traceability coverage has declined within the window")
    return DisciplineResult(
        category=DisciplineCategory.TRACEABILITY,
        rating=rating,
        reasons=tuple(reasons),
    )


def _runtime_qualification_discipline(
    history: LoadedHistory,
) -> DisciplineResult:
    """Discipline category: runtime qualification runs."""

    if not history.runtime_qualification:
        return DisciplineResult(
            category=DisciplineCategory.RUNTIME_QUALIFICATION,
            rating=DisciplineRating.UNKNOWN,
            reasons=("no runtime qualification summaries loaded",),
        )
    reasons: list[str] = []
    failures = 0
    statuses: list[str] = []
    for record in history.runtime_qualification:
        status = record.payload.get("overall_status") or record.payload.get(
            "status"
        )
        if isinstance(status, str):
            statuses.append(status)
            if status == "failed":
                failures += 1
    reasons.append(f"qualification statuses observed: {statuses}")
    if failures == 0:
        rating = DisciplineRating.STRONG
    elif failures <= 1:
        rating = DisciplineRating.ACCEPTABLE
    else:
        rating = DisciplineRating.WEAK
        reasons.append("multiple qualification failures recorded")
    return DisciplineResult(
        category=DisciplineCategory.RUNTIME_QUALIFICATION,
        rating=rating,
        reasons=tuple(reasons),
    )


def _review_completion_discipline(history: LoadedHistory) -> DisciplineResult:
    """Discipline category: operator review completion."""

    if not history.incident:
        return DisciplineResult(
            category=DisciplineCategory.REVIEW_COMPLETION,
            rating=DisciplineRating.UNKNOWN,
            reasons=("no incident bundles loaded",),
        )
    completed = 0
    total = 0
    reasons: list[str] = []
    for record in history.incident:
        total += 1
        completion = record.payload.get("review_completion_status")
        if completion == "completed":
            completed += 1
    if total == 0:
        return DisciplineResult(
            category=DisciplineCategory.REVIEW_COMPLETION,
            rating=DisciplineRating.UNKNOWN,
            reasons=("no incident bundles loaded",),
        )
    reasons.append(
        f"completed_reviews={completed}/{total} (rest are not_started or partial)"
    )
    if completed == 0:
        rating = DisciplineRating.WEAK
    elif completed == total:
        rating = DisciplineRating.STRONG
    elif completed >= total / 2:
        rating = DisciplineRating.ACCEPTABLE
    else:
        rating = DisciplineRating.WEAK
    return DisciplineResult(
        category=DisciplineCategory.REVIEW_COMPLETION,
        rating=rating,
        reasons=tuple(reasons),
    )


# ---------------------------------------------------------------------------
# Composition.
# ---------------------------------------------------------------------------


def _overall_from(disciplines: list[DisciplineResult]) -> GovernanceHealth:
    """Compose the overall programme health.

    Worst-discipline-wins, except that ``unknown`` is informational
    rather than a downgrade — a single unknown should not pull a
    `strong` aggregate down to `weak`. The mapping prefers
    conservatism: `concerning` if any discipline is concerning;
    `weak` if any is weak; `acceptable` if any is acceptable; else
    `strong` if any discipline reported a rating; else `critical`
    when every discipline is `unknown` AND there is no other signal.
    """

    if not disciplines:
        return GovernanceHealth.CRITICAL
    if any(d.rating == DisciplineRating.CONCERNING for d in disciplines):
        return GovernanceHealth.CONCERNING
    if any(d.rating == DisciplineRating.WEAK for d in disciplines):
        return GovernanceHealth.WEAK
    if any(d.rating == DisciplineRating.ACCEPTABLE for d in disciplines):
        return GovernanceHealth.ACCEPTABLE
    if any(d.rating == DisciplineRating.STRONG for d in disciplines):
        return GovernanceHealth.STRONG
    # Every discipline returned ``unknown``.
    return GovernanceHealth.WEAK
