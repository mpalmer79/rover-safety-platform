#!/usr/bin/env python3
"""Generate the Phase 10 programme review bundle.

Aggregates reliability-impact bundles, replay analytics reports,
runtime qualification summaries, replay review reports, and
incident reports across the configured roots into a single
governance-grade review.

The CLI is deterministic given the same inputs (apart from the
``--reference-time`` field used for freshness checks).

Usage:
    rover_ws/tools/generate_programme_review.py
        [--reliability-impact-root reliability-impact]
        [--replay-analytics incidents/analytics/replay-analytics-report.json]
        [--runtime-evidence-root evidence/runtime]
        [--incidents-root incidents]
        [--reference-time YYYY-MM-DDTHH:MM:SSZ]
        [--output programme-review/]
        [--fixture]
        [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from _probe_common import ensure_app_on_path  # noqa: E402

ensure_app_on_path()

from app.programme_review import (  # noqa: E402
    build_programme_review,
    write_programme_review_bundle,
)


def _parse_reference_time(value: Optional[str]) -> Optional[datetime]:
    if value is None:
        return None
    try:
        ts = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise SystemExit(f"--reference-time must be ISO-8601 (got {value!r})")
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reliability-impact-root",
        type=Path,
        default=None,
        action="append",
        dest="reliability_impact_roots",
        help="reliability-impact root; pass multiple times for multiple roots",
    )
    parser.add_argument(
        "--replay-analytics",
        type=Path,
        default=None,
        action="append",
        dest="replay_analytics_paths",
        help="replay-analytics-report.json path; pass multiple times for history",
    )
    parser.add_argument(
        "--runtime-evidence-root",
        type=Path,
        default=Path("evidence/runtime"),
    )
    parser.add_argument(
        "--incidents-root", type=Path, default=Path("incidents")
    )
    parser.add_argument("--reference-time", type=str, default=None)
    parser.add_argument(
        "--output", type=Path, default=Path("programme-review")
    )
    parser.add_argument("--fixture", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    reliability_impact_roots = args.reliability_impact_roots or [
        Path("reliability-impact")
    ]
    replay_analytics_paths = args.replay_analytics_paths or [
        Path("incidents/analytics/replay-analytics-report.json")
    ]
    review = build_programme_review(
        reliability_impact_roots=reliability_impact_roots,
        replay_analytics_paths=replay_analytics_paths,
        runtime_evidence_root=args.runtime_evidence_root,
        incidents_root=args.incidents_root,
        reference_time_utc=_parse_reference_time(args.reference_time),
        fixture_mode=args.fixture,
    )
    write_programme_review_bundle(review, out_dir=args.output)

    if args.json:
        json.dump(review.as_dict(), sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print(
            f"programme-review: health={review.governance_health.overall.value} "
            f"drift={review.drift_report.severity.value} "
            f"gate_volatility={review.gate_history.volatility.value} "
            f"records={sum(review.history_counts.values())}"
        )
        print(f"  output: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
