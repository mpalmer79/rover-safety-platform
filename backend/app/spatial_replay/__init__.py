"""Pose trajectory hydration and spatial replay artefacts."""

from __future__ import annotations

from .builder import build_spatial_replay
from .event_aligner import (
    DEFAULT_ALIGNMENT_TOLERANCE_NS,
    align_event,
    align_events,
)
from .manifest_loader import evaluate_bag_eligibility
from .models import (
    DERIVATION_BAG_BACKED,
    DERIVATION_FIXTURE,
    DERIVATION_UNAVAILABLE,
    PoseSample,
    SpatialReplay,
    TRAJECTORY_STATUS_COMPLETE,
    TRAJECTORY_STATUS_PARTIAL,
)
from .pose_extractor import (
    read_pose_samples,
    write_pose_samples,
)
from .reporter import (
    run_output_dir,
    spatial_replay_to_dict,
    write_spatial_replay_artefacts,
)
from .trajectory_builder import (
    build_segments,
    classify_trajectory,
    topic_sources,
)
from .validator import (
    is_honestly_bag_backed,
    validate_spatial_replay,
)

__all__ = [
    "DEFAULT_ALIGNMENT_TOLERANCE_NS",
    "DERIVATION_BAG_BACKED",
    "DERIVATION_FIXTURE",
    "DERIVATION_UNAVAILABLE",
    "PoseSample",
    "SpatialReplay",
    "TRAJECTORY_STATUS_COMPLETE",
    "TRAJECTORY_STATUS_PARTIAL",
    "align_event",
    "align_events",
    "build_segments",
    "build_spatial_replay",
    "classify_trajectory",
    "evaluate_bag_eligibility",
    "is_honestly_bag_backed",
    "read_pose_samples",
    "run_output_dir",
    "spatial_replay_to_dict",
    "topic_sources",
    "validate_spatial_replay",
    "write_pose_samples",
    "write_spatial_replay_artefacts",
]
