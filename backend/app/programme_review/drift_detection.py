"""Deterministic drift detection.

The detectors take a :class:`LoadedHistory` + the corresponding
:class:`TrendReport` and emit :class:`DriftFinding` instances with
documented severities. Rules are intentionally conservative:

* ``replay score critical`` — the analytics_average_score series
  degraded by ≥ 25 points;
* ``replay score regression`` — degraded by ≥ 10 points;
* ``increasing missing_bag frequency`` — at least one extra incident
  reports ``bag_status=missing_bag`` compared with the baseline run;
* ``increasing static_only dependency`` — same rule for ``static_only``;
* ``growing unknown file count`` — reliability-impact bundles report
  more unknown files in the most recent run than in the oldest;
* ``declining requirement coverage`` — fewer mapped requirement
  ids in the most recent reliability-impact bundle than in the oldest;
* ``replay validation instability`` — replay_validation_pass_rate
  exhibits volatile trend behaviour;
* ``CI gate volatility`` — gate_status_indicator series is volatile.

Insufficient history degrades every detector to ``informational``.
"""

from __future__ import annotations

from typing import Iterable

from app.programme_review.models import (
    DriftFinding,
    DriftReport,
    DriftSeverity,
    HistoryRecord,
    LoadedHistory,
    TrendCategory,
    TrendReport,
)


_SCORE_DROP_REGRESSION = 10.0
_SCORE_DROP_CRITICAL = 25.0


def detect_drift(
    *,
    history: LoadedHistory,
    trend_report: TrendReport,
) -> DriftReport:
    """Run every documented detector and return findings."""

    findings: list[DriftFinding] = []

    findings.extend(_score_drift(trend_report))
    findings.extend(_bag_status_drift(history))
    findings.extend(_static_only_drift(history))
    findings.extend(_unknown_file_drift(history))
    findings.extend(_requirement_coverage_drift(history))
    findings.extend(_validation_instability(trend_report))
    findings.extend(_gate_volatility(trend_report))

    return DriftReport(findings=findings)


# ---------------------------------------------------------------------------
# Individual detectors.
# ---------------------------------------------------------------------------


def _score_drift(trend_report: TrendReport) -> list[DriftFinding]:
    out: list[DriftFinding] = []
    series = next(
        (s for s in trend_report.series if s.label == "analytics_average_score"),
        None,
    )
    if series is None:
        return out
    values = [o.value for o in series.observations if o.value is not None]
    if len(values) < 2:
        out.append(
            DriftFinding(
                label="analytics_score_drift",
                severity=DriftSeverity.INFORMATIONAL,
                detail="insufficient analytics history for score drift",
            )
        )
        return out
    delta = values[-1] - values[0]
    if delta <= -_SCORE_DROP_CRITICAL:
        out.append(
            DriftFinding(
                label="analytics_score_critical_drop",
                severity=DriftSeverity.CRITICAL_REGRESSION,
                detail=(
                    f"analytics average score moved {values[0]:.1f} -> "
                    f"{values[-1]:.1f} (Δ={delta:.1f}); below -25 critical "
                    "threshold"
                ),
            )
        )
    elif delta <= -_SCORE_DROP_REGRESSION:
        out.append(
            DriftFinding(
                label="analytics_score_regression",
                severity=DriftSeverity.REGRESSION,
                detail=(
                    f"analytics average score moved {values[0]:.1f} -> "
                    f"{values[-1]:.1f} (Δ={delta:.1f}); below -10 regression "
                    "threshold"
                ),
            )
        )
    elif series.category == TrendCategory.VOLATILE:
        out.append(
            DriftFinding(
                label="analytics_score_volatile",
                severity=DriftSeverity.WARNING,
                detail="analytics average score exhibits volatile behaviour",
            )
        )
    return out


def _bag_status_drift(history: LoadedHistory) -> list[DriftFinding]:
    counts = _bag_status_counts(history.replay_review)
    if len(counts) < 2:
        return [
            DriftFinding(
                label="bag_status_history",
                severity=DriftSeverity.INFORMATIONAL,
                detail="insufficient replay-review history for bag-status drift",
            )
        ]
    earliest = counts[0]
    latest = counts[-1]
    missing_delta = latest.get("missing_bag", 0) - earliest.get("missing_bag", 0)
    out: list[DriftFinding] = []
    if missing_delta > 0:
        out.append(
            DriftFinding(
                label="missing_bag_frequency_increasing",
                severity=DriftSeverity.WARNING,
                detail=(
                    f"missing_bag count moved "
                    f"{earliest.get('missing_bag', 0)} -> "
                    f"{latest.get('missing_bag', 0)}"
                ),
            )
        )
    return out


def _static_only_drift(history: LoadedHistory) -> list[DriftFinding]:
    counts = _bag_status_counts(history.replay_review)
    if len(counts) < 2:
        return []
    earliest = counts[0]
    latest = counts[-1]
    delta = latest.get("static_only", 0) - earliest.get("static_only", 0)
    if delta > 0:
        return [
            DriftFinding(
                label="static_only_dependency_increasing",
                severity=DriftSeverity.WARNING,
                detail=(
                    f"static_only count moved {earliest.get('static_only', 0)} "
                    f"-> {latest.get('static_only', 0)}"
                ),
            )
        ]
    return []


def _unknown_file_drift(history: LoadedHistory) -> list[DriftFinding]:
    counts: list[int] = []
    for record in history.reliability_impact:
        files = record.payload.get("source_change", {}).get("changed_files", [])
        if not isinstance(files, list):
            continue
        counts.append(
            sum(1 for f in files if isinstance(f, dict) and f.get("subsystem") == "unknown")
        )
    if len(counts) < 2:
        return []
    delta = counts[-1] - counts[0]
    if delta >= 3:
        return [
            DriftFinding(
                label="unknown_file_count_growing",
                severity=DriftSeverity.REGRESSION,
                detail=(
                    f"unknown-file count moved {counts[0]} -> {counts[-1]} "
                    f"(Δ={delta}); the classifier prefix table likely needs an update"
                ),
            )
        ]
    if delta > 0:
        return [
            DriftFinding(
                label="unknown_file_count_increasing",
                severity=DriftSeverity.WARNING,
                detail=(
                    f"unknown-file count moved {counts[0]} -> {counts[-1]}"
                ),
            )
        ]
    return []


def _requirement_coverage_drift(history: LoadedHistory) -> list[DriftFinding]:
    counts: list[int] = []
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
        counts.append(len(ids))
    if len(counts) < 2:
        return []
    delta = counts[-1] - counts[0]
    if delta < 0:
        return [
            DriftFinding(
                label="requirement_coverage_declining",
                severity=DriftSeverity.WARNING,
                detail=(
                    f"mapped requirement count moved {counts[0]} -> {counts[-1]} "
                    f"(Δ={delta})"
                ),
            )
        ]
    return []


def _validation_instability(trend_report: TrendReport) -> list[DriftFinding]:
    series = next(
        (
            s
            for s in trend_report.series
            if s.label
            in {"runtime_qualification_passed_count", "replay_quality_score"}
        ),
        None,
    )
    if series is None:
        return []
    if series.category == TrendCategory.VOLATILE:
        return [
            DriftFinding(
                label="validation_instability",
                severity=DriftSeverity.WARNING,
                detail=(
                    f"{series.label} series is volatile; consider stabilising "
                    "the underlying check"
                ),
            )
        ]
    return []


def _gate_volatility(trend_report: TrendReport) -> list[DriftFinding]:
    series = next(
        (s for s in trend_report.series if s.label == "gate_status_indicator"),
        None,
    )
    if series is None:
        return []
    if series.category == TrendCategory.VOLATILE:
        return [
            DriftFinding(
                label="ci_gate_volatile",
                severity=DriftSeverity.WARNING,
                detail="CI gate status oscillates between pass / warning / failed",
            )
        ]
    if series.category == TrendCategory.DEGRADING:
        return [
            DriftFinding(
                label="ci_gate_degrading",
                severity=DriftSeverity.REGRESSION,
                detail="CI gate trend is degrading over the recorded window",
            )
        ]
    return []


# ---------------------------------------------------------------------------
# Shared helpers.
# ---------------------------------------------------------------------------


def _bag_status_counts(
    records: Iterable[HistoryRecord],
) -> list[dict[str, int]]:
    """Per-record count of `bag_status` values across the replay-review
    report payload.

    Replay-review reports record the per-incident bag_status; for
    drift we count the bag-status of each report (one report = one
    incident in the canonical layout).
    """

    out: list[dict[str, int]] = []
    for record in records:
        status = record.payload.get("bag_status")
        if not isinstance(status, str):
            continue
        out.append({status: 1})
    # Roll into cumulative counts so per-record entries reflect the
    # state of the world *at* that point in history rather than the
    # singleton record.
    rolling: dict[str, int] = {}
    cumulative: list[dict[str, int]] = []
    for entry in out:
        for key, value in entry.items():
            rolling[key] = rolling.get(key, 0) + value
        cumulative.append(dict(rolling))
    return cumulative
