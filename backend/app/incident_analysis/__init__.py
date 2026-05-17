"""Incident reconstruction: timelines, causality, recommendations."""

from __future__ import annotations

from app.incident_analysis.causality import build_causality_chains
from app.incident_analysis.classifier import classify_incident
from app.incident_analysis.compare import (
    compare_incidents,
    render_comparison_md as render_incident_comparison_md,
)
from app.incident_analysis.foxglove import (
    DEFAULT_LAYOUT as FOXGLOVE_DEFAULT_LAYOUT,
    build_foxglove_hint,
    write_default_layout as write_default_foxglove_layout,
)
from app.incident_analysis.index import (
    build_incident_index,
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
    CausalLink,
    CausalityChain,
    CausalityConfidence,
    EvidenceOrigin,
    Incident,
    IncidentEvidenceStatus,
    IncidentOutcome,
    IncidentSeverity,
    IncidentTimeline,
    TimelineEntry,
)
from app.incident_analysis.normalizer import normalise_bundle
from app.incident_analysis.reconstruct import reconstruct_incident
from app.incident_analysis.reporter import (
    derive_recommendations,
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
    "Incident",
    "IncidentEvidenceStatus",
    "IncidentOutcome",
    "IncidentSeverity",
    "IncidentTimeline",
    "LoadedEvidenceBundle",
    "LoadedRuntimeEvidence",
    "LoadedScenarioEvidence",
    "TimelineEntry",
    "build_causality_chains",
    "build_foxglove_hint",
    "build_incident_index",
    "build_timeline",
    "classify_incident",
    "compare_incidents",
    "derive_recommendations",
    "load_evidence_bundle",
    "load_runtime_evidence",
    "load_scenario_evidence",
    "normalise_bundle",
    "reconstruct_incident",
    "render_incident_comparison_md",
    "render_incident_report_md",
    "render_recommendations_md",
    "render_sequence_mmd",
    "render_state_mmd",
    "render_timeline_md",
    "write_default_foxglove_layout",
    "write_incident_bundle",
    "write_incident_index",
]
