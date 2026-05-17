"""Impact analysis of source changes on requirements and evidence."""

from __future__ import annotations

from app.reliability_impact.analytics_delta import compute_analytics_delta
from app.reliability_impact.baseline import (
    resolve_baseline,
    write_baseline,
)
from app.reliability_impact.ci_gate import decide_gate
from app.reliability_impact.evidence_mapper import (
    map_evidence,
    map_evidence_for_impacts,
)
from app.reliability_impact.git_changes import collect_source_change
from app.reliability_impact.models import (
    BaselineReference,
    ChangeType,
    ChangedFile,
    DeltaSeverity,
    EvidenceImpact,
    GateStatus,
    ImpactAssessment,
    ReliabilityRisk,
    ReplayAnalyticsDelta,
    RequirementImpact,
    RiskLevel,
    SourceChange,
    Subsystem,
    SubsystemImpact,
)
from app.reliability_impact.report import (
    build_report,
    write_report_files,
)
from app.reliability_impact.requirement_mapper import (
    map_impacts,
    map_subsystem_to_requirements,
)
from app.reliability_impact.risk_assessor import assess_impact
from app.reliability_impact.subsystem_classifier import classify_path

__all__ = [
    "BaselineReference",
    "ChangeType",
    "ChangedFile",
    "DeltaSeverity",
    "EvidenceImpact",
    "GateStatus",
    "ImpactAssessment",
    "ReliabilityRisk",
    "ReplayAnalyticsDelta",
    "RequirementImpact",
    "RiskLevel",
    "SourceChange",
    "Subsystem",
    "SubsystemImpact",
    "assess_impact",
    "build_report",
    "classify_path",
    "collect_source_change",
    "compute_analytics_delta",
    "decide_gate",
    "map_evidence",
    "map_evidence_for_impacts",
    "map_impacts",
    "map_subsystem_to_requirements",
    "resolve_baseline",
    "write_baseline",
    "write_report_files",
]
