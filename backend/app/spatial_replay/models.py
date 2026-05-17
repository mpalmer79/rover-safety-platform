"""Typed models for the Phase 17C spatial-replay layer.

The platform is **not safety-certified**. The spatial-replay package
is read-only with respect to runtime state: it ingests bag manifests
(via :mod:`backend.app.live_runtime`), optionally reads committed
pose-sample fixtures, builds deterministic trajectories, aligns
rehearsal events, and emits a frontend-consumable artefact.

Honesty rules baked into the data model:

* ``derivation_source`` is the single source of truth for *where the
  spatial geometry came from*. It is never inferred upward; a fixture
  may not be re-labelled ``bag_backed``.
* ``bag_status`` mirrors the bag manifest verbatim; if a manifest is
  missing or invalid the field still reports the honest state.
* ``validation_status`` reports the *artefact* validation, not the
  scenario outcome. A scenario can pass while the bag manifest
  validates ``partial`` (e.g. missing /tf).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


SPATIAL_REPLAY_DISCLAIMER: str = (
    "This project is not safety-certified. The spatial-replay "
    "layer renders bounded-input or bag-backed evidence; it never "
    "fabricates telemetry, and a fixture-derived map is never "
    "labelled bag-backed."
)


# Derivation-source vocabulary. The frontend uses these strings
# verbatim - never re-stringify them.
DERIVATION_BAG_BACKED: str = "bag_backed"
DERIVATION_FIXTURE: str = "fixture"
DERIVATION_BOUNDED_INPUTS: str = "bounded_inputs"
DERIVATION_TOPOLOGY_ONLY: str = "topology_only"
DERIVATION_UNAVAILABLE: str = "unavailable"

DERIVATION_SOURCES: tuple[str, ...] = (
    DERIVATION_BAG_BACKED,
    DERIVATION_FIXTURE,
    DERIVATION_BOUNDED_INPUTS,
    DERIVATION_TOPOLOGY_ONLY,
    DERIVATION_UNAVAILABLE,
)


# Trajectory-status vocabulary.
TRAJECTORY_STATUS_COMPLETE: str = "complete"
TRAJECTORY_STATUS_PARTIAL: str = "partial"
TRAJECTORY_STATUS_MISSING: str = "missing"

TRAJECTORY_STATUSES: tuple[str, ...] = (
    TRAJECTORY_STATUS_COMPLETE,
    TRAJECTORY_STATUS_PARTIAL,
    TRAJECTORY_STATUS_MISSING,
)


# Validation vocabulary.
VALIDATION_STATUS_PASSED: str = "passed"
VALIDATION_STATUS_PARTIAL: str = "partial"
VALIDATION_STATUS_FAILED: str = "failed"
VALIDATION_STATUS_NOT_EXECUTED: str = "not_executed"

VALIDATION_STATUSES: tuple[str, ...] = (
    VALIDATION_STATUS_PASSED,
    VALIDATION_STATUS_PARTIAL,
    VALIDATION_STATUS_FAILED,
    VALIDATION_STATUS_NOT_EXECUTED,
)


# Preferred pose topics. Order matters: the trajectory builder
# prefers /odom samples over /tf samples when both exist for the
# same timestamp.
PREFERRED_POSE_TOPICS: tuple[str, ...] = ("/odom", "/tf", "/tf_static")

# Optional context topics (event/health). These do NOT produce
# trajectory samples; the event-aligner reads them.
OPTIONAL_CONTEXT_TOPICS: tuple[str, ...] = (
    "/mission/events",
    "/safety/events",
    "/system/health",
)


@dataclass(frozen=True)
class PoseSample:
    """A single pose sample on the trajectory.

    Fields mirror the on-disk JSONL fixture format. ``confidence``
    is the source-supplied confidence string; the trajectory builder
    never *upgrades* this value.
    """

    sample_id: str
    time_ns: int
    x_m: float
    y_m: float
    theta_rad: float
    source_topic: str
    confidence: str = "unknown"
    event_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class TrajectorySegment:
    """A connecting segment between two consecutive pose samples."""

    from_sample_id: str
    to_sample_id: str
    distance_m: float
    duration_ns: int


@dataclass(frozen=True)
class EventAlignment:
    """Alignment of a rehearsal event to its nearest pose sample.

    When no pose sample is within the alignment tolerance the
    ``matched_sample_id`` is empty and ``spatial_position`` is
    ``None``. The UI then renders the event in the timeline only.
    """

    event_id: str
    deterministic_hash: str
    matched_sample_id: str
    spatial_position: tuple[float, float] | None
    delta_time_ns: int
    confidence: str


@dataclass(frozen=True)
class SpatialValidation:
    """Per-run spatial validation outcome.

    ``status`` is one of :data:`VALIDATION_STATUSES`; ``warnings``
    are human-readable strings; ``missing_topics`` enumerates the
    topics that the rehearsal expected but the bag/fixture did not
    contain.
    """

    status: str
    warnings: tuple[str, ...] = ()
    missing_topics: tuple[str, ...] = ()
    topic_sources: tuple[str, ...] = ()
    sample_count: int = 0
    bag_validation_warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class SpatialReplay:
    """The complete spatial-replay artefact for one run.

    The frontend consumes the JSON serialisation produced by
    :func:`backend.app.spatial_replay.reporter.spatial_replay_to_dict`.
    """

    run_id: str
    scenario_id: str
    mission_id: str
    evidence_origin: str
    bag_status: str
    derivation_source: str
    trajectory_status: str
    validation_status: str
    samples: tuple[PoseSample, ...] = ()
    segments: tuple[TrajectorySegment, ...] = ()
    event_alignments: tuple[EventAlignment, ...] = ()
    topic_sources: tuple[str, ...] = ()
    missing_topics: tuple[str, ...] = ()
    known_limitations: tuple[str, ...] = ()
    generated_at_utc: str = ""
    note: str = ""


@dataclass(frozen=True)
class BagEligibility:
    """Outcome of the bag-backed eligibility check.

    ``is_bag_backed`` is true only if every honesty rule (manifest
    present, bag paths on disk, metadata yaml on disk, validation
    status passed/partial, pose samples available) is satisfied.
    """

    is_bag_backed: bool
    reasons: tuple[str, ...]
    """Free-text reasons why the run was *not* bag-backed. Empty
    tuple iff ``is_bag_backed`` is true."""


__all__ = [
    "SPATIAL_REPLAY_DISCLAIMER",
    "DERIVATION_BAG_BACKED",
    "DERIVATION_FIXTURE",
    "DERIVATION_BOUNDED_INPUTS",
    "DERIVATION_TOPOLOGY_ONLY",
    "DERIVATION_UNAVAILABLE",
    "DERIVATION_SOURCES",
    "TRAJECTORY_STATUS_COMPLETE",
    "TRAJECTORY_STATUS_PARTIAL",
    "TRAJECTORY_STATUS_MISSING",
    "TRAJECTORY_STATUSES",
    "VALIDATION_STATUS_PASSED",
    "VALIDATION_STATUS_PARTIAL",
    "VALIDATION_STATUS_FAILED",
    "VALIDATION_STATUS_NOT_EXECUTED",
    "VALIDATION_STATUSES",
    "PREFERRED_POSE_TOPICS",
    "OPTIONAL_CONTEXT_TOPICS",
    "PoseSample",
    "TrajectorySegment",
    "EventAlignment",
    "SpatialValidation",
    "SpatialReplay",
    "BagEligibility",
]
