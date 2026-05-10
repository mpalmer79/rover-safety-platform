"""Phase 8 replay analytics package.

Read-only with respect to incident bundles, replay manifests, and
rosbag2 artefacts. Derives deterministic coverage metrics + quality
scores + trends + comparisons + recommendations from the artefacts
shipped by Phase 6 (incident reconstruction) and Phase 7 (replay
review). Tests do not require ROS, Gazebo, or Foxglove.
"""

from app.replay_analytics.comparison import (
    build_comparison,
    render_comparison_md,
)
from app.replay_analytics.coverage import analyze_coverage
from app.replay_analytics.index import (
    build_index,
    render_index_md,
    write_index,
)
from app.replay_analytics.loader import (
    LoadedReplayBundle,
    load_replay_bundle,
    load_replay_bundles,
)
from app.replay_analytics.models import (
    ANALYTICS_CERTIFICATION_DISCLAIMER,
    COVERAGE_METRIC_NAMES,
    ReplayAnalyticsIndex,
    ReplayAnalyticsIndexRow,
    ReplayComparison,
    ReplayCoverageMetric,
    ReplayCoverageReport,
    ReplayCoverageStatus,
    ReplayGap,
    ReplayGapSeverity,
    ReplayQualityScore,
    ReplayRecommendation,
    ReplayTrend,
    ReviewAudit,
    ReviewCompletionStatus,
)
from app.replay_analytics.recommendations import (
    build_recommendations,
    detect_gaps,
)
from app.replay_analytics.reporting import (
    bundles_by_id,
    render_aggregate_report_md,
    render_gap_analysis_md,
    render_per_incident_report_md,
    render_quality_index_json,
    render_trends_md,
)
from app.replay_analytics.review_audit import (
    CANONICAL_REVIEW_STEPS,
    audit_review,
    write_review_audit_json,
    write_review_audit_md,
)
from app.replay_analytics.scoring import (
    quality_bucket,
    score_for_metrics,
    score_replay_quality,
)
from app.replay_analytics.trends import build_trends


__all__ = [
    "ANALYTICS_CERTIFICATION_DISCLAIMER",
    "CANONICAL_REVIEW_STEPS",
    "COVERAGE_METRIC_NAMES",
    "LoadedReplayBundle",
    "ReplayAnalyticsIndex",
    "ReplayAnalyticsIndexRow",
    "ReplayComparison",
    "ReplayCoverageMetric",
    "ReplayCoverageReport",
    "ReplayCoverageStatus",
    "ReplayGap",
    "ReplayGapSeverity",
    "ReplayQualityScore",
    "ReplayRecommendation",
    "ReplayTrend",
    "ReviewAudit",
    "ReviewCompletionStatus",
    "analyze_coverage",
    "audit_review",
    "build_comparison",
    "build_index",
    "build_recommendations",
    "build_trends",
    "bundles_by_id",
    "detect_gaps",
    "load_replay_bundle",
    "load_replay_bundles",
    "quality_bucket",
    "render_aggregate_report_md",
    "render_comparison_md",
    "render_gap_analysis_md",
    "render_index_md",
    "render_per_incident_report_md",
    "render_quality_index_json",
    "render_trends_md",
    "score_for_metrics",
    "score_replay_quality",
    "write_index",
    "write_review_audit_json",
    "write_review_audit_md",
]
