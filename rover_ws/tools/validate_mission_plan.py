#!/usr/bin/env python3
"""Validate an existing compiled mission plan JSON file.

The platform is **not safety-certified**. The validator re-runs the
parser + compiler pipeline against the plan's recorded
``original_intent`` and confirms the resulting compile hash matches
the on-disk plan. This proves reproducibility and lets a reviewer
verify a plan came from a deterministic source.

Usage:
    rover_ws/tools/validate_mission_plan.py
        --plan mission-library/compiled/<plan_id>.json
        [--generated-at <iso8601>]
        [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _probe_common import ensure_app_on_path  # noqa: E402

ensure_app_on_path()

from app.natural_language_mission import compile_intent  # noqa: E402


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
    plan = compile_intent(
        payload["original_intent"],
        plan_id=payload["plan_id"],
        generated_at_utc=payload["generated_at_utc"],
        odd_profile_id=payload.get("odd_profile_id", "default-warehouse"),
    )
    ok = plan.compile_hash == payload.get("compile_hash")
    summary = {
        "plan_path": str(args.plan),
        "plan_id": plan.plan_id,
        "status": plan.status,
        "expected_hash": payload.get("compile_hash"),
        "recomputed_hash": plan.compile_hash,
        "reproducible": ok,
    }
    if args.json:
        json.dump(summary, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print(f"[{'OK' if ok else 'FAILED'}] {args.plan}")
        print(f"  expected_hash: {payload.get('compile_hash')}")
        print(f"  recomputed_hash: {plan.compile_hash}")
        print(f"  status: {plan.status}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
