"""Replay coverage, gap analysis, quality scoring, review audits."""

from __future__ import annotations

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
    ReplayCoverageStatus,
    ReplayGapSeverity,
    ReplayQualityScore,
    ReviewCompletionStatus,
)
from app.replay_analytics.recommendations import (
    build_recommendations,
    detect_gaps,
)
from app.replay_analytics.reporting import (
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
    score_replay_quality,
)
from app.replay_analytics.trends import build_trends

__all__ = [
    "ANALYTICS_CERTIFICATION_DISCLAIMER",
    "CANONICAL_REVIEW_STEPS",
    "LoadedReplayBundle",
    "ReplayCoverageStatus",
    "ReplayGapSeverity",
    "ReplayQualityScore",
    "ReviewCompletionStatus",
    "analyze_coverage",
    "audit_review",
    "build_comparison",
    "build_index",
    "build_recommendations",
    "build_trends",
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
    "score_replay_quality",
    "write_index",
    "write_review_audit_json",
    "write_review_audit_md",
]
