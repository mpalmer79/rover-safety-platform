"""Analytics delta engine.

Compares the current ``replay-quality-index.json`` and
``replay-analytics-report.json`` against a pinned baseline. Each
delta becomes an :class:`AnalyticsDeltaEntry`; severities follow
the documented rules:

* score drop ≥ 10 -> warning;
* score drop ≥ 25 -> regression;
* score crossing below 40 (baseline ≥ 40) -> critical_regression;
* new contradiction -> critical_regression;
* static-only labelled as bag-backed (honesty violation) -> critical_regression;
* missing-bag promoted to bag-backed without metadata -> critical_regression;
* missing live runtime evidence in current run, when baseline also lacked
  it, is not a regression.

A missing baseline is a warning, never a failure.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from app.reliability_impact.baseline import load_baseline_payload
from app.reliability_impact.models import (
    AnalyticsDeltaEntry,
    BaselineReference,
    DeltaSeverity,
    ReplayAnalyticsDelta,
)


def compute_analytics_delta(
    *,
    current_quality_index: Optional[Path] = None,
    current_analytics_report: Optional[Path] = None,
    baseline: BaselineReference,
) -> ReplayAnalyticsDelta:
    """Compute the cross-incident delta against the supplied baseline."""

    current_quality = _load(current_quality_index)
    current_analytics = _load(current_analytics_report)
    baseline_quality = load_baseline_payload(baseline.quality_index_path)
    baseline_analytics = load_baseline_payload(baseline.analytics_report_path)

    delta = ReplayAnalyticsDelta(
        baseline_path=baseline.quality_index_path,
        current_path=current_quality_index,
    )

    if current_quality is None:
        delta.warnings.append(
            "current replay-quality-index.json not supplied or unreadable"
        )
    if baseline_quality is None:
        delta.warnings.append(
            "baseline replay-quality-index.baseline.json not present; "
            "delta limited to current snapshot"
        )
    if baseline_analytics is None and current_analytics is not None:
        delta.warnings.append(
            "baseline analytics-report not present"
        )

    if current_quality and baseline_quality:
        delta.entries.extend(
            _diff_quality_indices(current_quality, baseline_quality)
        )
    elif current_quality and not baseline_quality:
        delta.entries.append(
            AnalyticsDeltaEntry(
                label="baseline_missing",
                category="baseline",
                severity=DeltaSeverity.WARNING,
                detail=(
                    "no baseline replay-quality-index available; the gate "
                    "treats this as a warning, not a failure"
                ),
            )
        )

    if current_analytics and baseline_analytics:
        delta.entries.extend(
            _diff_analytics_reports(current_analytics, baseline_analytics)
        )

    return delta


def _diff_quality_indices(
    current: dict, baseline: dict
) -> list[AnalyticsDeltaEntry]:
    """Per-incident comparisons from the quality index."""

    current_rows = {r.get("incident_id"): r for r in current.get("rows", [])}
    baseline_rows = {r.get("incident_id"): r for r in baseline.get("rows", [])}
    entries: list[AnalyticsDeltaEntry] = []

    for incident_id in sorted(baseline_rows.keys() - current_rows.keys()):
        entries.append(
            AnalyticsDeltaEntry(
                label="incident_removed",
                category="incident_count",
                severity=DeltaSeverity.REGRESSION,
                detail=(
                    f"incident {incident_id!r} was in the baseline but "
                    "is absent from the current run"
                ),
                baseline_value=baseline_rows[incident_id],
                current_value=None,
                incident_id=incident_id,
            )
        )

    for incident_id in sorted(current_rows.keys() - baseline_rows.keys()):
        entries.append(
            AnalyticsDeltaEntry(
                label="incident_added",
                category="incident_count",
                severity=DeltaSeverity.NEUTRAL,
                detail=f"new incident {incident_id!r} added since baseline",
                baseline_value=None,
                current_value=current_rows[incident_id],
                incident_id=incident_id,
            )
        )

    for incident_id in sorted(current_rows.keys() & baseline_rows.keys()):
        c = current_rows[incident_id]
        b = baseline_rows[incident_id]
        entries.extend(_diff_per_incident(incident_id, current=c, baseline=b))

    return entries


def _diff_per_incident(
    incident_id: str, *, current: dict, baseline: dict
) -> list[AnalyticsDeltaEntry]:
    entries: list[AnalyticsDeltaEntry] = []
    c_score = int(current.get("score", 0))
    b_score = int(baseline.get("score", 0))
    score_delta = c_score - b_score
    if score_delta != 0:
        severity = _score_severity(b_score=b_score, c_score=c_score)
        if severity != DeltaSeverity.NEUTRAL:
            entries.append(
                AnalyticsDeltaEntry(
                    label=f"quality_score[{incident_id}]",
                    category="score",
                    severity=severity,
                    detail=(
                        f"quality score moved {b_score:+d} -> {c_score:+d} "
                        f"(delta {score_delta:+d})"
                    ),
                    baseline_value=b_score,
                    current_value=c_score,
                    incident_id=incident_id,
                )
            )

    c_coverage = current.get("coverage_status", "")
    b_coverage = baseline.get("coverage_status", "")
    if c_coverage != b_coverage:
        severity = _coverage_severity(b_coverage, c_coverage)
        entries.append(
            AnalyticsDeltaEntry(
                label=f"coverage_status[{incident_id}]",
                category="coverage",
                severity=severity,
                detail=(
                    f"coverage status moved {b_coverage!r} -> {c_coverage!r}"
                ),
                baseline_value=b_coverage,
                current_value=c_coverage,
                incident_id=incident_id,
            )
        )

    c_bag = current.get("bag_status", "")
    b_bag = baseline.get("bag_status", "")
    if c_bag != b_bag:
        severity = _bag_severity(b_bag, c_bag)
        entries.append(
            AnalyticsDeltaEntry(
                label=f"bag_status[{incident_id}]",
                category="bag",
                severity=severity,
                detail=f"bag status moved {b_bag!r} -> {c_bag!r}",
                baseline_value=b_bag,
                current_value=c_bag,
                incident_id=incident_id,
            )
        )

    c_origin = current.get("evidence_origin", "")
    b_origin = baseline.get("evidence_origin", "")
    if c_origin != b_origin:
        severity = _origin_severity(b_origin, c_origin, c_bag, b_bag)
        entries.append(
            AnalyticsDeltaEntry(
                label=f"evidence_origin[{incident_id}]",
                category="honesty",
                severity=severity,
                detail=(
                    f"evidence_origin moved {b_origin!r} -> {c_origin!r}"
                ),
                baseline_value=b_origin,
                current_value=c_origin,
                incident_id=incident_id,
            )
        )

    return entries


def _diff_analytics_reports(
    current: dict, baseline: dict
) -> list[AnalyticsDeltaEntry]:
    """Aggregate-level deltas from replay-analytics-report.json."""

    entries: list[AnalyticsDeltaEntry] = []

    c_incidents = int(current.get("incident_count", 0))
    b_incidents = int(baseline.get("incident_count", 0))
    if c_incidents != b_incidents:
        severity = (
            DeltaSeverity.NEUTRAL
            if c_incidents > b_incidents
            else DeltaSeverity.REGRESSION
        )
        entries.append(
            AnalyticsDeltaEntry(
                label="incident_count_aggregate",
                category="incident_count",
                severity=severity,
                detail=(
                    f"aggregate incident count moved {b_incidents} -> {c_incidents}"
                ),
                baseline_value=b_incidents,
                current_value=c_incidents,
            )
        )

    c_scores = {s.get("incident_id"): s for s in current.get("scores", [])}
    b_scores = {s.get("incident_id"): s for s in baseline.get("scores", [])}
    new_contradictions: list[str] = []
    for incident_id, c_score in c_scores.items():
        b_score = b_scores.get(incident_id, {})
        c_gaps = c_score.get("blocking_gaps") or []
        b_gaps = b_score.get("blocking_gaps") or []
        c_contras = sum(1 for g in c_gaps if "contradictions" in str(g))
        b_contras = sum(1 for g in b_gaps if "contradictions" in str(g))
        if c_contras > b_contras:
            new_contradictions.append(incident_id)
            entries.append(
                AnalyticsDeltaEntry(
                    label=f"new_contradiction[{incident_id}]",
                    category="contradiction",
                    severity=DeltaSeverity.CRITICAL_REGRESSION,
                    detail=(
                        f"incident {incident_id!r} introduced a "
                        "contradiction not present in the baseline"
                    ),
                    baseline_value=b_contras,
                    current_value=c_contras,
                    incident_id=incident_id,
                )
            )

    return entries


# ---------------------------------------------------------------------------
# Severity classifiers.
# ---------------------------------------------------------------------------


def _score_severity(*, b_score: int, c_score: int) -> DeltaSeverity:
    delta = b_score - c_score
    if delta <= 0:
        return DeltaSeverity.IMPROVEMENT if delta < 0 else DeltaSeverity.NEUTRAL
    # Score crossed below 40 from a higher band.
    if b_score >= 40 and c_score < 40:
        return DeltaSeverity.CRITICAL_REGRESSION
    if delta >= 25:
        return DeltaSeverity.REGRESSION
    if delta >= 10:
        return DeltaSeverity.WARNING
    return DeltaSeverity.NEUTRAL


_COVERAGE_ORDER: dict[str, int] = {
    "missing": 0,
    "sparse": 1,
    "partial": 2,
    "substantial": 3,
    "complete": 4,
}


def _coverage_severity(b: str, c: str) -> DeltaSeverity:
    b_rank = _COVERAGE_ORDER.get(b, 0)
    c_rank = _COVERAGE_ORDER.get(c, 0)
    if c_rank > b_rank:
        return DeltaSeverity.IMPROVEMENT
    if c_rank == b_rank:
        return DeltaSeverity.NEUTRAL
    drop = b_rank - c_rank
    if drop >= 2:
        return DeltaSeverity.REGRESSION
    return DeltaSeverity.WARNING


_BAG_ORDER: dict[str, int] = {
    "missing_bag": 0,
    "static_only": 0,
    "not_executed": 0,
    "failed": 0,
    "partial": 1,
    "ready": 2,
    "passed": 2,
}


def _bag_severity(b: str, c: str) -> DeltaSeverity:
    b_rank = _BAG_ORDER.get(b, 0)
    c_rank = _BAG_ORDER.get(c, 0)
    if b == "ready" and c == "missing_bag":
        return DeltaSeverity.CRITICAL_REGRESSION
    if c_rank > b_rank:
        return DeltaSeverity.IMPROVEMENT
    if c_rank == b_rank:
        return DeltaSeverity.NEUTRAL
    return DeltaSeverity.REGRESSION


def _origin_severity(
    b_origin: str, c_origin: str, c_bag: str, b_bag: str
) -> DeltaSeverity:
    # Honesty violations:
    if (
        c_origin == "bag-backed"
        and c_bag in {"missing_bag", "static_only"}
    ):
        return DeltaSeverity.CRITICAL_REGRESSION
    # Static-only declared as live-runtime in the current run when the
    # baseline was scenario-evidence.
    if b_origin == "scenario-evidence" and c_origin == "live-runtime" and c_bag in {
        "missing_bag",
        "static_only",
    }:
        return DeltaSeverity.CRITICAL_REGRESSION
    # Normal progression (scenario-evidence -> bag-backed when bag arrived) is an improvement.
    if b_origin in {"scenario-evidence", "unknown"} and c_origin == "bag-backed" and c_bag in {"ready", "partial"}:
        return DeltaSeverity.IMPROVEMENT
    # bag-backed -> scenario-evidence is a regression.
    if b_origin == "bag-backed" and c_origin != "bag-backed":
        return DeltaSeverity.REGRESSION
    return DeltaSeverity.NEUTRAL


def _load(path: Optional[Path]) -> Optional[dict]:
    if path is None:
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
