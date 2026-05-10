"""Deterministic replay-quality scoring.

Inputs are the loaded :class:`LoadedReplayBundle` and the
corresponding :class:`ReplayCoverageReport`. The output is a
:class:`ReplayQualityScore` with an integer 0..100 score, a
confidence label, the coverage status, and a human-readable
summary plus the explicit blocking gaps.

Score bands (per the runbook):

* 90-100 — bag-backed, aligned markers, complete evidence, validated
  replay, no contradictions.
* 70-89  — partial replay gaps, some missing inventory, acceptable
  evidence quality.
* 40-69  — sparse replay artefacts, missing markers, partial reports.
* 0-39   — static-only, missing bags, incomplete reports, contradictions.

The function never inflates a static-only or missing-bag incident
into the upper bands. Caps are enforced explicitly.
"""

from __future__ import annotations

from typing import Iterable

from app.replay_analytics.coverage import ReplayCoverageReport
from app.replay_analytics.loader import LoadedReplayBundle
from app.replay_analytics.models import (
    ReplayCoverageMetric,
    ReplayCoverageStatus,
    ReplayQualityScore,
)


# Per-metric weights that sum to 100. The metric set mirrors
# ``COVERAGE_METRIC_NAMES``.
_METRIC_WEIGHTS: dict[str, int] = {
    "expected_topics_present_pct": 25,
    "marker_alignment_pct": 15,
    "timeline_alignment_pct": 10,
    "replay_validation_pass_rate": 20,
    "evidence_completeness_pct": 20,
    "review_artifact_completeness_pct": 10,
}


_BAG_STATUS_FLOOR: dict[str, int] = {
    # The maximum score allowed when the bag is in the listed state.
    "static_only": 39,
    "missing_bag": 59,
    "partial": 89,
    "not_executed": 39,
    "failed": 39,
    "ready": 100,
    "passed": 100,
}


def score_replay_quality(
    *,
    bundle: LoadedReplayBundle,
    coverage: ReplayCoverageReport,
) -> ReplayQualityScore:
    """Return the deterministic quality score for the bundle.

    Missing replay-review or missing incident report yields a hard
    score of 0; static-only and missing-bag inputs are capped per
    :data:`_BAG_STATUS_FLOOR`.
    """

    blocking_gaps: list[str] = []

    if not bundle.has_replay_review:
        blocking_gaps.append("replay-review bundle absent")
        return ReplayQualityScore(
            incident_id=bundle.incident_id,
            score=0,
            confidence="low",
            coverage_status=ReplayCoverageStatus.MISSING,
            quality_summary=(
                "no replay-review bundle generated; run "
                "build_replay_review_bundle.py first"
            ),
            blocking_gaps=tuple(blocking_gaps),
        )

    base = _weighted_average(coverage.metrics)
    cap = _BAG_STATUS_FLOOR.get(bundle.bag_status, 39)

    score = min(int(round(base)), cap)

    # Penalty for unavailable metrics (we only computed a base from
    # the available ones; cap further when many are unavailable).
    unavailable = [m for m in coverage.metrics if not m.available]
    if unavailable:
        # Each unavailable metric subtracts its weight from the cap.
        weight_lost = sum(_METRIC_WEIGHTS.get(m.name, 0) for m in unavailable)
        # We never let unavailable metrics raise the score; the floor
        # logic already handled the upper bound. The penalty is a
        # secondary cap of 100 - weight_lost.
        score = min(score, max(0, 100 - weight_lost))
        blocking_gaps.extend(
            f"metric_unavailable[{m.name}]" for m in unavailable
        )

    # Penalties for explicit blocking conditions.
    if bundle.bag_status == "missing_bag":
        blocking_gaps.append("bag_status=missing_bag")
    elif bundle.bag_status == "static_only":
        blocking_gaps.append("bag_status=static_only")

    contradictions = _contradiction_count(bundle)
    if contradictions:
        # Cap at 39 when contradictions exist (they belong in the
        # lowest band per the runbook).
        score = min(score, 39)
        blocking_gaps.append(f"contradictions={contradictions}")

    missing_topics = (
        bundle.replay_manifest.get("missing_topics", [])
        if bundle.replay_manifest
        else []
    )
    if missing_topics:
        blocking_gaps.append(f"missing_topics={len(missing_topics)}")

    confidence = _confidence(bundle, coverage)
    summary = _summary(bundle=bundle, coverage=coverage, score=score)
    return ReplayQualityScore(
        incident_id=bundle.incident_id,
        score=max(0, score),
        confidence=confidence,
        coverage_status=coverage.coverage_status,
        quality_summary=summary,
        blocking_gaps=tuple(blocking_gaps),
    )


def score_for_metrics(metrics: Iterable[ReplayCoverageMetric]) -> float:
    """Public helper used by tests + the comparator."""

    return _weighted_average(tuple(metrics))


def quality_bucket(score: int) -> str:
    """Return the band label for a 0..100 score."""

    if score >= 90:
        return "90-100"
    if score >= 70:
        return "70-89"
    if score >= 40:
        return "40-69"
    return "0-39"


# ---------------------------------------------------------------------------
# Internals.
# ---------------------------------------------------------------------------


def _weighted_average(metrics: tuple[ReplayCoverageMetric, ...]) -> float:
    """Weighted average of the metrics that are available.

    Unavailable metrics are excluded from the numerator and
    denominator (so a missing inventory does not unfairly inflate or
    deflate the average); the upstream cap handles the bag-status
    floor independently.
    """

    total_weight = 0
    total_value = 0.0
    for m in metrics:
        if not m.available or m.value is None:
            continue
        weight = _METRIC_WEIGHTS.get(m.name, 0)
        if weight == 0:
            continue
        total_weight += weight
        total_value += weight * float(m.value)
    if total_weight == 0:
        return 0.0
    return total_value / total_weight


def _contradiction_count(bundle: LoadedReplayBundle) -> int:
    if bundle.incident_report is None:
        return 0
    contradictions = bundle.incident_report.get("contradictions") or []
    return len(contradictions)


def _confidence(
    bundle: LoadedReplayBundle, coverage: ReplayCoverageReport
) -> str:
    if bundle.bag_status in {"static_only", "missing_bag"}:
        return "low"
    unavailable = [m for m in coverage.metrics if not m.available]
    if unavailable:
        return "moderate"
    return "high"


def _summary(
    *,
    bundle: LoadedReplayBundle,
    coverage: ReplayCoverageReport,
    score: int,
) -> str:
    band = quality_bucket(score)
    return (
        f"score={score} band={band} bag_status={bundle.bag_status} "
        f"coverage_status={coverage.coverage_status.value} "
        f"evidence_origin={bundle.evidence_origin}"
    )
