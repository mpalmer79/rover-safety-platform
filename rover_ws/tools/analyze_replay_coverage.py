#!/usr/bin/env python3
"""Analyse a single replay-review bundle and emit per-incident analytics.

Reads ``incident-report.json`` + ``replay-review-manifest.json`` +
``replay-review-report.json`` + ``replay-markers.json`` from the
supplied incident directory and produces:

* ``replay-analytics.md`` / ``.json`` — per-incident analytics report;
* ``replay-coverage.json`` — coverage metrics;
* ``replay-quality-score.json`` — deterministic 0..100 score;
* ``replay-gaps.json`` — detected gaps (with severity);
* ``review-audit.md`` / ``.json`` — operator-review audit;
* ``replay-recommendations.json`` — deterministic recommendations.

The CLI never opens a bag file. Static-only / missing-bag incidents
score honestly: they cannot reach the 70-89 / 90-100 bands.

Usage:
    rover_ws/tools/analyze_replay_coverage.py
        --incident incidents/<incident_id>
        [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _probe_common import ensure_app_on_path  # noqa: E402

ensure_app_on_path()

from app.replay_analytics.coverage import analyze_coverage  # noqa: E402
from app.replay_analytics.loader import load_replay_bundle  # noqa: E402
from app.replay_analytics.recommendations import (  # noqa: E402
    build_recommendations,
    detect_gaps,
)
from app.replay_analytics.reporting import render_per_incident_report_md  # noqa: E402
from app.replay_analytics.review_audit import (  # noqa: E402
    audit_review,
    write_review_audit_json,
    write_review_audit_md,
)
from app.replay_analytics.scoring import score_replay_quality  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--incident", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    bundle = load_replay_bundle(args.incident)
    if not bundle.has_replay_review:
        sys.stderr.write(
            f"replay-review bundle missing under {args.incident}\n"
            "Run rover_ws/tools/build_replay_review_bundle.py first.\n"
        )
    coverage = analyze_coverage(bundle)
    score = score_replay_quality(bundle=bundle, coverage=coverage)
    audit = audit_review(bundle)
    gaps = detect_gaps(bundle=bundle, coverage=coverage)
    recs = build_recommendations(bundle=bundle, gaps=gaps)

    target = args.incident
    target.mkdir(parents=True, exist_ok=True)
    (target / "replay-coverage.json").write_text(
        json.dumps(coverage.as_dict(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (target / "replay-quality-score.json").write_text(
        json.dumps(score.as_dict(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (target / "replay-gaps.json").write_text(
        json.dumps([g.as_dict() for g in gaps], indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (target / "replay-recommendations.json").write_text(
        json.dumps([r.as_dict() for r in recs], indent=2, sort_keys=True),
        encoding="utf-8",
    )
    write_review_audit_json(audit, path=target / "review-audit.json")
    write_review_audit_md(audit, path=target / "review-audit.md")
    md = render_per_incident_report_md(
        bundle=bundle,
        coverage=coverage,
        score=score,
        audit=audit,
        gaps=gaps,
        recommendations=recs,
    )
    (target / "replay-analytics.md").write_text(md, encoding="utf-8")
    payload = {
        "incident_id": bundle.incident_id,
        "score": score.as_dict(),
        "coverage": coverage.as_dict(),
        "audit": audit.as_dict(),
        "gaps": [g.as_dict() for g in gaps],
        "recommendations": [r.as_dict() for r in recs],
    }
    (target / "replay-analytics.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    if args.json:
        json.dump(payload, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print(
            f"replay-analytics {bundle.incident_id}: score={score.score} "
            f"coverage={score.coverage_status.value} "
            f"confidence={score.confidence} "
            f"bag={bundle.bag_status} review={audit.status.value} "
            f"gaps={len(gaps)}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
