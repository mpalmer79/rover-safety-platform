#!/usr/bin/env python3
"""Generate the cross-incident analytics report, trends, gap analysis, and index.

Scans ``incidents/`` (or a custom root), runs the Phase-8 analytics
on every bundle that has a Phase-7 replay-review, and writes:

* ``incidents/analytics/replay-analytics-report.md`` / ``.json``;
* ``incidents/analytics/replay-quality-index.json``;
* ``incidents/analytics/replay-gap-analysis.md``;
* ``incidents/analytics/trends/replay-trends.md`` / ``.json``;
* ``incidents/analytics/index.json`` + ``docs/REPLAY_ANALYTICS_INDEX.md``.

Usage:
    rover_ws/tools/generate_replay_analytics.py
        [--incidents-root incidents]
        [--analytics-root incidents/analytics]
        [--md-index-out docs/REPLAY_ANALYTICS_INDEX.md]
        [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from _probe_common import ensure_app_on_path  # noqa: E402

ensure_app_on_path()

from app.replay_analytics import (  # noqa: E402
    analyze_coverage,
    audit_review,
    build_index,
    build_recommendations,
    build_trends,
    detect_gaps,
    load_replay_bundles,
    render_aggregate_report_md,
    render_gap_analysis_md,
    render_quality_index_json,
    render_trends_md,
    score_replay_quality,
    write_index,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--incidents-root", type=Path, default=Path("incidents")
    )
    parser.add_argument(
        "--analytics-root", type=Path, default=Path("incidents/analytics")
    )
    parser.add_argument(
        "--md-index-out", type=Path, default=Path("docs/REPLAY_ANALYTICS_INDEX.md")
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    bundles = load_replay_bundles(args.incidents_root)
    coverages = {b.incident_id: analyze_coverage(b) for b in bundles}
    scores = {
        b.incident_id: score_replay_quality(
            bundle=b, coverage=coverages[b.incident_id]
        )
        for b in bundles
    }
    audits = {b.incident_id: audit_review(b) for b in bundles}
    gaps = {
        b.incident_id: detect_gaps(bundle=b, coverage=coverages[b.incident_id])
        for b in bundles
    }
    recommendations = {
        b.incident_id: build_recommendations(bundle=b, gaps=gaps[b.incident_id])
        for b in bundles
    }
    trend = build_trends(
        bundles=bundles,
        coverages=coverages.values(),
        scores=scores.values(),
        gaps_by_incident={k: [g.as_dict() for g in v] for k, v in gaps.items()},
    )

    args.analytics_root.mkdir(parents=True, exist_ok=True)
    trends_dir = args.analytics_root / "trends"
    trends_dir.mkdir(parents=True, exist_ok=True)

    md_report = render_aggregate_report_md(
        bundles=bundles,
        coverages=coverages,
        scores=scores,
        audits=audits,
        trend=trend,
        recommendations_by_incident=recommendations,
    )
    (args.analytics_root / "replay-analytics-report.md").write_text(
        md_report, encoding="utf-8"
    )
    payload = {
        "generated_at_utc": datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
        "incident_count": len(bundles),
        "trend": trend.as_dict(),
        "scores": [s.as_dict() for s in scores.values()],
        "coverages": [c.as_dict() for c in coverages.values()],
        "audits": [a.as_dict() for a in audits.values()],
        "recommendations": {k: [r.as_dict() for r in v] for k, v in recommendations.items()},
    }
    (args.analytics_root / "replay-analytics-report.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    quality_index = render_quality_index_json(
        bundles=bundles, scores=scores, coverages=coverages
    )
    (args.analytics_root / "replay-quality-index.json").write_text(
        json.dumps(quality_index, indent=2, sort_keys=True), encoding="utf-8"
    )

    (args.analytics_root / "replay-gap-analysis.md").write_text(
        render_gap_analysis_md(gaps_by_incident=gaps), encoding="utf-8"
    )

    (trends_dir / "replay-trends.md").write_text(
        render_trends_md(trend), encoding="utf-8"
    )
    (trends_dir / "replay-trends.json").write_text(
        json.dumps(trend.as_dict(), indent=2, sort_keys=True), encoding="utf-8"
    )

    index = build_index(
        bundles=bundles,
        coverages=coverages,
        scores=scores,
        audits=audits,
    )
    write_index(
        index,
        json_path=args.analytics_root / "index.json",
        md_path=args.md_index_out,
    )

    summary = {
        "incident_count": len(bundles),
        "buckets": trend.quality_score_buckets,
        "bag_status_distribution": trend.bag_status_distribution,
    }
    if args.json:
        json.dump(summary, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print(
            f"replay-analytics: {len(bundles)} bundle(s) — "
            f"buckets={trend.quality_score_buckets} "
            f"bag_distribution={trend.bag_status_distribution}"
        )
        print(f"  report:  {args.analytics_root / 'replay-analytics-report.md'}")
        print(f"  trends:  {trends_dir / 'replay-trends.md'}")
        print(f"  gaps:    {args.analytics_root / 'replay-gap-analysis.md'}")
        print(f"  index:   {args.md_index_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
