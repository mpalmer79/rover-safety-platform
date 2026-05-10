"""Typed models for the Phase 8 replay analytics layer.

The analytics layer is **read-only** with respect to incident
bundles, replay manifests, and rosbag2 artefacts. It derives
deterministic metrics, scores, and trends; it never mutates source
evidence and never invents replay coverage.

Status vocabularies preserve Phase 6 / Phase 7 honesty:
* missing artefacts are reported (never silently substituted);
* static-only incidents stay static-only;
* operator review completion is recognised only via an explicit
  acknowledgement.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Optional


class ReplayCoverageStatus(str, Enum):
    """Aggregate coverage label for an incident."""

    COMPLETE = "complete"
    SUBSTANTIAL = "substantial"
    PARTIAL = "partial"
    SPARSE = "sparse"
    MISSING = "missing"


class ReviewCompletionStatus(str, Enum):
    """Operator review completion status."""

    NOT_STARTED = "not_started"
    PARTIAL = "partial"
    COMPLETED = "completed"
    INCONCLUSIVE = "inconclusive"


class ReplayGapSeverity(str, Enum):
    """Severity for an individual gap finding."""

    INFORMATIONAL = "informational"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


# Metric names used in the coverage and quality reports. Keeping the
# vocabulary explicit so the reporter and tests share one source of
# truth.
COVERAGE_METRIC_NAMES: tuple[str, ...] = (
    "expected_topics_present_pct",
    "marker_alignment_pct",
    "timeline_alignment_pct",
    "replay_validation_pass_rate",
    "evidence_completeness_pct",
    "review_artifact_completeness_pct",
)


@dataclass
class ReplayCoverageMetric:
    """One coverage metric derived from a replay-review bundle."""

    name: str
    value: Optional[float]
    """``None`` when the metric is unavailable (e.g. no bag inventory).
    The scoring engine treats unavailable metrics conservatively."""

    available: bool
    detail: str = ""
    """Free-text explanation; the reporter renders this verbatim."""

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "value": self.value,
            "available": self.available,
            "detail": self.detail,
        }


@dataclass
class ReplayCoverageReport:
    """Per-incident coverage report."""

    incident_id: str
    bag_status: str
    """Mirror of the Phase-7 ``ReplayExecutionStatus`` value."""

    evidence_origin: str
    metrics: tuple[ReplayCoverageMetric, ...]
    coverage_status: ReplayCoverageStatus
    notes: tuple[str, ...] = ()
    generated_at_utc: str = ""

    def metric(self, name: str) -> Optional[ReplayCoverageMetric]:
        for m in self.metrics:
            if m.name == name:
                return m
        return None

    def as_dict(self) -> dict:
        return {
            "incident_id": self.incident_id,
            "bag_status": self.bag_status,
            "evidence_origin": self.evidence_origin,
            "metrics": [m.as_dict() for m in self.metrics],
            "coverage_status": self.coverage_status.value,
            "notes": list(self.notes),
            "generated_at_utc": self.generated_at_utc,
        }


@dataclass
class ReplayQualityScore:
    """Deterministic 0-100 quality score for an incident."""

    incident_id: str
    score: int
    """Integer 0..100. Static-only incidents are capped below 40;
    missing-bag below 60; complete replay at or above 90."""

    confidence: str
    """``high`` when the bag is bag-backed and every metric is
    available; ``moderate`` when at least one metric is unavailable;
    ``low`` for static-only / missing-bag."""

    coverage_status: ReplayCoverageStatus
    quality_summary: str
    blocking_gaps: tuple[str, ...]
    """Free-text labels (e.g. ``missing_bag``, ``contradictions``)."""

    def as_dict(self) -> dict:
        return {
            "incident_id": self.incident_id,
            "score": self.score,
            "confidence": self.confidence,
            "coverage_status": self.coverage_status.value,
            "quality_summary": self.quality_summary,
            "blocking_gaps": list(self.blocking_gaps),
        }


@dataclass
class ReplayGap:
    """A single gap detected during analysis."""

    incident_id: str
    label: str
    severity: ReplayGapSeverity
    detail: str
    evidence_paths: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {
            "incident_id": self.incident_id,
            "label": self.label,
            "severity": self.severity.value,
            "detail": self.detail,
            "evidence_paths": list(self.evidence_paths),
        }


@dataclass
class ReplayRecommendation:
    """Deterministic, evidence-grounded recommendation."""

    incident_id: str
    label: str
    detail: str
    cited_artifacts: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {
            "incident_id": self.incident_id,
            "label": self.label,
            "detail": self.detail,
            "cited_artifacts": list(self.cited_artifacts),
        }


@dataclass
class ReviewAudit:
    """Operator-review completion audit for a single incident."""

    incident_id: str
    status: ReviewCompletionStatus
    completed_steps: tuple[str, ...]
    pending_steps: tuple[str, ...]
    operator: str = ""
    notes: str = ""
    audit_path: str = ""
    """Pointer to the explicit ``review-audit.json`` artefact, when present."""

    def as_dict(self) -> dict:
        return {
            "incident_id": self.incident_id,
            "status": self.status.value,
            "completed_steps": list(self.completed_steps),
            "pending_steps": list(self.pending_steps),
            "operator": self.operator,
            "notes": self.notes,
            "audit_path": self.audit_path,
        }


@dataclass
class ReplayComparison:
    """Cross-incident analytics comparison."""

    comparison_id: str
    rows: list[dict] = field(default_factory=list)
    """Per-incident projected rows, ordered deterministically by
    descending quality score then by incident id."""

    deltas: list[dict] = field(default_factory=list)
    """Pairwise observations across the rows (latency deltas,
    coverage deltas, evidence-origin notes)."""

    notes: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {
            "comparison_id": self.comparison_id,
            "rows": list(self.rows),
            "deltas": list(self.deltas),
            "notes": list(self.notes),
        }


@dataclass
class ReplayTrend:
    """Aggregate trend table across many incidents."""

    bag_status_distribution: dict[str, int] = field(default_factory=dict)
    coverage_status_distribution: dict[str, int] = field(default_factory=dict)
    review_completion_distribution: dict[str, int] = field(default_factory=dict)
    evidence_origin_distribution: dict[str, int] = field(default_factory=dict)
    quality_score_buckets: dict[str, int] = field(default_factory=dict)
    """Buckets are ``0-39``, ``40-69``, ``70-89``, ``90-100``."""

    most_common_safety_states: list[tuple[str, int]] = field(default_factory=list)
    most_common_outcomes: list[tuple[str, int]] = field(default_factory=list)
    most_common_missing_topics: list[tuple[str, int]] = field(default_factory=list)
    most_common_gaps: list[tuple[str, int]] = field(default_factory=list)
    incident_count: int = 0
    notes: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {
            "bag_status_distribution": dict(self.bag_status_distribution),
            "coverage_status_distribution": dict(
                self.coverage_status_distribution
            ),
            "review_completion_distribution": dict(
                self.review_completion_distribution
            ),
            "evidence_origin_distribution": dict(
                self.evidence_origin_distribution
            ),
            "quality_score_buckets": dict(self.quality_score_buckets),
            "most_common_safety_states": [
                list(t) for t in self.most_common_safety_states
            ],
            "most_common_outcomes": [list(t) for t in self.most_common_outcomes],
            "most_common_missing_topics": [
                list(t) for t in self.most_common_missing_topics
            ],
            "most_common_gaps": [list(t) for t in self.most_common_gaps],
            "incident_count": self.incident_count,
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class ReplayAnalyticsIndexRow:
    incident_id: str
    quality_score: int
    coverage_status: str
    review_completion_status: str
    bag_status: str
    evidence_origin: str
    marker_alignment_pct: Optional[float]
    evidence_completeness_pct: Optional[float]
    contradiction_count: int
    replay_validation_status: str
    scenario_id: Optional[str] = None

    def as_dict(self) -> dict:
        return {
            "incident_id": self.incident_id,
            "scenario_id": self.scenario_id,
            "quality_score": self.quality_score,
            "coverage_status": self.coverage_status,
            "review_completion_status": self.review_completion_status,
            "bag_status": self.bag_status,
            "evidence_origin": self.evidence_origin,
            "marker_alignment_pct": self.marker_alignment_pct,
            "evidence_completeness_pct": self.evidence_completeness_pct,
            "contradiction_count": self.contradiction_count,
            "replay_validation_status": self.replay_validation_status,
        }


@dataclass
class ReplayAnalyticsIndex:
    rows: list[ReplayAnalyticsIndexRow] = field(default_factory=list)

    def filter(
        self,
        *,
        min_score: Optional[int] = None,
        max_score: Optional[int] = None,
        coverage_status: Optional[str] = None,
        bag_status: Optional[str] = None,
        review_completion_status: Optional[str] = None,
        evidence_origin: Optional[str] = None,
        replay_validation_status: Optional[str] = None,
    ) -> list[ReplayAnalyticsIndexRow]:
        out: list[ReplayAnalyticsIndexRow] = []
        for row in self.rows:
            if min_score is not None and row.quality_score < min_score:
                continue
            if max_score is not None and row.quality_score > max_score:
                continue
            if coverage_status is not None and row.coverage_status != coverage_status:
                continue
            if bag_status is not None and row.bag_status != bag_status:
                continue
            if (
                review_completion_status is not None
                and row.review_completion_status != review_completion_status
            ):
                continue
            if evidence_origin is not None and row.evidence_origin != evidence_origin:
                continue
            if (
                replay_validation_status is not None
                and row.replay_validation_status != replay_validation_status
            ):
                continue
            out.append(row)
        return out

    def as_dict(self) -> dict:
        return {"rows": [r.as_dict() for r in self.rows]}


ANALYTICS_CERTIFICATION_DISCLAIMER: str = (
    "This replay analytics report is an engineering analysis "
    "artifact derived from available replay-review bundles. It does "
    "not represent safety certification or regulatory approval."
)
