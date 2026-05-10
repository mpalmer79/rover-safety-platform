"""Typed models for the Phase 10 programme-review layer.

The layer is **read-only** with respect to every upstream artefact
it consumes (reliability-impact bundles, replay analytics, runtime
qualification reports, replay review reports, incident reports).
Aggregation is deterministic; the layer never invents history,
never claims causality, and never auto-updates baselines.

Status vocabularies and honesty rules preserve prior phases:

* missing history is ``insufficient_history`` (trends) or
  ``unknown`` (freshness / gate volatility), **not** regression;
* static-only evidence stays static-only across aggregation;
* mixed-origin samples are explicitly labelled;
* the gate failure surface is reserved for documented critical
  governance conditions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Optional


# ---------------------------------------------------------------------------
# Controlled enums.
# ---------------------------------------------------------------------------


class TrendCategory(str, Enum):
    """Classification emitted by the trend analyser."""

    IMPROVING = "improving"
    STABLE = "stable"
    DEGRADING = "degrading"
    VOLATILE = "volatile"
    INSUFFICIENT_HISTORY = "insufficient_history"


class DriftSeverity(str, Enum):
    """Drift-detection severity (matches prior phases)."""

    INFORMATIONAL = "informational"
    WARNING = "warning"
    REGRESSION = "regression"
    CRITICAL_REGRESSION = "critical_regression"


class GovernanceHealth(str, Enum):
    """Programme-level operational posture."""

    STRONG = "strong"
    ACCEPTABLE = "acceptable"
    WEAK = "weak"
    CONCERNING = "concerning"
    CRITICAL = "critical"


class DisciplineCategory(str, Enum):
    """Per-category discipline buckets."""

    EVIDENCE = "evidence"
    REPLAY = "replay"
    CI = "ci"
    TRACEABILITY = "traceability"
    RUNTIME_QUALIFICATION = "runtime_qualification"
    REVIEW_COMPLETION = "review_completion"


class DisciplineRating(str, Enum):
    """Per-discipline rating."""

    STRONG = "strong"
    ACCEPTABLE = "acceptable"
    WEAK = "weak"
    CONCERNING = "concerning"
    UNKNOWN = "unknown"


class FreshnessStatus(str, Enum):
    """Per-artefact freshness status."""

    FRESH = "fresh"
    STALE = "stale"
    UNKNOWN = "unknown"


class GateVolatility(str, Enum):
    """CI gate trend volatility label."""

    STEADY = "steady"
    OSCILLATING = "oscillating"
    REGRESSING = "regressing"
    IMPROVING = "improving"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Loader records (no upstream import dependency).
# ---------------------------------------------------------------------------


@dataclass
class HistoryRecord:
    """One loaded artefact with its source category + timestamps."""

    record_type: str
    """Category label (``reliability_impact``, ``replay_analytics``,
    ``runtime_qualification``, ``replay_review``, ``incident``)."""

    source_path: Path
    payload: dict
    generated_at_utc: str = ""
    record_id: str = ""
    """Best-effort stable id (``incident_id`` / ``run_id`` / file name)."""

    notes: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {
            "record_type": self.record_type,
            "source_path": str(self.source_path),
            "record_id": self.record_id,
            "generated_at_utc": self.generated_at_utc,
            "notes": list(self.notes),
        }


@dataclass
class LoadedHistory:
    """A complete loaded history for one programme review run."""

    reliability_impact: list[HistoryRecord] = field(default_factory=list)
    replay_analytics: list[HistoryRecord] = field(default_factory=list)
    runtime_qualification: list[HistoryRecord] = field(default_factory=list)
    replay_review: list[HistoryRecord] = field(default_factory=list)
    incident: list[HistoryRecord] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    """Structured warnings; never raised exceptions."""

    def all_records(self) -> list[HistoryRecord]:
        return (
            list(self.reliability_impact)
            + list(self.replay_analytics)
            + list(self.runtime_qualification)
            + list(self.replay_review)
            + list(self.incident)
        )

    def counts(self) -> dict[str, int]:
        return {
            "reliability_impact": len(self.reliability_impact),
            "replay_analytics": len(self.replay_analytics),
            "runtime_qualification": len(self.runtime_qualification),
            "replay_review": len(self.replay_review),
            "incident": len(self.incident),
        }

    def as_dict(self) -> dict:
        return {
            "counts": self.counts(),
            "reliability_impact": [r.as_dict() for r in self.reliability_impact],
            "replay_analytics": [r.as_dict() for r in self.replay_analytics],
            "runtime_qualification": [
                r.as_dict() for r in self.runtime_qualification
            ],
            "replay_review": [r.as_dict() for r in self.replay_review],
            "incident": [r.as_dict() for r in self.incident],
            "warnings": list(self.warnings),
        }


# ---------------------------------------------------------------------------
# Trend + drift.
# ---------------------------------------------------------------------------


@dataclass
class TrendObservation:
    """One observation in a trend series."""

    timestamp: str
    value: Optional[float]
    """``None`` when the underlying metric was unavailable for this
    record (the analyser treats unavailable values conservatively)."""

    record_id: str = ""
    evidence_origin: str = ""

    def as_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "value": self.value,
            "record_id": self.record_id,
            "evidence_origin": self.evidence_origin,
        }


@dataclass
class TrendSeries:
    """A named trend series + its classification."""

    label: str
    observations: tuple[TrendObservation, ...]
    category: TrendCategory
    detail: str = ""
    window_size: int = 0
    """Number of observations the classifier considered."""

    rolling_3: TrendCategory = TrendCategory.INSUFFICIENT_HISTORY
    rolling_5: TrendCategory = TrendCategory.INSUFFICIENT_HISTORY

    def as_dict(self) -> dict:
        return {
            "label": self.label,
            "category": self.category.value,
            "rolling_3": self.rolling_3.value,
            "rolling_5": self.rolling_5.value,
            "window_size": self.window_size,
            "detail": self.detail,
            "observations": [o.as_dict() for o in self.observations],
        }


@dataclass
class TrendReport:
    """Aggregate of every tracked trend."""

    series: list[TrendSeries] = field(default_factory=list)
    notes: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {
            "series": [s.as_dict() for s in self.series],
            "notes": list(self.notes),
        }


@dataclass
class DriftFinding:
    """One drift detection."""

    label: str
    severity: DriftSeverity
    detail: str
    evidence_paths: tuple[str, ...] = ()
    affected_subsystems: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {
            "label": self.label,
            "severity": self.severity.value,
            "detail": self.detail,
            "evidence_paths": list(self.evidence_paths),
            "affected_subsystems": list(self.affected_subsystems),
        }


@dataclass
class DriftReport:
    findings: list[DriftFinding] = field(default_factory=list)
    notes: tuple[str, ...] = ()

    @property
    def severity(self) -> DriftSeverity:
        order = {
            DriftSeverity.INFORMATIONAL: 0,
            DriftSeverity.WARNING: 1,
            DriftSeverity.REGRESSION: 2,
            DriftSeverity.CRITICAL_REGRESSION: 3,
        }
        if not self.findings:
            return DriftSeverity.INFORMATIONAL
        return max(self.findings, key=lambda f: order[f.severity]).severity

    def summary_counts(self) -> dict[str, int]:
        out = {s.value: 0 for s in DriftSeverity}
        for f in self.findings:
            out[f.severity.value] += 1
        return out

    def as_dict(self) -> dict:
        return {
            "severity": self.severity.value,
            "summary_counts": self.summary_counts(),
            "findings": [f.as_dict() for f in self.findings],
            "notes": list(self.notes),
        }


# ---------------------------------------------------------------------------
# Governance health.
# ---------------------------------------------------------------------------


@dataclass
class DisciplineResult:
    category: DisciplineCategory
    rating: DisciplineRating
    reasons: tuple[str, ...]
    triggering_artifacts: tuple[str, ...] = ()
    affected_subsystems: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {
            "category": self.category.value,
            "rating": self.rating.value,
            "reasons": list(self.reasons),
            "triggering_artifacts": list(self.triggering_artifacts),
            "affected_subsystems": list(self.affected_subsystems),
        }


@dataclass
class GovernanceHealthReport:
    overall: GovernanceHealth
    disciplines: list[DisciplineResult] = field(default_factory=list)
    notes: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {
            "overall": self.overall.value,
            "disciplines": [d.as_dict() for d in self.disciplines],
            "notes": list(self.notes),
        }


# ---------------------------------------------------------------------------
# Freshness.
# ---------------------------------------------------------------------------


@dataclass
class FreshnessEntry:
    record_type: str
    record_id: str
    source_path: str
    generated_at_utc: str
    age_seconds: Optional[int]
    threshold_seconds: int
    status: FreshnessStatus
    notes: str = ""

    def as_dict(self) -> dict:
        return {
            "record_type": self.record_type,
            "record_id": self.record_id,
            "source_path": self.source_path,
            "generated_at_utc": self.generated_at_utc,
            "age_seconds": self.age_seconds,
            "threshold_seconds": self.threshold_seconds,
            "status": self.status.value,
            "notes": self.notes,
        }


@dataclass
class FreshnessReport:
    reference_time_utc: str
    entries: list[FreshnessEntry] = field(default_factory=list)
    notes: tuple[str, ...] = ()

    def status_counts(self) -> dict[str, int]:
        out = {s.value: 0 for s in FreshnessStatus}
        for e in self.entries:
            out[e.status.value] += 1
        return out

    def as_dict(self) -> dict:
        return {
            "reference_time_utc": self.reference_time_utc,
            "status_counts": self.status_counts(),
            "entries": [e.as_dict() for e in self.entries],
            "notes": list(self.notes),
        }


# ---------------------------------------------------------------------------
# Subsystem risk aggregation.
# ---------------------------------------------------------------------------


@dataclass
class SubsystemRiskRow:
    subsystem: str
    frequency: int
    severity_distribution: dict[str, int]
    repeat_regression_count: int
    gate_failure_count: int
    unresolved_warning_count: int
    representative_artifacts: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {
            "subsystem": self.subsystem,
            "frequency": self.frequency,
            "severity_distribution": dict(self.severity_distribution),
            "repeat_regression_count": self.repeat_regression_count,
            "gate_failure_count": self.gate_failure_count,
            "unresolved_warning_count": self.unresolved_warning_count,
            "representative_artifacts": list(self.representative_artifacts),
        }


@dataclass
class SubsystemRiskReport:
    rows: list[SubsystemRiskRow] = field(default_factory=list)
    notes: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {
            "rows": [r.as_dict() for r in self.rows],
            "notes": list(self.notes),
        }


# ---------------------------------------------------------------------------
# Coverage evolution + gate history.
# ---------------------------------------------------------------------------


@dataclass
class CoverageEvolutionEntry:
    timestamp: str
    record_id: str
    evidence_origin: str
    bag_status: str
    coverage_status: str
    review_completion_status: str
    score: Optional[int]

    def as_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "record_id": self.record_id,
            "evidence_origin": self.evidence_origin,
            "bag_status": self.bag_status,
            "coverage_status": self.coverage_status,
            "review_completion_status": self.review_completion_status,
            "score": self.score,
        }


@dataclass
class CoverageEvolutionReport:
    entries: list[CoverageEvolutionEntry] = field(default_factory=list)
    origin_mix_label: str = "unavailable"
    """``static_only_only`` / ``bag_backed_only`` / ``mixed_origin`` /
    ``unavailable``."""

    notes: tuple[str, ...] = ()

    def origin_distribution(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for entry in self.entries:
            out[entry.evidence_origin] = out.get(entry.evidence_origin, 0) + 1
        return out

    def bag_status_distribution(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for entry in self.entries:
            out[entry.bag_status] = out.get(entry.bag_status, 0) + 1
        return out

    def as_dict(self) -> dict:
        return {
            "origin_mix_label": self.origin_mix_label,
            "origin_distribution": self.origin_distribution(),
            "bag_status_distribution": self.bag_status_distribution(),
            "entries": [e.as_dict() for e in self.entries],
            "notes": list(self.notes),
        }


@dataclass
class GateHistoryReport:
    pass_count: int = 0
    warning_count: int = 0
    failure_count: int = 0
    not_executed_count: int = 0
    last_status: str = "unknown"
    last_transition: Optional[str] = None
    """Free-text label of the most recent transition (``passed -> warning``, etc.)."""

    volatility: GateVolatility = GateVolatility.UNKNOWN
    sequence: tuple[str, ...] = ()
    """Ordered list of gate statuses (for the report)."""

    notes: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {
            "pass_count": self.pass_count,
            "warning_count": self.warning_count,
            "failure_count": self.failure_count,
            "not_executed_count": self.not_executed_count,
            "last_status": self.last_status,
            "last_transition": self.last_transition,
            "volatility": self.volatility.value,
            "sequence": list(self.sequence),
            "notes": list(self.notes),
        }


# ---------------------------------------------------------------------------
# Programme review (aggregate).
# ---------------------------------------------------------------------------


@dataclass
class ProgrammeReview:
    generated_at_utc: str
    history_counts: dict[str, int]
    trend_report: TrendReport
    drift_report: DriftReport
    governance_health: GovernanceHealthReport
    freshness_report: FreshnessReport
    subsystem_risk_report: SubsystemRiskReport
    coverage_evolution: CoverageEvolutionReport
    gate_history: GateHistoryReport
    warnings: tuple[str, ...] = ()
    known_limitations: tuple[str, ...] = ()
    fixture_mode: bool = False

    def as_dict(self) -> dict:
        return {
            "generated_at_utc": self.generated_at_utc,
            "history_counts": dict(self.history_counts),
            "trend_report": self.trend_report.as_dict(),
            "drift_report": self.drift_report.as_dict(),
            "governance_health": self.governance_health.as_dict(),
            "freshness_report": self.freshness_report.as_dict(),
            "subsystem_risk_report": self.subsystem_risk_report.as_dict(),
            "coverage_evolution": self.coverage_evolution.as_dict(),
            "gate_history": self.gate_history.as_dict(),
            "warnings": list(self.warnings),
            "known_limitations": list(self.known_limitations),
            "fixture_mode": self.fixture_mode,
        }


PROGRAMME_CERTIFICATION_DISCLAIMER: str = (
    "This programme review is an engineering governance artifact "
    "derived from available reliability and replay evidence. It does "
    "not represent safety certification or regulatory approval."
)


DEFAULT_KNOWN_LIMITATIONS: tuple[str, ...] = (
    "The platform is **not** safety-certified. Programme review is "
    "engineering reliability material.",
    "Trends are deterministic projections of recorded history; the "
    "layer never forecasts future behaviour.",
    "Source-level causality is never inferred. The report records "
    "observations, not blame.",
    "Missing history is reported as ``insufficient_history`` / "
    "``unknown``; it is never silently treated as regression.",
    "Static-only evidence stays static-only across aggregation. "
    "Mixed-origin samples are labelled explicitly.",
    "Baselines and freshness thresholds are caller-supplied; the "
    "layer never auto-updates them.",
)
