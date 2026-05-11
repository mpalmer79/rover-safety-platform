#!/usr/bin/env python3
"""Generate the audit artefact (JSON + Markdown) for a compiled mission plan.

The platform is **not safety-certified**.

Usage:
    rover_ws/tools/generate_mission_audit.py
        --plan mission-library/compiled/<plan_id>.json
        [--out-dir mission-library/audits]
        [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _probe_common import ensure_app_on_path  # noqa: E402

ensure_app_on_path()

from app.natural_language_mission import (  # noqa: E402
    build_audit,
    compile_intent,
    render_audit_markdown,
    write_audit,
)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=Path("mission-library/audits"))
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
    args.out_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.out_dir / f"{plan.plan_id}-audit.json"
    md_path = args.out_dir / f"{plan.plan_id}-audit.md"
    audit = write_audit(plan, json_path=json_path, md_path=md_path)
    if args.json:
        json.dump(audit, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print(f"plan_id: {plan.plan_id}")
        print(f"status: {plan.status}")
        print(f"compile_hash: {plan.compile_hash}")
        print(f"audit json: {json_path}")
        print(f"audit md: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
