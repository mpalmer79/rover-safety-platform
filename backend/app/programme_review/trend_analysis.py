"""Deterministic trend classification.

Each metric produces a :class:`TrendSeries` of observations. The
classifier maps a series of available values into one of:

* ``improving`` — last value ≥ first value + threshold;
* ``degrading`` — last value ≤ first value − threshold;
* ``stable`` — values within ±threshold;
* ``volatile`` — at least one direction-change of ≥ ``volatility_threshold``;
* ``insufficient_history`` — fewer than two available values.

The classifier never forecasts: the rules look at recorded
observations only. Rolling-3 and rolling-5 categories are computed
on the trailing windows so a degrading recent run is visible even
when the long-window category is stable.
"""

from __future__ import annotations

from typing import Iterable, Optional

from app.programme_review.models import (
    HistoryRecord,
    LoadedHistory,
    TrendCategory,
    TrendObservation,
    TrendReport,
    TrendSeries,
)


# Per-metric thresholds. Picked to match prior phases: a 5-point
# score move is "stable", 10 is "warning territory", 25 is a
# regression.
_DEFAULT_STABLE_THRESHOLD: float = 5.0
_DEFAULT_VOLATILITY_THRESHOLD: float = 10.0


def _classify_window(
    values: list[float],
    *,
    stable_threshold: float = _DEFAULT_STABLE_THRESHOLD,
    volatility_threshold: float = _DEFAULT_VOLATILITY_THRESHOLD,
) -> TrendCategory:
    """Classify a list of consecutive numeric samples."""

    if len(values) < 2:
        return TrendCategory.INSUFFICIENT_HISTORY
    first = values[0]
    last = values[-1]
    delta = last - first
    # Volatility check: any direction-change of ≥ threshold.
    swings = 0
    for i in range(1, len(values) - 1):
        prev_delta = values[i] - values[i - 1]
        next_delta = values[i + 1] - values[i]
        if (
            (prev_delta >= volatility_threshold and next_delta <= -volatility_threshold)
            or (prev_delta <= -volatility_threshold and next_delta >= volatility_threshold)
        ):
            swings += 1
    if swings:
        return TrendCategory.VOLATILE
    if delta >= stable_threshold:
        return TrendCategory.IMPROVING
    if delta <= -stable_threshold:
        return TrendCategory.DEGRADING
    return TrendCategory.STABLE


def _classify_series(observations: list[TrendObservation]) -> TrendCategory:
    values = [o.value for o in observations if o.value is not None]
    if len(values) < 2:
        return TrendCategory.INSUFFICIENT_HISTORY
    return _classify_window(values)


def _rolling_category(
    observations: list[TrendObservation], *, window: int
) -> TrendCategory:
    values = [o.value for o in observations if o.value is not None]
    if len(values) < 2:
        return TrendCategory.INSUFFICIENT_HISTORY
    trailing = values[-window:]
    return _classify_window(trailing)


def build_series_from_payloads(
    *,
    label: str,
    records: Iterable[HistoryRecord],
    value_resolver,
) -> TrendSeries:
    """Compose a TrendSeries from history records + a per-record resolver.

    ``value_resolver(record) -> Optional[float]`` returns the metric
    value for a single record, or ``None`` when the metric is
    unavailable for that record.
    """

    observations: list[TrendObservation] = []
    for record in records:
        value = value_resolver(record)
        evidence_origin = _evidence_origin_from(record)
        observations.append(
            TrendObservation(
                timestamp=record.generated_at_utc,
                value=value,
                record_id=record.record_id,
                evidence_origin=evidence_origin,
            )
        )
    category = _classify_series(observations)
    rolling_3 = _rolling_category(observations, window=3)
    rolling_5 = _rolling_category(observations, window=5)
    detail = _detail_for(observations, category)
    return TrendSeries(
        label=label,
        observations=tuple(observations),
        category=category,
        rolling_3=rolling_3,
        rolling_5=rolling_5,
        window_size=sum(1 for o in observations if o.value is not None),
        detail=detail,
    )


def _detail_for(
    observations: list[TrendObservation], category: TrendCategory
) -> str:
    available = [o for o in observations if o.value is not None]
    if not available:
        return "no available values"
    first = available[0].value
    last = available[-1].value
    return (
        f"first={first} last={last} samples={len(available)} "
        f"category={category.value}"
    )


def _evidence_origin_from(record: HistoryRecord) -> str:
    """Best-effort extraction of ``evidence_origin`` from a record.

    The field exists on replay-review reports and reliability-impact
    bundles (per-row). When neither shape applies, we fall back to
    ``unknown`` rather than guessing.
    """

    payload = record.payload
    origin = payload.get("evidence_origin")
    if isinstance(origin, str):
        return origin
    return "unknown"


# ---------------------------------------------------------------------------
# Public composition.
# ---------------------------------------------------------------------------


def build_trend_report(history: LoadedHistory) -> TrendReport:
    """Compose the full :class:`TrendReport` from a loaded history."""

    report = TrendReport()

    # Replay quality score per replay-review record.
    report.series.append(
        build_series_from_payloads(
            label="replay_quality_score",
            records=history.replay_review,
            value_resolver=_replay_review_score,
        )
    )

    # Aggregate analytics: average quality across the index per
    # analytics report snapshot.
    report.series.append(
        build_series_from_payloads(
            label="analytics_average_score",
            records=history.replay_analytics,
            value_resolver=_analytics_average_score,
        )
    )

    # Coverage % derived from replay-review reports.
    report.series.append(
        build_series_from_payloads(
            label="expected_topics_present_pct",
            records=history.replay_review,
            value_resolver=lambda r: _replay_review_coverage(r, "expected_topics_present_pct"),
        )
    )
    report.series.append(
        build_series_from_payloads(
            label="marker_alignment_pct",
            records=history.replay_review,
            value_resolver=lambda r: _replay_review_coverage(r, "marker_alignment_pct"),
        )
    )

    # Runtime qualification status / counts.
    report.series.append(
        build_series_from_payloads(
            label="runtime_qualification_passed_count",
            records=history.runtime_qualification,
            value_resolver=_qualification_passed_count,
        )
    )

    # Reliability-impact gate-result indicator (1 for passed, 0 for warning,
    # -1 for failed). Captured as a numeric series so the trend logic still
    # applies; volatility flips between values cleanly.
    report.series.append(
        build_series_from_payloads(
            label="gate_status_indicator",
            records=history.reliability_impact,
            value_resolver=_gate_status_indicator,
        )
    )

    return report


def _replay_review_score(record: HistoryRecord) -> Optional[float]:
    """Replay reviews don't embed quality scores directly; the score
    lives on the analytics side. Surface validation pass count as a
    proxy when present, else None."""

    counts = record.payload.get("status_counts") or {}
    if not isinstance(counts, dict):
        return None
    passed = counts.get("passed")
    if isinstance(passed, (int, float)):
        return float(passed)
    return None


def _analytics_average_score(record: HistoryRecord) -> Optional[float]:
    scores = record.payload.get("scores") or []
    if not isinstance(scores, list) or not scores:
        return None
    available = [s.get("score") for s in scores if isinstance(s, dict)]
    available = [v for v in available if isinstance(v, (int, float))]
    if not available:
        return None
    return float(sum(available)) / float(len(available))


def _replay_review_coverage(
    record: HistoryRecord, metric: str
) -> Optional[float]:
    """Replay-review reports don't carry coverage; the field lives on
    the per-incident replay-analytics output. The trend series picks
    up the metric when it is present in the payload, otherwise
    returns None."""

    value = record.payload.get(metric)
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _qualification_passed_count(record: HistoryRecord) -> Optional[float]:
    counts = record.payload.get("status_counts") or {}
    if not isinstance(counts, dict):
        return None
    passed = counts.get("passed")
    if isinstance(passed, (int, float)):
        return float(passed)
    return None


def _gate_status_indicator(record: HistoryRecord) -> Optional[float]:
    gate = record.payload.get("gate_decision") or {}
    status = gate.get("status")
    if status == "passed":
        return 1.0
    if status == "warning":
        return 0.0
    if status == "failed":
        return -1.0
    return None
