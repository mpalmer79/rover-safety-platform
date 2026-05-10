"""Typed models for the incident analysis layer.

The package is read-only with respect to runtime evidence. These
models exist so the loader, normaliser, timeline builder, causality
engine, classifier, and reporter can pass structured values without
touching the underlying JSON shapes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Optional


class IncidentSeverity(str, Enum):
    INFORMATIONAL = "informational"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentOutcome(str, Enum):
    CONTROLLED_DEGRADATION = "controlled_degradation"
    SAFE_STOP_SUCCESS = "safe_stop_success"
    ESTOP_LATCHED = "estop_latched"
    MISSION_ABORTED = "mission_aborted"
    RECOVERY_SUCCESS = "recovery_success"
    RECOVERY_FAILED = "recovery_failed"
    INCONCLUSIVE = "inconclusive"


class IncidentEvidenceStatus(str, Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    STATIC_ONLY = "static_only"
    LIVE_RUNTIME = "live_runtime"
    NOT_EXECUTED = "not_executed"
    MISSING = "missing"
    INCONSISTENT = "inconsistent"


class EvidenceOrigin(str, Enum):
    STATIC_SOURCE = "static-source"
    STATIC_WORKSPACE = "static-workspace"
    LIVE_RUNTIME = "live-runtime"
    SCENARIO_EVIDENCE = "scenario-evidence"
    RUNTIME_EVIDENCE = "runtime-evidence"
    UNKNOWN = "unknown"


class CausalityConfidence(str, Enum):
    DIRECT = "direct"
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    INCONCLUSIVE = "inconclusive"


_TIMELINE_CATEGORIES: tuple[str, ...] = (
    "safety_transition",
    "mission_transition",
    "fault_injection",
    "motion_arbitration",
    "watchdog",
    "sensor_health",
    "replay",
    "operator_action",
    "runtime_validation",
    "diagnostic_health",
    "qualification",
    "regression",
    "system_lifecycle",
    "world_model",
    "recovery",
    "unknown",
)


def is_known_category(value: str) -> bool:
    return value in _TIMELINE_CATEGORIES


@dataclass
class LoaderWarning:
    """A structured warning produced by the loader / normaliser."""

    category: str
    """Free-text category, e.g. ``missing_file``, ``malformed_json``,
    ``schema_drift``, ``empty_event_stream``."""

    detail: str
    source: Optional[Path] = None

    def as_dict(self) -> dict:
        return {
            "category": self.category,
            "detail": self.detail,
            "source": str(self.source) if self.source else "",
        }


@dataclass
class TimelineEntry:
    """One canonical entry in the incident timeline.

    ``timestamp`` is ISO-8601 when known. ``relative_time_ms`` is the
    monotonic offset from the first event (when ``sim_time_ns`` is
    available); otherwise ``None``.
    """

    sequence_index: int
    """Zero-based monotonic ordering index assigned by the timeline
    builder. Stable and deterministic for a given evidence set."""

    timestamp: str
    relative_time_ms: Optional[int]
    sim_time_ns: Optional[int]
    source_file: str
    category: str
    event_type: str
    severity: str
    safety_state: Optional[str]
    mission_state: Optional[str]
    reason_code: Optional[str]
    message: str
    evidence_origin: EvidenceOrigin
    run_id: Optional[str]
    scenario_id: Optional[str]
    raw_reference: Optional[str]
    """Free-text pointer into the source file (event id, line number,
    JSON key) so a reviewer can find the original record."""

    attributes: dict = field(default_factory=dict)
    """Domain-specific attributes copied verbatim from the source
    record (e.g. ``fault_id``, ``fault_type``, transition reason).
    The normaliser preserves these so downstream causality rules can
    inspect them."""

    def as_dict(self) -> dict:
        return {
            "sequence_index": self.sequence_index,
            "timestamp": self.timestamp,
            "relative_time_ms": self.relative_time_ms,
            "sim_time_ns": self.sim_time_ns,
            "source_file": self.source_file,
            "category": self.category,
            "event_type": self.event_type,
            "severity": self.severity,
            "safety_state": self.safety_state,
            "mission_state": self.mission_state,
            "reason_code": self.reason_code,
            "message": self.message,
            "evidence_origin": self.evidence_origin.value,
            "run_id": self.run_id,
            "scenario_id": self.scenario_id,
            "raw_reference": self.raw_reference,
            "attributes": dict(self.attributes),
        }


@dataclass
class CausalLink:
    """A single edge in a causality chain."""

    from_entry_index: int
    to_entry_index: int
    relation: str
    """Free-text label, e.g. ``triggered``, ``escalated_to``,
    ``zeroed_motion_in``, ``inferred_from``."""

    confidence: CausalityConfidence
    rationale: str
    inferred: bool
    """``True`` when the link is inferred (no direct event evidence)."""

    def as_dict(self) -> dict:
        return {
            "from_entry_index": self.from_entry_index,
            "to_entry_index": self.to_entry_index,
            "relation": self.relation,
            "confidence": self.confidence.value,
            "rationale": self.rationale,
            "inferred": self.inferred,
        }


@dataclass
class CausalityChain:
    """A named chain of :class:`CausalLink` instances."""

    chain_id: str
    """Stable identifier, e.g. ``stale_lidar_chain``,
    ``command_timeout_chain``."""

    description: str
    links: list[CausalLink] = field(default_factory=list)
    missing_links: list[str] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)
    overall_confidence: CausalityConfidence = CausalityConfidence.INCONCLUSIVE

    def as_dict(self) -> dict:
        return {
            "chain_id": self.chain_id,
            "description": self.description,
            "overall_confidence": self.overall_confidence.value,
            "links": [link.as_dict() for link in self.links],
            "missing_links": list(self.missing_links),
            "contradictions": list(self.contradictions),
        }


@dataclass
class TelemetryCorrelation:
    """A documented correlation between two timeline entries.

    Used by the reporter to surface notable temporal relationships
    that fell outside a named causality chain.
    """

    label: str
    primary_index: int
    secondary_index: int
    delta_ms: Optional[int]
    note: str

    def as_dict(self) -> dict:
        return {
            "label": self.label,
            "primary_index": self.primary_index,
            "secondary_index": self.secondary_index,
            "delta_ms": self.delta_ms,
            "note": self.note,
        }


@dataclass
class IncidentTimeline:
    incident_id: str
    entries: list[TimelineEntry] = field(default_factory=list)
    out_of_order_indices: list[int] = field(default_factory=list)
    """Indices that the source data placed in non-monotonic order;
    the timeline builder records them and re-sorts deterministically."""

    first_fault_index: Optional[int] = None
    first_safety_transition_index: Optional[int] = None
    first_command_intervention_index: Optional[int] = None
    terminal_index: Optional[int] = None

    def as_dict(self) -> dict:
        return {
            "incident_id": self.incident_id,
            "entry_count": len(self.entries),
            "out_of_order_indices": list(self.out_of_order_indices),
            "first_fault_index": self.first_fault_index,
            "first_safety_transition_index": self.first_safety_transition_index,
            "first_command_intervention_index": self.first_command_intervention_index,
            "terminal_index": self.terminal_index,
            "entries": [e.as_dict() for e in self.entries],
        }


@dataclass
class FoxgloveReplayHint:
    recommended_topics: tuple[str, ...]
    timeline_markers: tuple[dict, ...]
    """Each marker is ``{"sim_time_ns", "label", "category"}``."""

    safety_state_topic: str
    mission_state_topic: str
    command_topics: tuple[str, ...]
    fault_topics: tuple[str, ...]
    diagnostic_topics: tuple[str, ...]
    layout_path: str
    notes: str = ""

    def as_dict(self) -> dict:
        return {
            "recommended_topics": list(self.recommended_topics),
            "timeline_markers": [dict(m) for m in self.timeline_markers],
            "safety_state_topic": self.safety_state_topic,
            "mission_state_topic": self.mission_state_topic,
            "command_topics": list(self.command_topics),
            "fault_topics": list(self.fault_topics),
            "diagnostic_topics": list(self.diagnostic_topics),
            "layout_path": self.layout_path,
            "notes": self.notes,
        }


@dataclass
class IncidentCause:
    """Top-level cause assigned by the classifier (best-evidence)."""

    label: str
    confidence: CausalityConfidence
    rationale: str
    evidence_paths: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {
            "label": self.label,
            "confidence": self.confidence.value,
            "rationale": self.rationale,
            "evidence_paths": list(self.evidence_paths),
        }


@dataclass
class IncidentEvidenceManifest:
    """Per-file evidence presence and origin."""

    files: dict[str, dict] = field(default_factory=dict)
    """Map ``relative_path -> {origin, present, size_bytes, notes}``."""

    warnings: list[LoaderWarning] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "files": dict(self.files),
            "warnings": [w.as_dict() for w in self.warnings],
        }


@dataclass
class Incident:
    incident_id: str
    run_id: Optional[str]
    scenario_id: Optional[str]
    severity: IncidentSeverity
    outcome: IncidentOutcome
    evidence_status: IncidentEvidenceStatus
    cause: Optional[IncidentCause] = None
    safety_states: tuple[str, ...] = ()
    mission_states: tuple[str, ...] = ()
    fault_ids: tuple[str, ...] = ()
    timeline: Optional[IncidentTimeline] = None
    causality_chains: list[CausalityChain] = field(default_factory=list)
    telemetry_correlations: list[TelemetryCorrelation] = field(default_factory=list)
    foxglove_hint: Optional[FoxgloveReplayHint] = None
    evidence_manifest: IncidentEvidenceManifest = field(
        default_factory=IncidentEvidenceManifest
    )
    missing_evidence: tuple[str, ...] = ()
    contradictions: tuple[str, ...] = ()
    operational_interpretation: str = ""
    recommended_follow_up: tuple[str, ...] = ()
    generated_at_utc: str = ""

    def as_dict(self) -> dict:
        return {
            "incident_id": self.incident_id,
            "run_id": self.run_id,
            "scenario_id": self.scenario_id,
            "severity": self.severity.value,
            "outcome": self.outcome.value,
            "evidence_status": self.evidence_status.value,
            "cause": self.cause.as_dict() if self.cause else None,
            "safety_states": list(self.safety_states),
            "mission_states": list(self.mission_states),
            "fault_ids": list(self.fault_ids),
            "timeline": self.timeline.as_dict() if self.timeline else None,
            "causality_chains": [c.as_dict() for c in self.causality_chains],
            "telemetry_correlations": [
                t.as_dict() for t in self.telemetry_correlations
            ],
            "foxglove_hint": (
                self.foxglove_hint.as_dict() if self.foxglove_hint else None
            ),
            "evidence_manifest": self.evidence_manifest.as_dict(),
            "missing_evidence": list(self.missing_evidence),
            "contradictions": list(self.contradictions),
            "operational_interpretation": self.operational_interpretation,
            "recommended_follow_up": list(self.recommended_follow_up),
            "generated_at_utc": self.generated_at_utc,
        }


@dataclass(frozen=True)
class IncidentBundle:
    """A reconstructed incident plus the paths where its artefacts live."""

    incident: Incident
    bundle_dir: Path

    def as_dict(self) -> dict:
        return {
            "incident": self.incident.as_dict(),
            "bundle_dir": str(self.bundle_dir),
        }


CERTIFICATION_DISCLAIMER: str = (
    "This report is an engineering analysis artifact generated from "
    "available simulation and runtime evidence. It does not represent "
    "safety certification or regulatory approval."
)
