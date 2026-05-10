#!/usr/bin/env python3
"""Validate a Phase 11 reviewer-export bundle on disk.

Checks: manifest present + verbatim disclaimer; CSV / JSONL /
schema files present for every documented table; row counts match
the manifest; required fields present in the CSV header;
``causality_claimed`` is always ``false`` in subsystem_risk;
static-only / missing-bag flags are preserved in replay_quality;
notebook is valid JSON.

Usage:
    rover_ws/tools/validate_reviewer_export.py [--bundle reviewer-export] [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _probe_common import ensure_app_on_path  # noqa: E402

ensure_app_on_path()

from app.reviewer_exports import validate_export  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, default=Path("reviewer-export"))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    report = validate_export(args.bundle)
    payload = report.as_dict()
    if args.json:
        json.dump(payload, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print(f"reviewer-export-validation: passed={report.passed}")
        for r in report.results:
            mark = "OK" if r.passed else "FAIL"
            print(f"  [{mark}] {r.name}: {r.detail}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    sys.exit(main())
