#!/usr/bin/env python3
"""Generate the Phase 13 live-runtime maturity report.

Aggregates every ``evidence/runtime/<run_id>/`` bundle into a
single JSON + Markdown report that summarises live-runtime status
honestly:

* runs total, runs by status,
* bag counters (bag_backed / missing_bag / partial / not_executed /
  invalid),
* required-topic and scenario coverage,
* runner status (qualified / partial / not_qualified / unknown),
* downstream pipeline integration status,
* known limitations and next actions.

Usage:
    rover_ws/tools/generate_live_runtime_maturity_report.py
        [--evidence-root evidence/runtime]
        [--incidents-root incidents]
        [--analytics-root incidents/analytics]
        [--programme-review-root programme-review]
        [--reviewer-export-root reviewer-export]
        [--out-json live-runtime/live-runtime-maturity.json]
        [--out-md docs/LIVE_RUNTIME_MATURITY_REPORT.md]
        [--reference-time <iso8601>]
        [--json]

The platform is **not safety-certified**.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from _probe_common import ensure_app_on_path  # noqa: E402

ensure_app_on_path()

from app.live_runtime import (  # noqa: E402
    aggregate_maturity,
    maturity_report_to_dict,
    write_maturity_json,
    write_maturity_markdown,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--evidence-root", type=Path, default=Path("evidence/runtime"))
    parser.add_argument("--incidents-root", type=Path, default=Path("incidents"))
    parser.add_argument("--analytics-root", type=Path, default=Path("incidents/analytics"))
    parser.add_argument(
        "--programme-review-root", type=Path, default=Path("programme-review")
    )
    parser.add_argument(
        "--reviewer-export-root", type=Path, default=Path("reviewer-export")
    )
    parser.add_argument(
        "--out-json", type=Path, default=Path("live-runtime/live-runtime-maturity.json")
    )
    parser.add_argument(
        "--out-md", type=Path, default=Path("docs/LIVE_RUNTIME_MATURITY_REPORT.md")
    )
    parser.add_argument("--reference-time", type=str, default=None)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(list(argv) if argv is not None else sys.argv[1:])
    generated_at = args.reference_time or _now_iso()
    report = aggregate_maturity(
        evidence_root=args.evidence_root,
        incidents_root=args.incidents_root,
        replay_analytics_root=args.analytics_root,
        programme_review_root=args.programme_review_root,
        reviewer_export_root=args.reviewer_export_root,
        generated_at_utc=generated_at,
    )
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    write_maturity_json(report, args.out_json)
    write_maturity_markdown(report, args.out_md)

    if args.json:
        json.dump(maturity_report_to_dict(report), sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print(f"runs_total: {report.runs_total}")
        print(f"latest_run: {report.latest_run_id} ({report.latest_run_status})")
        print(f"runner_status: {report.runner_status}")
        print(f"bag_backed: {report.bag_counters.bag_backed}")
        print(f"missing_bag: {report.bag_counters.missing_bag}")
        print(f"not_executed: {report.bag_counters.not_executed}")
        print(f"json: {args.out_json}")
        print(f"markdown: {args.out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
