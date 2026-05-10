#!/usr/bin/env python3
"""Emit the Phase 10 evidence freshness report.

Usage:
    rover_ws/tools/review_evidence_freshness.py
        [--reliability-impact-root reliability-impact]
        [--replay-analytics incidents/analytics/replay-analytics-report.json]
        [--runtime-evidence-root evidence/runtime]
        [--incidents-root incidents]
        [--reference-time YYYY-MM-DDTHH:MM:SSZ]
        [--output programme-review/]
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
    assess_freshness,
    load_history,
    render_freshness_md,
)
from app.programme_review.aggregation import build_programme_review  # noqa: E402


def _parse_reference_time(value: Optional[str]) -> Optional[datetime]:
    if value is None:
        return None
    ts = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts


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
    parser.add_argument("--reference-time", type=str, default=None)
    parser.add_argument("--output", type=Path, default=Path("programme-review"))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    reference = _parse_reference_time(args.reference_time) or datetime.now(
        tz=timezone.utc
    )
    history = load_history(
        reliability_impact_roots=args.reliability_impact_roots,
        replay_analytics_paths=args.replay_analytics_paths,
        runtime_evidence_root=args.runtime_evidence_root,
        incidents_root=args.incidents_root,
    )
    report = assess_freshness(history=history, reference_time_utc=reference)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "freshness-report.json").write_text(
        json.dumps(report.as_dict(), indent=2, sort_keys=True), encoding="utf-8"
    )
    review = build_programme_review(
        history=history, reference_time_utc=reference
    )
    (args.output / "freshness-report.md").write_text(
        render_freshness_md(review), encoding="utf-8"
    )
    if args.json:
        json.dump(report.as_dict(), sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        counts = report.status_counts()
        print(
            f"evidence-freshness: fresh={counts['fresh']} stale={counts['stale']} "
            f"unknown={counts['unknown']} reference={reference.isoformat()}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
