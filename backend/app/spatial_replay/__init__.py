"""Phase 17C spatial-replay package.

The platform is **not safety-certified**. This package ingests bag
manifests, optional pose-sample fixtures, and rehearsal events, and
emits a deterministic spatial-replay artefact that the Mission
Control frontend can render alongside the existing bounded-input
mission map.

Honesty hierarchy enforced here:

* ``bag_backed`` — real bag manifest + real pose samples on disk;
* ``fixture`` — committed fixture pose samples (never bag-backed);
* (frontend fallback) ``bounded_inputs`` — derived from bounded
  distance/angle inputs in the mission plan;
* (frontend fallback) ``topology_only`` — waypoint order only;
* (frontend fallback) ``unavailable`` — no spatial data.
"""

from __future__ import annotations

from .builder import build_spatial_replay
from .event_aligner import (
    DEFAULT_ALIGNMENT_TOLERANCE_NS,
    align_event,
    align_events,
)
from .manifest_loader import (
    evaluate_bag_eligibility,
    load_run_manifest,
    manifest_bag_status,
    runtime_run_dir,
)
from .models import (
    DERIVATION_BAG_BACKED,
    DERIVATION_BOUNDED_INPUTS,
    DERIVATION_FIXTURE,
    DERIVATION_SOURCES,
    DERIVATION_TOPOLOGY_ONLY,
    DERIVATION_UNAVAILABLE,
    OPTIONAL_CONTEXT_TOPICS,
    PREFERRED_POSE_TOPICS,
    SPATIAL_REPLAY_DISCLAIMER,
    TRAJECTORY_STATUS_COMPLETE,
    TRAJECTORY_STATUS_MISSING,
    TRAJECTORY_STATUS_PARTIAL,
    TRAJECTORY_STATUSES,
    VALIDATION_STATUS_FAILED,
    VALIDATION_STATUS_NOT_EXECUTED,
    VALIDATION_STATUS_PARTIAL,
    VALIDATION_STATUS_PASSED,
    VALIDATION_STATUSES,
    BagEligibility,
    EventAlignment,
    PoseSample,
    SpatialReplay,
    SpatialValidation,
    TrajectorySegment,
)
from .pose_extractor import (
    POSE_SAMPLES_FILENAME,
    extract_pose_samples,
    fixture_pose_samples_path,
    fixtures_run_dir,
    read_pose_samples,
    runtime_pose_samples_path,
    write_pose_samples,
)
from .reporter import (
    pose_sample_to_dict,
    render_report_markdown,
    run_output_dir,
    runs_dir,
    spatial_replay_to_dict,
    spatial_validation_to_dict,
    trajectory_segment_to_dict,
    write_spatial_replay_artefacts,
)
from .trajectory_builder import (
    bounding_box,
    build_segments,
    classify_trajectory,
    topic_sources,
)
from .validator import (
    compute_missing_topics,
    is_honestly_bag_backed,
    validate_spatial_replay,
)


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
    "POSE_SAMPLES_FILENAME",
    "DEFAULT_ALIGNMENT_TOLERANCE_NS",
    "PoseSample",
    "TrajectorySegment",
    "EventAlignment",
    "SpatialReplay",
    "SpatialValidation",
    "BagEligibility",
    "align_event",
    "align_events",
    "build_segments",
    "build_spatial_replay",
    "bounding_box",
    "classify_trajectory",
    "compute_missing_topics",
    "evaluate_bag_eligibility",
    "extract_pose_samples",
    "fixture_pose_samples_path",
    "fixtures_run_dir",
    "is_honestly_bag_backed",
    "load_run_manifest",
    "manifest_bag_status",
    "pose_sample_to_dict",
    "read_pose_samples",
    "render_report_markdown",
    "run_output_dir",
    "runs_dir",
    "runtime_pose_samples_path",
    "runtime_run_dir",
    "spatial_replay_to_dict",
    "spatial_validation_to_dict",
    "topic_sources",
    "trajectory_segment_to_dict",
    "validate_spatial_replay",
    "write_pose_samples",
    "write_spatial_replay_artefacts",
]
