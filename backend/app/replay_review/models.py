"""Typed models for the Phase 7 replay review layer.

The layer is read-only with respect to runtime evidence and rosbag2
artefacts: it inspects, indexes, and produces metadata. It never
fabricates a bag inventory and never claims live replay success
unless a real bag is present.

Status vocabularies follow Phase 6 honesty rules: missing bags are
``missing_bag``, static scenario fixtures stay ``static_only``, and
``not_executed`` is reserved for paths that genuinely require a live
ROS host.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Optional


class ReplayExecutionStatus(str, Enum):
    """Top-level replay-readiness status for an incident bundle."""

    READY = "ready"
    PARTIAL = "partial"
    MISSING_BAG = "missing_bag"
    STATIC_ONLY = "static_only"
    NOT_EXECUTED = "not_executed"
    FAILED = "failed"
    PASSED = "passed"


class ReplayValidationStatus(str, Enum):
    """Per-check validation status (mirrors the Phase-3 vocabulary)."""

    PASSED = "passed"
    FAILED = "failed"
    PARTIAL = "partial"
    SKIPPED = "skipped"
    NOT_EXECUTED = "not_executed"


class ReplayEvidenceOrigin(str, Enum):
    """Where a replay artefact came from.

    The layer accepts the Phase-6 origins plus a new ``bag-backed``
    origin used only when a real bag artefact is detected.
    """

    STATIC_SOURCE = "static-source"
    STATIC_WORKSPACE = "static-workspace"
    SCENARIO_EVIDENCE = "scenario-evidence"
    RUNTIME_EVIDENCE = "runtime-evidence"
    LIVE_RUNTIME = "live-runtime"
    BAG_BACKED = "bag-backed"
    UNKNOWN = "unknown"


# Topics every replay review session expects to find when a real bag
# is present. The list mirrors the Phase 4 / Phase 5 contract; the
# manifest's `expected_topics` defaults to this set.
EXPECTED_REPLAY_TOPICS: tuple[str, ...] = (
    "/clock",
    "/scan",
    "/imu",
    "/odom",
    "/tf",
    "/tf_static",
    "/cmd_vel_requested",
    "/cmd_vel_authorized",
    "/safety/state",
    "/safety/events",
    "/system/health",
    "/mission/state",
    "/mission/events",
    "/mission/progress",
    "/world_model/state",
)


_BAG_FILE_EXTENSIONS: frozenset[str] = frozenset({".db3", ".mcap"})


def is_bag_file(path: Path) -> bool:
    """Return True for filenames that look like rosbag2 bag chunks."""

    return path.suffix.lower() in _BAG_FILE_EXTENSIONS


@dataclass
class BagArtifact:
    """One bag-related file detected by :mod:`bag_index`."""

    path: Path
    kind: str
    """``mcap`` / ``db3`` / ``metadata`` / ``unknown``."""

    size_bytes: int
    notes: str = ""

    def as_dict(self) -> dict:
        return {
            "path": str(self.path),
            "kind": self.kind,
            "size_bytes": self.size_bytes,
            "notes": self.notes,
        }


@dataclass
class BagIndex:
    """Result of indexing a candidate bag directory."""

    bag_root: Path
    artifacts: list[BagArtifact] = field(default_factory=list)
    metadata_path: Optional[Path] = None
    inventory_topics: tuple[str, ...] = ()
    """Topics declared in ``metadata.yaml`` (when readable)."""

    message_counts: dict[str, int] = field(default_factory=dict)
    start_time_ns: Optional[int] = None
    end_time_ns: Optional[int] = None
    notes: list[str] = field(default_factory=list)
    """Free-text notes recorded during indexing (e.g. metadata not
    parseable, no bag chunks present, etc.). The replay validator
    surfaces these to the operator."""

    @property
    def has_bag_chunks(self) -> bool:
        return any(a.kind in {"mcap", "db3"} for a in self.artifacts)

    @property
    def has_metadata(self) -> bool:
        return self.metadata_path is not None

    @property
    def status(self) -> ReplayExecutionStatus:
        if self.has_bag_chunks and self.has_metadata:
            return ReplayExecutionStatus.READY
        if self.has_bag_chunks or self.has_metadata:
            return ReplayExecutionStatus.PARTIAL
        return ReplayExecutionStatus.MISSING_BAG

    def as_dict(self) -> dict:
        return {
            "bag_root": str(self.bag_root),
            "status": self.status.value,
            "has_bag_chunks": self.has_bag_chunks,
            "has_metadata": self.has_metadata,
            "metadata_path": str(self.metadata_path) if self.metadata_path else "",
            "inventory_topics": list(self.inventory_topics),
            "message_counts": dict(self.message_counts),
            "start_time_ns": self.start_time_ns,
            "end_time_ns": self.end_time_ns,
            "artifacts": [a.as_dict() for a in self.artifacts],
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class ReplayTopic:
    """A topic the replay session expects to find."""

    name: str
    purpose: str
    required: bool = True

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "purpose": self.purpose,
            "required": self.required,
        }


@dataclass
class ReplayMarker:
    """Timeline marker for an operational review session."""

    marker_id: str
    label: str
    description: str
    timeline_index: int
    """Index into the incident timeline."""

    relative_time_ms: Optional[int]
    sim_time_ns: Optional[int]
    source_event_id: str
    source_file: str
    confidence: str
    """One of ``direct`` / ``strong`` / ``moderate`` / ``weak`` /
    ``inconclusive`` / ``unknown``. Mirrors the Phase 6
    ``CausalityConfidence`` vocabulary; ``unknown`` is used when
    causality did not run."""

    evidence_origin: ReplayEvidenceOrigin
    alignment: str = "exact"
    """One of ``exact`` (sim_time_ns present) / ``partial``
    (relative time only) / ``unaligned`` (no time signal)."""

    def as_dict(self) -> dict:
        return {
            "marker_id": self.marker_id,
            "label": self.label,
            "description": self.description,
            "timeline_index": self.timeline_index,
            "relative_time_ms": self.relative_time_ms,
            "sim_time_ns": self.sim_time_ns,
            "source_event_id": self.source_event_id,
            "source_file": self.source_file,
            "confidence": self.confidence,
            "evidence_origin": self.evidence_origin.value,
            "alignment": self.alignment,
        }


@dataclass
class FoxglovePanelHint:
    panel_id: str
    title: str
    """Panel title for the Foxglove layout."""

    topics: tuple[str, ...]
    notes: str = ""

    def as_dict(self) -> dict:
        return {
            "panel_id": self.panel_id,
            "title": self.title,
            "topics": list(self.topics),
            "notes": self.notes,
        }


@dataclass
class FoxgloveSession:
    """Replay-session metadata.

    The format is **not** an official Foxglove session import. It is a
    plain JSON document that points at the canonical layout, lists
    recommended topics, and embeds the timeline markers so a reviewer
    can open the bag in Foxglove with the right context. The
    ``schema_version`` makes that explicit.
    """

    incident_id: str
    layout_path: str
    recommended_data_source: str
    expected_topics: tuple[str, ...]
    panel_hints: tuple[FoxglovePanelHint, ...]
    marker_overlays: tuple[dict, ...]
    review_notes: str = ""
    known_limitations: tuple[str, ...] = ()
    schema_version: str = "rover-replay-review/1"
    """This format is internal to the project; reviewers must import
    the layout file separately. The schema_version makes that explicit."""

    def as_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "incident_id": self.incident_id,
            "layout_path": self.layout_path,
            "recommended_data_source": self.recommended_data_source,
            "expected_topics": list(self.expected_topics),
            "panel_hints": [p.as_dict() for p in self.panel_hints],
            "marker_overlays": [dict(m) for m in self.marker_overlays],
            "review_notes": self.review_notes,
            "known_limitations": list(self.known_limitations),
        }


@dataclass
class ReplayValidationResult:
    name: str
    status: ReplayValidationStatus
    detail: str = ""
    reason: str = ""
    evidence_paths: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status.value,
            "detail": self.detail,
            "reason": self.reason,
            "evidence_paths": list(self.evidence_paths),
        }


@dataclass
class ReplayReviewManifest:
    """Per-incident replay manifest (the ``replay-review-manifest.json``)."""

    incident_id: str
    run_id: Optional[str]
    scenario_id: Optional[str]
    evidence_status: str
    """Mirrors the Phase 6 incident's ``evidence_status``."""

    bag_status: ReplayExecutionStatus
    bag_indices: tuple[BagIndex, ...]
    expected_topics: tuple[ReplayTopic, ...]
    available_topics: tuple[str, ...]
    missing_topics: tuple[str, ...]
    foxglove_layout_path: str
    foxglove_session_path: str
    timeline_marker_count: int
    review_steps: tuple[str, ...]
    known_limitations: tuple[str, ...]
    generated_at_utc: str = ""

    def as_dict(self) -> dict:
        return {
            "incident_id": self.incident_id,
            "run_id": self.run_id,
            "scenario_id": self.scenario_id,
            "evidence_status": self.evidence_status,
            "bag_status": self.bag_status.value,
            "bag_indices": [b.as_dict() for b in self.bag_indices],
            "expected_topics": [t.as_dict() for t in self.expected_topics],
            "available_topics": list(self.available_topics),
            "missing_topics": list(self.missing_topics),
            "foxglove_layout_path": self.foxglove_layout_path,
            "foxglove_session_path": self.foxglove_session_path,
            "timeline_marker_count": self.timeline_marker_count,
            "review_steps": list(self.review_steps),
            "known_limitations": list(self.known_limitations),
            "generated_at_utc": self.generated_at_utc,
        }


@dataclass
class ReplayReviewReport:
    """Aggregate report (the ``replay-review-report.{md,json}``)."""

    incident_id: str
    run_id: Optional[str]
    scenario_id: Optional[str]
    bag_status: ReplayExecutionStatus
    replay_execution_status: ReplayExecutionStatus
    evidence_origin: ReplayEvidenceOrigin
    expected_topics: tuple[str, ...]
    available_topics: tuple[str, ...]
    missing_topics: tuple[str, ...]
    timeline_markers: tuple[ReplayMarker, ...]
    foxglove_layout_path: str
    foxglove_session_path: str
    review_workflow: tuple[str, ...]
    known_limitations: tuple[str, ...]
    validation_results: tuple[ReplayValidationResult, ...]
    operator_checklist: tuple[str, ...]
    generated_at_utc: str = ""

    @property
    def overall_status(self) -> ReplayExecutionStatus:
        # The execution status drives the report; the bag status is
        # captured in a dedicated field.
        return self.replay_execution_status

    def status_counts(self) -> dict[str, int]:
        out = {s.value: 0 for s in ReplayValidationStatus}
        for v in self.validation_results:
            out[v.status.value] += 1
        return out

    def as_dict(self) -> dict:
        return {
            "incident_id": self.incident_id,
            "run_id": self.run_id,
            "scenario_id": self.scenario_id,
            "bag_status": self.bag_status.value,
            "replay_execution_status": self.replay_execution_status.value,
            "evidence_origin": self.evidence_origin.value,
            "expected_topics": list(self.expected_topics),
            "available_topics": list(self.available_topics),
            "missing_topics": list(self.missing_topics),
            "timeline_markers": [m.as_dict() for m in self.timeline_markers],
            "foxglove_layout_path": self.foxglove_layout_path,
            "foxglove_session_path": self.foxglove_session_path,
            "review_workflow": list(self.review_workflow),
            "known_limitations": list(self.known_limitations),
            "validation_results": [v.as_dict() for v in self.validation_results],
            "operator_checklist": list(self.operator_checklist),
            "generated_at_utc": self.generated_at_utc,
            "status_counts": self.status_counts(),
        }


@dataclass(frozen=True)
class ReplayReviewBundle:
    """Output of the bundle orchestrator."""

    incident_id: str
    bundle_dir: Path
    manifest: ReplayReviewManifest
    report: ReplayReviewReport
    foxglove_session: FoxgloveSession
    markers: tuple[ReplayMarker, ...]

    def as_dict(self) -> dict:
        return {
            "incident_id": self.incident_id,
            "bundle_dir": str(self.bundle_dir),
            "manifest": self.manifest.as_dict(),
            "report": self.report.as_dict(),
            "foxglove_session": self.foxglove_session.as_dict(),
            "markers": [m.as_dict() for m in self.markers],
        }


REPLAY_CERTIFICATION_DISCLAIMER: str = (
    "This replay review is an engineering analysis artifact generated "
    "from available simulation and runtime evidence. It does not "
    "represent safety certification or regulatory approval."
)
