"""Phase 9 reliability-impact analysis package.

Read-only with respect to source code, evidence artefacts, and
replay analytics. Inspects git diffs / changed file lists and
derives subsystem impacts, requirement + evidence maps, analytics
deltas vs baseline, a conservative risk assessment, and a CI gate
decision. Tests do not require ROS, Gazebo, Foxglove, or network
access.
"""

from app.reliability_impact.analytics_delta import compute_analytics_delta
from app.reliability_impact.baseline import (
    DEFAULT_BASELINE_ROOT,
    load_baseline_payload,
    resolve_baseline,
    write_baseline,
)
from app.reliability_impact.ci_gate import decide_gate
from app.reliability_impact.evidence_mapper import (
    map_evidence,
    map_evidence_for_impacts,
)
from app.reliability_impact.git_changes import (
    collect_from_ci_env,
    collect_source_change,
)
from app.reliability_impact.models import (
    AnalyticsDeltaEntry,
    BaselineReference,
    ChangedFile,
    ChangeType,
    DEFAULT_KNOWN_LIMITATIONS,
    DeltaSeverity,
    EvidenceImpact,
    GateDecision,
    GateStatus,
    IMPACT_CERTIFICATION_DISCLAIMER,
    ImpactAssessment,
    ImpactReport,
    ReliabilityRisk,
    ReplayAnalyticsDelta,
    RequirementImpact,
    RiskLevel,
    SourceChange,
    Subsystem,
    SubsystemImpact,
    is_safety_critical,
)
from app.reliability_impact.report import (
    build_report,
    render_report_md,
    write_report_files,
)
from app.reliability_impact.requirement_mapper import (
    map_impacts,
    map_subsystem_to_requirements,
)
from app.reliability_impact.risk_assessor import assess_impact
from app.reliability_impact.subsystem_classifier import classify_path

__all__ = [
    "AnalyticsDeltaEntry",
    "BaselineReference",
    "ChangedFile",
    "ChangeType",
    "DEFAULT_BASELINE_ROOT",
    "DEFAULT_KNOWN_LIMITATIONS",
    "DeltaSeverity",
    "EvidenceImpact",
    "GateDecision",
    "GateStatus",
    "IMPACT_CERTIFICATION_DISCLAIMER",
    "ImpactAssessment",
    "ImpactReport",
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
    "collect_from_ci_env",
    "collect_source_change",
    "compute_analytics_delta",
    "decide_gate",
    "is_safety_critical",
    "load_baseline_payload",
    "map_evidence",
    "map_evidence_for_impacts",
    "map_impacts",
    "map_subsystem_to_requirements",
    "render_report_md",
    "resolve_baseline",
    "write_baseline",
    "write_report_files",
]
