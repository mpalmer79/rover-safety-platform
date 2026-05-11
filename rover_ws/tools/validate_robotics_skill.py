#!/usr/bin/env python3
"""Validate a generated robotics skill JSON against the safety rules.

The platform is **not safety-certified**. This CLI re-runs the
deterministic safety validator over a generated skill bundle so a
reviewer can confirm that the skill on disk still meets the
documented honesty rules (uses /cmd_vel_requested, bounded loop,
contains stop command, mentions safety supervisor, no shell or
network access).

Usage:
    rover_ws/tools/validate_robotics_skill.py
        --skill skill-library/audits/move_forward_6_feet/generated-skill.json
        [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _probe_common import ensure_app_on_path  # noqa: E402

ensure_app_on_path()

from app.skill_authoring.validator import (  # noqa: E402
    REQUIRED_CODE_TOKENS,
    validate_generated_code,
)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--skill", required=True, type=Path)
    p.add_argument("--json", action="store_true")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    try:
        payload = json.loads(args.skill.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"skill file not found: {args.skill}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"skill file is not valid JSON: {exc}", file=sys.stderr)
        return 2

    skill_type = str(payload.get("skill_type") or "")
    code = str(payload.get("code") or "")
    if not skill_type or not code:
        print("skill payload missing skill_type or code", file=sys.stderr)
        return 2

    diagnostics = validate_generated_code(code, skill_type)
    summary = {
        "skill_path": str(args.skill),
        "skill_type": skill_type,
        "required_tokens": list(REQUIRED_CODE_TOKENS.get(skill_type, ())),
        "valid": not diagnostics,
        "diagnostics": [
            {
                "code": d.code,
                "severity": d.severity,
                "message": d.message,
                "parameter": d.parameter,
            }
            for d in diagnostics
        ],
    }
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"valid: {summary['valid']}")
        for d in summary["diagnostics"]:
            print(f"  [{d['severity']}] {d['code']}: {d['message']}")
    return 0 if summary["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
