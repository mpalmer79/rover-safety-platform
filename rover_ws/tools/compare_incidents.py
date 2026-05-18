#!/usr/bin/env python3
"""Compare two or more incident bundles.

Reads each bundle's ``incident-report.json`` and writes a comparison
under ``incidents/comparisons/<comparison_id>.{json,md}``.

Usage:
    rover_ws/tools/compare_incidents.py <bundle-dir> [<bundle-dir> ...]
        [--comparison-id <id>]
        [--out-dir incidents/comparisons]
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

from app.incident_analysis.compare import (  # noqa: E402
    compare_incidents,
    render_comparison_md as render_incident_comparison_md,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundles", type=Path, nargs="+")
    parser.add_argument(
        "--comparison-id",
        type=str,
        default="",
        help="comparison id; default: stamped timestamp",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("incidents/comparisons"),
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if len(args.bundles) < 2:
        parser.error("compare requires at least two bundle directories")
    cid = args.comparison_id or datetime.now(tz=timezone.utc).strftime(
        "comparison-%Y%m%dT%H%M%SZ"
    )

    comparison = compare_incidents(bundle_dirs=args.bundles, comparison_id=cid)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.out_dir / f"{cid}.json"
    md_path = args.out_dir / f"{cid}.md"
    json_path.write_text(
        json.dumps(comparison.as_dict(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    md_path.write_text(render_incident_comparison_md(comparison), encoding="utf-8")

    if args.json:
        json.dump(comparison.as_dict(), sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print(f"comparison {cid}: rows={len(comparison.rows)}")
        print(f"  json: {json_path}")
        print(f"  md:   {md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
