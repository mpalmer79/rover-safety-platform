#!/usr/bin/env python3
"""Run the Phase 10 drift detector and emit the drift report.

Usage:
    rover_ws/tools/detect_reliability_drift.py
        [--reliability-impact-root reliability-impact]
        [--replay-analytics incidents/analytics/replay-analytics-report.json]
        [--incidents-root incidents]
        [--output programme-review/]
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

from app.programme_review import (  # noqa: E402
    build_programme_review,
    render_drift_md,
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
    parser.add_argument("--incidents-root", type=Path, default=Path("incidents"))
    parser.add_argument("--output", type=Path, default=Path("programme-review"))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    review = build_programme_review(
        reliability_impact_roots=args.reliability_impact_roots,
        replay_analytics_paths=args.replay_analytics_paths,
        incidents_root=args.incidents_root,
        reference_time_utc=datetime.now(tz=timezone.utc),
    )
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "drift-report.json").write_text(
        json.dumps(review.drift_report.as_dict(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (args.output / "drift-report.md").write_text(
        render_drift_md(review), encoding="utf-8"
    )
    if args.json:
        json.dump(review.drift_report.as_dict(), sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print(
            f"reliability-drift: severity={review.drift_report.severity.value} "
            f"findings={len(review.drift_report.findings)}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
