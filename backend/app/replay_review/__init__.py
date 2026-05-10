"""Phase 7 replay review package.

Read-only with respect to runtime evidence and rosbag2 artefacts.
Inspects bag directories, generates per-incident replay manifests,
emits Foxglove session metadata, validates the result, and renders
Markdown + JSON reports.

The package never opens a bag file — Foxglove handles that. Tests do
not require Foxglove or ROS.
"""

from app.replay_review.bag_index import (
    candidate_bag_roots,
    index_bag_candidates,
    index_bag_directory,
    merge_inventory,
)
from app.replay_review.bundle import build_replay_review
from app.replay_review.foxglove_session import (
    build_foxglove_session,
    write_session,
)
from app.replay_review.manifest import (
    build_manifest,
    default_replay_topics,
    render_manifest_md,
)
from app.replay_review.marker import (
    alignment_status,
    build_markers,
)
from app.replay_review.models import (
    BagArtifact,
    BagIndex,
    EXPECTED_REPLAY_TOPICS,
    FoxglovePanelHint,
    FoxgloveSession,
    REPLAY_CERTIFICATION_DISCLAIMER,
    ReplayEvidenceOrigin,
    ReplayExecutionStatus,
    ReplayMarker,
    ReplayReviewBundle,
    ReplayReviewManifest,
    ReplayReviewReport,
    ReplayTopic,
    ReplayValidationResult,
    ReplayValidationStatus,
    is_bag_file,
)
from app.replay_review.reporter import build_report, render_report_md
from app.replay_review.validator import aggregate_status, validate_replay_review

__all__ = [
    "BagArtifact",
    "BagIndex",
    "EXPECTED_REPLAY_TOPICS",
    "FoxglovePanelHint",
    "FoxgloveSession",
    "REPLAY_CERTIFICATION_DISCLAIMER",
    "ReplayEvidenceOrigin",
    "ReplayExecutionStatus",
    "ReplayMarker",
    "ReplayReviewBundle",
    "ReplayReviewManifest",
    "ReplayReviewReport",
    "ReplayTopic",
    "ReplayValidationResult",
    "ReplayValidationStatus",
    "aggregate_status",
    "alignment_status",
    "build_foxglove_session",
    "build_manifest",
    "build_markers",
    "build_replay_review",
    "build_report",
    "candidate_bag_roots",
    "default_replay_topics",
    "index_bag_candidates",
    "index_bag_directory",
    "is_bag_file",
    "merge_inventory",
    "render_manifest_md",
    "render_report_md",
    "validate_replay_review",
    "write_session",
]
