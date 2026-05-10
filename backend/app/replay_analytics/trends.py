"""Cross-incident replay trend analysis.

Aggregates per-incident :class:`ReplayCoverageReport` and
:class:`ReplayQualityScore` instances into a deterministic
:class:`ReplayTrend` table. The aggregator is read-only and never
invents statistical claims; "most common" tables are deterministic
counts ordered by frequency then label.
"""

from __future__ import annotations

from collections import Counter
from typing import Iterable

from app.replay_analytics.coverage import ReplayCoverageReport
from app.replay_analytics.loader import LoadedReplayBundle
from app.replay_analytics.models import (
    ReplayQualityScore,
    ReplayTrend,
)
from app.replay_analytics.scoring import quality_bucket


def build_trends(
    *,
    bundles: Iterable[LoadedReplayBundle],
    coverages: Iterable[ReplayCoverageReport],
    scores: Iterable[ReplayQualityScore],
    gaps_by_incident: dict[str, list[dict]] | None = None,
) -> ReplayTrend:
    """Build the trend tables from per-incident analytics."""

    bundles = list(bundles)
    coverages_list = list(coverages)
    scores_list = list(scores)
    gaps_by_incident = dict(gaps_by_incident or {})

    bag_counter: Counter[str] = Counter()
    coverage_counter: Counter[str] = Counter()
    review_counter: Counter[str] = Counter()
    origin_counter: Counter[str] = Counter()
    bucket_counter: Counter[str] = Counter()
    safety_state_counter: Counter[str] = Counter()
    outcome_counter: Counter[str] = Counter()
    missing_topic_counter: Counter[str] = Counter()
    gap_counter: Counter[str] = Counter()

    for bundle in bundles:
        bag_counter[bundle.bag_status] += 1
        origin_counter[bundle.evidence_origin] += 1
        if bundle.incident_report:
            for state in bundle.incident_report.get("safety_states", []) or []:
                if isinstance(state, str):
                    safety_state_counter[state] += 1
            outcome = bundle.incident_report.get("outcome")
            if isinstance(outcome, str) and outcome:
                outcome_counter[outcome] += 1
        if bundle.replay_manifest:
            for topic in bundle.replay_manifest.get("missing_topics", []) or []:
                if isinstance(topic, str):
                    missing_topic_counter[topic] += 1
        if bundle.review_audit:
            review_counter[
                bundle.review_audit.get("status", "not_started")
            ] += 1
        else:
            review_counter["not_started"] += 1

    for cov in coverages_list:
        coverage_counter[cov.coverage_status.value] += 1

    for score in scores_list:
        bucket_counter[quality_bucket(score.score)] += 1

    for incident_id, gap_list in gaps_by_incident.items():
        for gap in gap_list:
            label = gap.get("label", "")
            if label:
                gap_counter[label] += 1

    notes: list[str] = []
    if not bundles:
        notes.append("no replay-review bundles inspected")

    return ReplayTrend(
        bag_status_distribution=dict(bag_counter),
        coverage_status_distribution=dict(coverage_counter),
        review_completion_distribution=dict(review_counter),
        evidence_origin_distribution=dict(origin_counter),
        quality_score_buckets=dict(bucket_counter),
        most_common_safety_states=_top(safety_state_counter),
        most_common_outcomes=_top(outcome_counter),
        most_common_missing_topics=_top(missing_topic_counter),
        most_common_gaps=_top(gap_counter),
        incident_count=len(bundles),
        notes=tuple(notes),
    )


def _top(counter: Counter[str], *, limit: int = 10) -> list[tuple[str, int]]:
    """Deterministic top-N (sorted by count descending, then label asc)."""

    items = sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))
    return items[:limit]
