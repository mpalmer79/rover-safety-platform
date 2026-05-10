#!/usr/bin/env python3
"""Reliability impact CI gate.

Reads an existing reliability-impact bundle (``impact-report.json``
+ ``gate-decision.json``) and prints / emits the gate decision. The
gate exit code is:

* ``0`` — ``passed`` or ``warning``;
* ``1`` — ``failed``.

By design the gate **never** fails for missing live runtime
evidence on a github-hosted runner; the documented failure
conditions are enforced by
:mod:`app.reliability_impact.ci_gate`. This CLI is the thin wrapper
that surfaces them in CI.

Usage:
    rover_ws/tools/reliability_impact_gate.py
        [--report reliability-impact/impact-report.json]
        [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _probe_common import ensure_app_on_path  # noqa: E402

ensure_app_on_path()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("reliability-impact/impact-report.json"),
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if not args.report.exists():
        sys.stderr.write(
            f"impact report not found: {args.report}\n"
            "Run rover_ws/tools/analyze_source_impact.py first.\n"
        )
        return 1
    try:
        payload = json.loads(args.report.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"impact report did not parse: {exc}\n")
        return 1

    gate = payload.get("gate_decision") or {}
    status = gate.get("status", "not_executed")
    failures = list(gate.get("failures") or [])
    warnings = list(gate.get("warnings") or [])
    notes = list(gate.get("notes") or [])

    out = {
        "status": status,
        "failures": failures,
        "warnings": warnings,
        "notes": notes,
    }
    if args.json:
        json.dump(out, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print(f"reliability-impact-gate: status={status}")
        for f in failures:
            print(f"  FAIL: {f}")
        for w in warnings:
            print(f"  WARN: {w}")
        for n in notes:
            print(f"  NOTE: {n}")

    return 0 if status != "failed" else 1


if __name__ == "__main__":
    sys.exit(main())
