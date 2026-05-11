#!/usr/bin/env python3
"""Render the explainability chain of a compiled mission plan.

The platform is **not safety-certified**.

Usage:
    rover_ws/tools/explain_mission_plan.py
        --plan mission-library/compiled/<plan_id>.json
        [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _probe_common import ensure_app_on_path  # noqa: E402

ensure_app_on_path()


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(list(argv) if argv is not None else sys.argv[1:])
    if not args.plan.is_file():
        print(f"error: plan not found: {args.plan}", file=sys.stderr)
        return 2
    payload = json.loads(args.plan.read_text(encoding="utf-8"))
    chain = payload.get("explainability_chain", []) or []
    if args.json:
        json.dump(
            {
                "plan_id": payload.get("plan_id"),
                "status": payload.get("status"),
                "chain": list(chain),
            },
            sys.stdout,
            indent=2,
            sort_keys=True,
        )
        sys.stdout.write("\n")
    else:
        print(f"plan_id: {payload.get('plan_id')}")
        print(f"status: {payload.get('status')}")
        print("explainability chain:")
        for line in chain:
            print(f"  - {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
