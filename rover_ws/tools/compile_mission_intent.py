#!/usr/bin/env python3
"""Compile a natural language mission intent into a candidate mission plan.

The platform is **not safety-certified**. This CLI is the operator
entry point to the Phase 14A deterministic mission compiler. It
NEVER executes user intent and NEVER authorises motion.

Usage:
    rover_ws/tools/compile_mission_intent.py
        --intent "<natural language>"
        [--intent-file <path>]
        [--plan-id <id>]
        [--odd-profile <profile_id>]
        [--generated-at <iso8601>]
        [--out-dir mission-library/compiled]
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

from app.natural_language_mission import (  # noqa: E402
    DEFAULT_ODD_PROFILE_ID,
    compile_intent,
    plan_to_dict,
    write_plan,
    write_replay_binding,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--intent", type=str, default=None)
    parser.add_argument("--intent-file", type=Path, default=None)
    parser.add_argument("--plan-id", type=str, default="mission-cli")
    parser.add_argument("--odd-profile", type=str, default=DEFAULT_ODD_PROFILE_ID)
    parser.add_argument("--generated-at", type=str, default=None)
    parser.add_argument("--out-dir", type=Path, default=Path("mission-library/compiled"))
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(list(argv) if argv is not None else sys.argv[1:])
    if args.intent_file:
        text = args.intent_file.read_text(encoding="utf-8")
    elif args.intent:
        text = args.intent
    else:
        print("error: --intent or --intent-file is required", file=sys.stderr)
        return 2

    generated_at = args.generated_at or _now_iso()
    plan = compile_intent(
        text,
        plan_id=args.plan_id,
        generated_at_utc=generated_at,
        odd_profile_id=args.odd_profile,
    )

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{args.plan_id}.json"
    md_path = out_dir / f"{args.plan_id}.md"
    binding_path = out_dir / f"{args.plan_id}-replay-binding.json"
    write_plan(plan, json_path=json_path, md_path=md_path)
    write_replay_binding(plan, binding_path)

    if args.json:
        json.dump(plan_to_dict(plan), sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print(f"plan_id: {plan.plan_id}")
        print(f"status: {plan.status}")
        print(f"risk: {plan.risk.band} (score {plan.risk.score})")
        print(f"objectives: {len(plan.objectives)}")
        print(f"constraints: {len(plan.constraints)}")
        print(f"diagnostics: {len(plan.diagnostics)}")
        print(f"compile_hash: {plan.compile_hash}")
        print(f"json: {json_path}")
        print(f"md: {md_path}")
        print(f"replay binding: {binding_path}")
    # Non-zero only on hard failure; rejection is an honest outcome.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
