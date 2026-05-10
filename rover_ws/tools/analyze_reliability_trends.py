#!/usr/bin/env python3
"""Run the Phase 10 trend analyser and emit the trend report.

The CLI loads the same history the full programme-review uses, but
emits **only** the trend report (Markdown + JSON). Useful when the
operator wants to inspect trends without rebuilding the full
review.

Usage:
    rover_ws/tools/analyze_reliability_trends.py
        [--reliability-impact-root reliability-impact]
        [--replay-analytics incidents/analytics/replay-analytics-report.json]
        [--runtime-evidence-root evidence/runtime]
        [--incidents-root incidents]
        [--output programme-review/]
        [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _probe_common import ensure_app_on_path  # noqa: E402

ensure_app_on_path()

from app.programme_review import (  # noqa: E402
    build_trend_report,
    load_history,
    render_trend_md,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reliability-impact-root",
        type=Path,
        action="append",
        default=[Path("reliability-impact")],
        dest="reliability_impact_roots",
    )
    parser.add_argument(
        "--replay-analytics",
        type=Path,
        action="append",
        default=[Path("incidents/analytics/replay-analytics-report.json")],
        dest="replay_analytics_paths",
    )
    parser.add_argument(
        "--runtime-evidence-root", type=Path, default=Path("evidence/runtime")
    )
    parser.add_argument("--incidents-root", type=Path, default=Path("incidents"))
    parser.add_argument("--output", type=Path, default=Path("programme-review"))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    history = load_history(
        reliability_impact_roots=args.reliability_impact_roots,
        replay_analytics_paths=args.replay_analytics_paths,
        runtime_evidence_root=args.runtime_evidence_root,
        incidents_root=args.incidents_root,
    )
    trend = build_trend_report(history)
    args.output.mkdir(parents=True, exist_ok=True)
    payload = trend.as_dict()
    (args.output / "trend-report.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    md_path = args.output / "trend-report.md"
    md_path.parent.mkdir(parents=True, exist_ok=True)
    from app.programme_review import ProgrammeReview
    from app.programme_review.reporting import render_trend_md
    # Reuse the existing renderer by composing a minimal review object.
    from datetime import datetime, timezone
    from app.programme_review.aggregation import build_programme_review

    # Use the full builder so the renderer's expectations are met.
    full = build_programme_review(
        history=history,
        reference_time_utc=datetime.now(tz=timezone.utc),
    )
    md_path.write_text(render_trend_md(full), encoding="utf-8")
    if args.json:
        json.dump(payload, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print(
            f"reliability-trends: series={len(trend.series)} "
            f"history_records={sum(history.counts().values())}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
