#!/usr/bin/env python3
"""Compare replay-review bundles across incidents.

Reads two or more incident bundles (each containing
``incident-report.json`` + the Phase-7 replay-review artefacts) and
emits a structured analytics comparison: quality scores, coverage
metrics, marker alignment, missing-topic counts, contradictions,
review completion, and pairwise deltas.

Usage:
    rover_ws/tools/compare_replay_reviews.py <bundle-dir> [<bundle-dir> ...]
        [--comparison-id <id>]
        [--out-dir incidents/analytics/comparisons]
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

from app.replay_analytics.comparison import (  # noqa: E402
    build_comparison,
    render_comparison_md,
)
from app.replay_analytics.coverage import analyze_coverage  # noqa: E402
from app.replay_analytics.loader import load_replay_bundle  # noqa: E402
from app.replay_analytics.review_audit import audit_review  # noqa: E402
from app.replay_analytics.scoring import score_replay_quality  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundles", type=Path, nargs="+")
    parser.add_argument("--comparison-id", type=str, default="")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("incidents/analytics/comparisons"),
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if len(args.bundles) < 2:
        parser.error("compare requires at least two bundle directories")

    cid = args.comparison_id or datetime.now(tz=timezone.utc).strftime(
        "comparison-%Y%m%dT%H%M%SZ"
    )

    bundles = [load_replay_bundle(b) for b in args.bundles]
    coverages = {b.incident_id: analyze_coverage(b) for b in bundles}
    scores = {
        b.incident_id: score_replay_quality(
            bundle=b, coverage=coverages[b.incident_id]
        )
        for b in bundles
    }
    # Audits aren't part of the comparison rows directly but we want
    # them loaded so the bundle's review_audit field is populated.
    for b in bundles:
        audit_review(b)
    comparison = build_comparison(
        comparison_id=cid,
        bundles=bundles,
        coverages=coverages,
        scores=scores,
    )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.out_dir / f"{cid}.json"
    md_path = args.out_dir / f"{cid}.md"
    json_path.write_text(
        json.dumps(comparison.as_dict(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    md_path.write_text(render_comparison_md(comparison), encoding="utf-8")

    if args.json:
        json.dump(comparison.as_dict(), sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print(f"replay-analytics-comparison {cid}: rows={len(comparison.rows)}")
        print(f"  json: {json_path}")
        print(f"  md:   {md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
