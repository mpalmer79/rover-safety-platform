#!/usr/bin/env python3
"""Generate the Phase 11 reviewer-export package.

Bundles CSV + JSONL + JSON Schemas + a manifest + a reviewer
notebook + a reviewer summary into the requested output directory.

Usage:
    rover_ws/tools/generate_reviewer_export.py
        [--programme-review-root programme-review]
        [--incidents-root incidents]
        [--reliability-impact-root reliability-impact]
        [--traceability verification/traceability.json]
        [--output reviewer-export]
        [--export-id <id>]
        [--generated-at YYYY-MM-DDTHH:MM:SSZ]
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

from app.reviewer_exports import build_reviewer_export  # noqa: E402


def _parse_iso(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    try:
        ts = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise SystemExit(f"--generated-at must be ISO-8601 (got {value!r})")
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.isoformat(timespec="seconds")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--programme-review-root", type=Path, default=Path("programme-review")
    )
    parser.add_argument("--incidents-root", type=Path, default=Path("incidents"))
    parser.add_argument(
        "--reliability-impact-root",
        type=Path,
        default=Path("reliability-impact"),
    )
    parser.add_argument(
        "--traceability",
        type=Path,
        default=Path("verification/traceability.json"),
    )
    parser.add_argument("--output", type=Path, default=Path("reviewer-export"))
    parser.add_argument("--export-id", type=str, default=None)
    parser.add_argument("--generated-at", type=str, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    export = build_reviewer_export(
        bundle_dir=args.output,
        programme_review_root=args.programme_review_root,
        incidents_root=args.incidents_root,
        reliability_impact_root=args.reliability_impact_root,
        traceability_path=args.traceability,
        export_id=args.export_id,
        generated_at_utc=_parse_iso(args.generated_at),
    )

    if args.json:
        json.dump(export.as_dict(), sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print(
            f"reviewer-export {export.export_id}: tables={len(export.tables)} "
            f"warnings={len(export.warnings)}"
        )
        for table in export.tables:
            print(f"  {table.name:<25s} rows={len(table.rows)}")
        print(f"  output: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
