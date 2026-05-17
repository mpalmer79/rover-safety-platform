"""Programme health: drift, freshness, governance, trends."""

from __future__ import annotations

from app.programme_review.aggregation import build_programme_review
from app.programme_review.coverage_evolution import build_coverage_evolution
from app.programme_review.drift_detection import detect_drift
from app.programme_review.freshness import assess_freshness
from app.programme_review.gate_history import build_gate_history
from app.programme_review.governance_health import assess_governance_health
from app.programme_review.history_loader import load_history
from app.programme_review.models import (
    DriftSeverity,
    FreshnessStatus,
    GateVolatility,
    GovernanceHealth,
    PROGRAMME_CERTIFICATION_DISCLAIMER,
    ProgrammeReview,
    TrendCategory,
)
from app.programme_review.reporting import (
    render_drift_md,
    render_freshness_md,
    render_health_md,
    render_trend_md,
    write_programme_review_bundle,
)
from app.programme_review.subsystem_risk import aggregate_subsystem_risk
from app.programme_review.trend_analysis import build_trend_report

__all__ = [
    "DriftSeverity",
    "FreshnessStatus",
    "GateVolatility",
    "GovernanceHealth",
    "PROGRAMME_CERTIFICATION_DISCLAIMER",
    "ProgrammeReview",
    "TrendCategory",
    "aggregate_subsystem_risk",
    "assess_freshness",
    "assess_governance_health",
    "build_coverage_evolution",
    "build_gate_history",
    "build_programme_review",
    "build_trend_report",
    "detect_drift",
    "load_history",
    "render_drift_md",
    "render_freshness_md",
    "render_health_md",
    "render_trend_md",
    "write_programme_review_bundle",
]
