"""Aggregation: wire every sub-module into a single :class:`ProgrammeReview`."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

from app.programme_review.coverage_evolution import build_coverage_evolution
from app.programme_review.drift_detection import detect_drift
from app.programme_review.freshness import assess_freshness
from app.programme_review.gate_history import build_gate_history
from app.programme_review.governance_health import assess_governance_health
from app.programme_review.history_loader import load_history
from app.programme_review.models import (
    DEFAULT_KNOWN_LIMITATIONS,
    LoadedHistory,
    ProgrammeReview,
)
from app.programme_review.subsystem_risk import aggregate_subsystem_risk
from app.programme_review.trend_analysis import build_trend_report


def build_programme_review(
    *,
    reliability_impact_roots: Optional[Iterable[Path]] = None,
    replay_analytics_paths: Optional[Iterable[Path]] = None,
    runtime_evidence_root: Optional[Path] = None,
    incidents_root: Optional[Path] = None,
    reference_time_utc: Optional[datetime] = None,
    freshness_thresholds_seconds: Optional[dict[str, int]] = None,
    fixture_mode: bool = False,
    history: Optional[LoadedHistory] = None,
) -> ProgrammeReview:
    """Compose the full programme review.

    ``reference_time_utc`` controls freshness checks; tests supply a
    fixture time, CI passes ``datetime.now(tz=timezone.utc)``. When
    omitted the function uses the current UTC time, which is fine
    for human-driven runs but should not be used in tests.
    """

    history = history or load_history(
        reliability_impact_roots=reliability_impact_roots,
        replay_analytics_paths=replay_analytics_paths,
        runtime_evidence_root=runtime_evidence_root,
        incidents_root=incidents_root,
    )

    trend_report = build_trend_report(history)
    drift_report = detect_drift(history=history, trend_report=trend_report)
    governance = assess_governance_health(
        history=history, drift_report=drift_report
    )
    reference_time = reference_time_utc or datetime.now(tz=timezone.utc)
    freshness_report = assess_freshness(
        history=history,
        reference_time_utc=reference_time,
        thresholds_seconds=freshness_thresholds_seconds,
    )
    subsystem_risk = aggregate_subsystem_risk(history)
    coverage_evolution = build_coverage_evolution(history)
    gate_history = build_gate_history(history)

    generated_at = (
        reference_time_utc.isoformat(timespec="seconds")
        if reference_time_utc is not None
        else datetime.now(tz=timezone.utc).isoformat(timespec="seconds")
    )
    return ProgrammeReview(
        generated_at_utc=generated_at,
        history_counts=history.counts(),
        trend_report=trend_report,
        drift_report=drift_report,
        governance_health=governance,
        freshness_report=freshness_report,
        subsystem_risk_report=subsystem_risk,
        coverage_evolution=coverage_evolution,
        gate_history=gate_history,
        warnings=tuple(history.warnings),
        known_limitations=DEFAULT_KNOWN_LIMITATIONS,
        fixture_mode=fixture_mode,
    )
