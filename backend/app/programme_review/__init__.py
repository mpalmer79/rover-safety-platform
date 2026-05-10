"""Phase 10 programme-review package.

Read-only longitudinal governance layer over Phase 3..9 artefacts.
The package never invents history, never claims causality, never
auto-updates baselines, and never fails CI for missing live
runtime evidence. Tests run without ROS, Gazebo, Foxglove, or
network access.
"""

from app.programme_review.aggregation import build_programme_review
from app.programme_review.coverage_evolution import build_coverage_evolution
from app.programme_review.dashboard import build_dashboard
from app.programme_review.drift_detection import detect_drift
from app.programme_review.freshness import assess_freshness
from app.programme_review.gate_history import build_gate_history
from app.programme_review.governance_health import assess_governance_health
from app.programme_review.history_loader import (
    DEFAULT_INCIDENTS_ROOT,
    DEFAULT_RELIABILITY_IMPACT_ROOTS,
    DEFAULT_REPLAY_ANALYTICS_PATH,
    DEFAULT_REPLAY_ANALYTICS_QUALITY_PATH,
    DEFAULT_RUNTIME_EVIDENCE_ROOT,
    load_history,
)
from app.programme_review.models import (
    CoverageEvolutionEntry,
    CoverageEvolutionReport,
    DEFAULT_KNOWN_LIMITATIONS,
    DisciplineCategory,
    DisciplineRating,
    DisciplineResult,
    DriftFinding,
    DriftReport,
    DriftSeverity,
    FreshnessEntry,
    FreshnessReport,
    FreshnessStatus,
    GateHistoryReport,
    GateVolatility,
    GovernanceHealth,
    GovernanceHealthReport,
    HistoryRecord,
    LoadedHistory,
    PROGRAMME_CERTIFICATION_DISCLAIMER,
    ProgrammeReview,
    SubsystemRiskReport,
    SubsystemRiskRow,
    TrendCategory,
    TrendObservation,
    TrendReport,
    TrendSeries,
)
from app.programme_review.reporting import (
    render_coverage_evolution_md,
    render_drift_md,
    render_freshness_md,
    render_gate_history_md,
    render_health_md,
    render_programme_review_md,
    render_subsystem_risk_md,
    render_trend_md,
    write_programme_review_bundle,
)
from app.programme_review.subsystem_risk import aggregate_subsystem_risk
from app.programme_review.trend_analysis import (
    build_series_from_payloads,
    build_trend_report,
)

__all__ = [
    "CoverageEvolutionEntry",
    "CoverageEvolutionReport",
    "DEFAULT_INCIDENTS_ROOT",
    "DEFAULT_KNOWN_LIMITATIONS",
    "DEFAULT_RELIABILITY_IMPACT_ROOTS",
    "DEFAULT_REPLAY_ANALYTICS_PATH",
    "DEFAULT_REPLAY_ANALYTICS_QUALITY_PATH",
    "DEFAULT_RUNTIME_EVIDENCE_ROOT",
    "DisciplineCategory",
    "DisciplineRating",
    "DisciplineResult",
    "DriftFinding",
    "DriftReport",
    "DriftSeverity",
    "FreshnessEntry",
    "FreshnessReport",
    "FreshnessStatus",
    "GateHistoryReport",
    "GateVolatility",
    "GovernanceHealth",
    "GovernanceHealthReport",
    "HistoryRecord",
    "LoadedHistory",
    "PROGRAMME_CERTIFICATION_DISCLAIMER",
    "ProgrammeReview",
    "SubsystemRiskReport",
    "SubsystemRiskRow",
    "TrendCategory",
    "TrendObservation",
    "TrendReport",
    "TrendSeries",
    "aggregate_subsystem_risk",
    "assess_freshness",
    "assess_governance_health",
    "build_coverage_evolution",
    "build_dashboard",
    "build_gate_history",
    "build_programme_review",
    "build_series_from_payloads",
    "build_trend_report",
    "detect_drift",
    "load_history",
    "render_coverage_evolution_md",
    "render_drift_md",
    "render_freshness_md",
    "render_gate_history_md",
    "render_health_md",
    "render_programme_review_md",
    "render_subsystem_risk_md",
    "render_trend_md",
    "write_programme_review_bundle",
]
