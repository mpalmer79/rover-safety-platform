"""Phase 6 incident analysis package.

Read-only with respect to runtime evidence. Loads scenario and
runtime evidence, normalises events, builds timelines, reconstructs
causality chains, classifies incidents, and renders Markdown / JSON
reports plus Foxglove replay hints.

The package is pure-logic and does not require ROS or Gazebo to run.
"""

from app.incident_analysis.causality import build_causality_chains
from app.incident_analysis.classifier import classify_incident
from app.incident_analysis.compare import (
    IncidentComparison,
    IncidentComparisonRow,
    compare_incidents,
    render_comparison_md as render_incident_comparison_md,
)
from app.incident_analysis.foxglove import (
    DEFAULT_LAYOUT as FOXGLOVE_DEFAULT_LAYOUT,
    build_foxglove_hint,
    write_default_layout as write_default_foxglove_layout,
)
from app.incident_analysis.index import (
    IncidentIndex,
    IncidentIndexRow,
    build_incident_index,
    render_incident_index_md,
    write_incident_index,
)
from app.incident_analysis.loader import (
    LoadedEvidenceBundle,
    LoadedRuntimeEvidence,
    LoadedScenarioEvidence,
    load_evidence_bundle,
    load_runtime_evidence,
    load_scenario_evidence,
)
from app.incident_analysis.models import (
    CERTIFICATION_DISCLAIMER,
    CausalityChain,
    CausalityConfidence,
    CausalLink,
    EvidenceOrigin,
    FoxgloveReplayHint,
    Incident,
    IncidentBundle,
    IncidentCause,
    IncidentEvidenceManifest,
    IncidentEvidenceStatus,
    IncidentOutcome,
    IncidentSeverity,
    IncidentTimeline,
    LoaderWarning,
    TelemetryCorrelation,
    TimelineEntry,
)
from app.incident_analysis.normalizer import normalise_bundle
from app.incident_analysis.reconstruct import reconstruct_incident
from app.incident_analysis.reporter import (
    derive_operational_interpretation,
    derive_recommendations,
    render_causality_md,
    render_incident_report_md,
    render_recommendations_md,
    write_incident_bundle,
)
from app.incident_analysis.timeline import (
    build_timeline,
    render_sequence_mmd,
    render_state_mmd,
    render_timeline_md,
)

__all__ = [
    "CERTIFICATION_DISCLAIMER",
    "CausalLink",
    "CausalityChain",
    "CausalityConfidence",
    "EvidenceOrigin",
    "FOXGLOVE_DEFAULT_LAYOUT",
    "FoxgloveReplayHint",
    "Incident",
    "IncidentBundle",
    "IncidentCause",
    "IncidentComparison",
    "IncidentComparisonRow",
    "IncidentEvidenceManifest",
    "IncidentEvidenceStatus",
    "IncidentIndex",
    "IncidentIndexRow",
    "IncidentOutcome",
    "IncidentSeverity",
    "IncidentTimeline",
    "LoadedEvidenceBundle",
    "LoadedRuntimeEvidence",
    "LoadedScenarioEvidence",
    "LoaderWarning",
    "TelemetryCorrelation",
    "TimelineEntry",
    "build_causality_chains",
    "build_foxglove_hint",
    "build_incident_index",
    "build_timeline",
    "classify_incident",
    "compare_incidents",
    "derive_operational_interpretation",
    "derive_recommendations",
    "load_evidence_bundle",
    "load_runtime_evidence",
    "load_scenario_evidence",
    "normalise_bundle",
    "reconstruct_incident",
    "render_causality_md",
    "render_incident_comparison_md",
    "render_incident_index_md",
    "render_incident_report_md",
    "render_recommendations_md",
    "render_sequence_mmd",
    "render_state_mmd",
    "render_timeline_md",
    "write_default_foxglove_layout",
    "write_incident_bundle",
    "write_incident_index",
]
