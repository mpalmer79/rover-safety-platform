"""Aggregate subsystem risk across reliability-impact bundles.

The aggregator counts how often each subsystem appeared in the
loaded history, tallies the severity distribution of the
reliability risks recorded against it, and ranks the resulting
rows. It never claims causality.

Ranking order: highest repeat-regression count > highest
critical-risk frequency > highest total frequency > alphabetical.
"""

from __future__ import annotations

from collections import Counter
from typing import Iterable

from app.programme_review.models import (
    HistoryRecord,
    LoadedHistory,
    SubsystemRiskReport,
    SubsystemRiskRow,
)


def aggregate_subsystem_risk(history: LoadedHistory) -> SubsystemRiskReport:
    """Walk every reliability-impact bundle and tally per-subsystem risk."""

    if not history.reliability_impact:
        return SubsystemRiskReport(
            rows=[],
            notes=("no reliability-impact bundles in history",),
        )

    frequency: Counter[str] = Counter()
    severity_per_subsystem: dict[str, Counter[str]] = {}
    repeat_regressions: Counter[str] = Counter()
    gate_failure_counts: Counter[str] = Counter()
    unresolved_warning_counts: Counter[str] = Counter()
    representative_artifacts: dict[str, list[str]] = {}

    for record in history.reliability_impact:
        payload = record.payload
        gate_status = payload.get("gate_decision", {}).get("status", "")
        assessment_risks = payload.get("assessment", {}).get("risks", [])
        impacted_subsystems = {
            entry.get("subsystem", "unknown")
            for entry in payload.get("subsystem_impacts", [])
            if isinstance(entry, dict)
        }
        for subsystem in impacted_subsystems:
            if not isinstance(subsystem, str):
                continue
            frequency[subsystem] += 1
            severity_counter = severity_per_subsystem.setdefault(
                subsystem, Counter()
            )
            for risk in assessment_risks:
                if not isinstance(risk, dict):
                    continue
                level = risk.get("level", "none")
                severity_counter[level] += 1
                if level in {"high", "critical"}:
                    repeat_regressions[subsystem] += 1
                if level in {"moderate", "high", "critical"}:
                    unresolved_warning_counts[subsystem] += 1
            if gate_status == "failed":
                gate_failure_counts[subsystem] += 1
            representative_artifacts.setdefault(subsystem, []).append(
                str(record.source_path)
            )

    rows: list[SubsystemRiskRow] = []
    for subsystem, count in frequency.items():
        severity_dist = dict(severity_per_subsystem.get(subsystem, Counter()))
        rows.append(
            SubsystemRiskRow(
                subsystem=subsystem,
                frequency=count,
                severity_distribution=severity_dist,
                repeat_regression_count=repeat_regressions.get(subsystem, 0),
                gate_failure_count=gate_failure_counts.get(subsystem, 0),
                unresolved_warning_count=unresolved_warning_counts.get(
                    subsystem, 0
                ),
                representative_artifacts=tuple(
                    representative_artifacts.get(subsystem, [])[:3]
                ),
            )
        )
    rows.sort(
        key=lambda r: (
            -r.repeat_regression_count,
            -_severity_score(r.severity_distribution),
            -r.frequency,
            r.subsystem,
        )
    )
    notes: tuple[str, ...] = ()
    if not rows:
        notes = (
            "no subsystem impacts found in the loaded reliability-impact bundles",
        )
    return SubsystemRiskReport(rows=rows, notes=notes)


def _severity_score(distribution: dict[str, int]) -> int:
    weights = {
        "none": 0,
        "low": 1,
        "moderate": 2,
        "high": 5,
        "critical": 10,
    }
    return sum(
        weights.get(level, 0) * count for level, count in distribution.items()
    )
