"""Typed models for the Phase 9 reliability-impact layer.

The layer is **read-only** with respect to source code, evidence
artefacts, and replay analytics. It inspects git diffs / changed
file lists and derives:

* per-file subsystem classification;
* per-subsystem requirement + evidence impact maps;
* analytics deltas against a pinned baseline;
* a conservative risk assessment;
* a deterministic CI gate decision.

The package never mutates source code, never fabricates git
history, and never fails CI for missing live runtime evidence on a
github-hosted runner. Risk is conservative; warnings are not
promoted to failures.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Optional


class ChangeType(str, Enum):
    """Per-file change kind."""

    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"
    UNKNOWN = "unknown"


class Subsystem(str, Enum):
    """Coarse subsystem buckets for impact analysis.

    The classifier maps every changed file to exactly one bucket.
    Files that don't match a documented prefix fall through to
    :attr:`UNKNOWN`; they are surfaced in the report, never silently
    ignored.
    """

    SAFETY = "safety"
    MISSION = "mission"
    MOTION = "motion"
    REPLAY = "replay"
    INCIDENT_ANALYSIS = "incident_analysis"
    REPLAY_REVIEW = "replay_review"
    REPLAY_ANALYTICS = "replay_analytics"
    RUNTIME_VALIDATION = "runtime_validation"
    VERIFICATION = "verification"
    RELIABILITY_IMPACT = "reliability_impact"
    ROS_WORKSPACE = "ros_workspace"
    GAZEBO_SIMULATION = "gazebo_simulation"
    OBSERVABILITY = "observability"
    DOCS = "docs"
    TESTS = "tests"
    CI = "ci"
    EVIDENCE = "evidence"
    UNKNOWN = "unknown"


class RiskLevel(str, Enum):
    """Conservative risk label for the overall impact assessment."""

    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class GateStatus(str, Enum):
    """CI gate decision (independent of risk level)."""

    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"
    NOT_EXECUTED = "not_executed"


class DeltaSeverity(str, Enum):
    """Severity for a single analytics delta."""

    IMPROVEMENT = "improvement"
    NEUTRAL = "neutral"
    WARNING = "warning"
    REGRESSION = "regression"
    CRITICAL_REGRESSION = "critical_regression"


_SAFETY_CRITICAL_SUBSYSTEMS: frozenset[Subsystem] = frozenset(
    {
        Subsystem.SAFETY,
        Subsystem.MISSION,
        Subsystem.MOTION,
        Subsystem.REPLAY,
        Subsystem.RUNTIME_VALIDATION,
        Subsystem.OBSERVABILITY,
    }
)


def is_safety_critical(subsystem: Subsystem) -> bool:
    return subsystem in _SAFETY_CRITICAL_SUBSYSTEMS


@dataclass(frozen=True)
class ChangedFile:
    path: str
    change_type: ChangeType
    subsystem: Subsystem

    def as_dict(self) -> dict:
        return {
            "path": self.path,
            "change_type": self.change_type.value,
            "subsystem": self.subsystem.value,
        }


@dataclass
class SourceChange:
    """A complete change inventory for one PR / working tree state."""

    base_ref: str
    head_ref: str
    source: str
    """``git_diff`` / ``explicit_list`` / ``working_tree`` / ``ci_env``."""

    changed_files: tuple[ChangedFile, ...] = ()
    warnings: tuple[str, ...] = ()

    def files_by_subsystem(self) -> dict[Subsystem, list[ChangedFile]]:
        out: dict[Subsystem, list[ChangedFile]] = {}
        for f in self.changed_files:
            out.setdefault(f.subsystem, []).append(f)
        return out

    def as_dict(self) -> dict:
        return {
            "base_ref": self.base_ref,
            "head_ref": self.head_ref,
            "source": self.source,
            "changed_files": [f.as_dict() for f in self.changed_files],
            "warnings": list(self.warnings),
        }


@dataclass
class SubsystemImpact:
    subsystem: Subsystem
    changed_files: tuple[ChangedFile, ...]
    """The subset of ``SourceChange.changed_files`` in this subsystem."""

    is_safety_critical: bool = False

    def as_dict(self) -> dict:
        return {
            "subsystem": self.subsystem.value,
            "is_safety_critical": self.is_safety_critical,
            "changed_files": [f.as_dict() for f in self.changed_files],
        }


@dataclass
class RequirementImpact:
    subsystem: Subsystem
    requirement_ids: tuple[str, ...]
    notes: str = ""

    def as_dict(self) -> dict:
        return {
            "subsystem": self.subsystem.value,
            "requirement_ids": list(self.requirement_ids),
            "notes": self.notes,
        }


@dataclass
class EvidenceImpact:
    subsystem: Subsystem
    requirement_ids: tuple[str, ...]
    recommended_tools: tuple[str, ...]
    """Recommended commands / scripts to rerun."""

    recommended_artifacts: tuple[str, ...]
    """Evidence files / directories to regenerate or inspect."""

    notes: str = ""

    def as_dict(self) -> dict:
        return {
            "subsystem": self.subsystem.value,
            "requirement_ids": list(self.requirement_ids),
            "recommended_tools": list(self.recommended_tools),
            "recommended_artifacts": list(self.recommended_artifacts),
            "notes": self.notes,
        }


@dataclass
class AnalyticsDeltaEntry:
    """A single comparison row between current and baseline analytics."""

    label: str
    category: str
    """``score`` / ``coverage`` / ``bag`` / ``review`` / ``gap`` /
    ``contradiction`` / ``incident_count`` / ``honesty``."""

    severity: DeltaSeverity
    detail: str
    baseline_value: Any = None
    current_value: Any = None
    incident_id: Optional[str] = None

    def as_dict(self) -> dict:
        return {
            "label": self.label,
            "category": self.category,
            "severity": self.severity.value,
            "detail": self.detail,
            "baseline_value": _jsonable(self.baseline_value),
            "current_value": _jsonable(self.current_value),
            "incident_id": self.incident_id,
        }


@dataclass
class ReplayAnalyticsDelta:
    baseline_path: Optional[Path]
    current_path: Optional[Path]
    entries: list[AnalyticsDeltaEntry] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def severity(self) -> DeltaSeverity:
        order = {
            DeltaSeverity.IMPROVEMENT: 0,
            DeltaSeverity.NEUTRAL: 0,
            DeltaSeverity.WARNING: 1,
            DeltaSeverity.REGRESSION: 2,
            DeltaSeverity.CRITICAL_REGRESSION: 3,
        }
        if not self.entries:
            return DeltaSeverity.NEUTRAL
        return max(self.entries, key=lambda e: order[e.severity]).severity

    def summary_counts(self) -> dict[str, int]:
        out = {s.value: 0 for s in DeltaSeverity}
        for entry in self.entries:
            out[entry.severity.value] += 1
        return out

    def as_dict(self) -> dict:
        return {
            "baseline_path": str(self.baseline_path) if self.baseline_path else "",
            "current_path": str(self.current_path) if self.current_path else "",
            "severity": self.severity.value,
            "summary_counts": self.summary_counts(),
            "warnings": list(self.warnings),
            "entries": [e.as_dict() for e in self.entries],
        }


@dataclass
class ReliabilityRisk:
    label: str
    level: RiskLevel
    rationale: str
    cited_artifacts: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {
            "label": self.label,
            "level": self.level.value,
            "rationale": self.rationale,
            "cited_artifacts": list(self.cited_artifacts),
        }


@dataclass
class ImpactAssessment:
    risks: list[ReliabilityRisk] = field(default_factory=list)
    overall_risk: RiskLevel = RiskLevel.NONE

    def as_dict(self) -> dict:
        return {
            "overall_risk": self.overall_risk.value,
            "risks": [r.as_dict() for r in self.risks],
        }


@dataclass
class GateDecision:
    status: GateStatus
    failures: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {
            "status": self.status.value,
            "failures": list(self.failures),
            "warnings": list(self.warnings),
            "notes": list(self.notes),
        }


@dataclass
class BaselineReference:
    quality_index_path: Optional[Path]
    analytics_report_path: Optional[Path]
    notes: str = ""

    @property
    def available(self) -> bool:
        return self.quality_index_path is not None or self.analytics_report_path is not None

    def as_dict(self) -> dict:
        return {
            "quality_index_path": (
                str(self.quality_index_path) if self.quality_index_path else ""
            ),
            "analytics_report_path": (
                str(self.analytics_report_path)
                if self.analytics_report_path
                else ""
            ),
            "notes": self.notes,
            "available": self.available,
        }


@dataclass
class ImpactReport:
    base_ref: str
    head_ref: str
    source: str
    source_change: SourceChange
    subsystem_impacts: tuple[SubsystemImpact, ...]
    requirement_impacts: tuple[RequirementImpact, ...]
    evidence_impacts: tuple[EvidenceImpact, ...]
    analytics_delta: ReplayAnalyticsDelta
    assessment: ImpactAssessment
    gate_decision: GateDecision
    baseline: BaselineReference
    known_limitations: tuple[str, ...] = ()
    generated_at_utc: str = ""
    fixture_mode: bool = False
    """When True the report was generated from a fixture file list,
    not a real git diff. The reporter labels this explicitly."""

    def as_dict(self) -> dict:
        return {
            "base_ref": self.base_ref,
            "head_ref": self.head_ref,
            "source": self.source,
            "fixture_mode": self.fixture_mode,
            "source_change": self.source_change.as_dict(),
            "subsystem_impacts": [s.as_dict() for s in self.subsystem_impacts],
            "requirement_impacts": [r.as_dict() for r in self.requirement_impacts],
            "evidence_impacts": [e.as_dict() for e in self.evidence_impacts],
            "analytics_delta": self.analytics_delta.as_dict(),
            "assessment": self.assessment.as_dict(),
            "gate_decision": self.gate_decision.as_dict(),
            "baseline": self.baseline.as_dict(),
            "known_limitations": list(self.known_limitations),
            "generated_at_utc": self.generated_at_utc,
        }


IMPACT_CERTIFICATION_DISCLAIMER: str = (
    "This impact report is an engineering traceability artifact. It "
    "does not represent safety certification or regulatory approval."
)


# Default known limitations applied to every generated report.
DEFAULT_KNOWN_LIMITATIONS: tuple[str, ...] = (
    "The platform is **not** safety-certified. Impact analysis is "
    "engineering reliability material.",
    "Source-level causality is asserted only when supported by "
    "explicit evidence; missing data is reported, not inferred.",
    "Missing live runtime evidence on github-hosted CI is never "
    "treated as a failure; the gate only fails when explicit "
    "criteria are met.",
    "Baselines are managed intentionally via the `--write-baseline` "
    "CLI flag; CI never auto-updates them.",
    "When git history is unavailable the impact tooling supports "
    "`--changed-files` mode; metadata derived from git is reported "
    "as `not_executed` in that mode.",
)


def _jsonable(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    return repr(value)
