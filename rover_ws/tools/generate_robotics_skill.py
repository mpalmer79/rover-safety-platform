#!/usr/bin/env python3
"""Generate a deterministic robotics skill bundle from a developer request.

The platform is **not safety-certified**. This CLI is the operator
entry point to the Phase 15A robotics skill authoring workbench.
It NEVER executes user intent, NEVER publishes to ROS topics,
NEVER calls a remote API, and NEVER generates code that bypasses
the safety supervisor's authority.

Usage:
    rover_ws/tools/generate_robotics_skill.py
        --text "What code do I need to move my robot 6 feet forward?"
        --language python_ros2
        --output skill-library/audits/move_forward_6_feet
        [--request-id move_forward_6_feet]
        [--generated-at 2026-05-13T00:00:00+00:00]
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

from app.skill_authoring import (  # noqa: E402
    SKILL_AUTHORING_DISCLAIMER,
    SkillAuthoringRequest,
    SkillLanguage,
    generate_skill,
    write_audit_files,
)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--text", required=True, help="Natural-language developer request")
    p.add_argument(
        "--language",
        default=SkillLanguage.PYTHON_ROS2.value,
        choices=[s.value for s in SkillLanguage],
    )
    p.add_argument("--output", required=True, type=Path, help="Audit bundle directory")
    p.add_argument("--request-id", default="", help="Request identifier")
    p.add_argument(
        "--generated-at",
        default=None,
        help="ISO-8601 timestamp; defaults to current UTC",
    )
    p.add_argument("--json", action="store_true")
    return p.parse_args(argv)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _resolve_request_id(explicit: str, output: Path) -> str:
    if explicit:
        return explicit
    if output.name and output.name not in (".", ""):
        return output.name
    return "skill-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    request = SkillAuthoringRequest(
        request_id=_resolve_request_id(args.request_id, args.output),
        text=args.text,
        language=args.language,
        requested_at_utc=args.generated_at or _now_iso(),
    )
    timestamp = args.generated_at or _now_iso()
    result = generate_skill(request, generated_at_utc=timestamp)
    audit, paths = write_audit_files(result, args.output)

    summary = {
        "request_id": request.request_id,
        "status": result.status,
        "rejection_reason": result.rejection_reason,
        "skill_type": (
            result.generated_skill.skill_type if result.generated_skill else None
        ),
        "language": (
            result.generated_skill.language if result.generated_skill else request.language
        ),
        "title": result.generated_skill.title if result.generated_skill else "",
        "paths": paths,
        "disclaimer": SKILL_AUTHORING_DISCLAIMER,
        "generated_at_utc": timestamp,
    }
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"request_id: {summary['request_id']}")
        print(f"status:     {summary['status']}")
        if summary["rejection_reason"]:
            print(f"reason:     {summary['rejection_reason']}")
        if summary["skill_type"]:
            print(f"skill_type: {summary['skill_type']}")
            print(f"title:      {summary['title']}")
        for label, path in paths.items():
            print(f"  wrote {label}: {path}")
    return 0 if summary["status"] == "generated" else 1


if __name__ == "__main__":
    raise SystemExit(main())
