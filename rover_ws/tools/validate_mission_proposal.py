#!/usr/bin/env python3
"""Validate a proposal JSON against the Phase 14B proposal schema.

The platform is **not safety-certified**. This CLI checks the
structural shape of a proposal (required fields, enum membership)
and, when ``--run-sanitizer`` is supplied, runs the sanitizer
without invoking the compiler. It NEVER calls a remote API.

Usage:
    rover_ws/tools/validate_mission_proposal.py
        --proposal mission-proposals/examples/mock_valid_inspection.json
        [--run-sanitizer]
        [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _probe_common import ensure_app_on_path  # noqa: E402

ensure_app_on_path()

from app.mission_proposal import (  # noqa: E402
    sanitize_proposal,
    validate_proposal_dict,
)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proposal", type=Path, required=True)
    parser.add_argument("--run-sanitizer", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])

    try:
        payload = json.loads(args.proposal.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"proposal file not found: {args.proposal}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"proposal file is not valid JSON: {exc}", file=sys.stderr)
        return 2

    errors, proposal = validate_proposal_dict(payload)
    summary: dict = {
        "proposal_path": str(args.proposal),
        "valid": not errors,
        "errors": list(errors),
    }
    if not errors and proposal is not None and args.run_sanitizer:
        sanitizer_result = sanitize_proposal(proposal)
        summary["sanitizer"] = {
            "status": sanitizer_result.status,
            "accepted": sanitizer_result.accepted,
            "blocked_phrases": list(sanitizer_result.blocked_phrases),
            "diagnostics": [
                {
                    "code": d.code,
                    "severity": d.severity,
                    "message": d.message,
                    "matched_phrase": d.matched_phrase,
                }
                for d in sanitizer_result.diagnostics
            ],
            "notes": list(sanitizer_result.notes),
        }

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"valid: {summary['valid']}")
        for err in summary["errors"]:
            print(f"  - {err}")
        if "sanitizer" in summary:
            print(f"sanitizer: {summary['sanitizer']['status']}")
            for d in summary["sanitizer"]["diagnostics"]:
                print(f"  [{d['severity']}] {d['code']}: {d['message']}")

    return 0 if summary["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
