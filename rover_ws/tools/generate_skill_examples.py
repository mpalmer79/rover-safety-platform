#!/usr/bin/env python3
"""Regenerate the canonical Phase 15A skill authoring examples.

The platform is **not safety-certified**. This CLI walks every
canonical example (10 accepted, 9 rejected) and writes the audit
bundle under ``skill-library/``. It is deterministic; the output is
byte-stable across repeated runs against the same ``--generated-at``.

Usage:
    rover_ws/tools/generate_skill_examples.py
        [--examples-dir skill-library/examples]
        [--audits-dir skill-library/audits]
        [--rejected-dir skill-library/rejected]
        [--generated-at 2026-05-13T00:00:00+00:00]
        [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _probe_common import ensure_app_on_path  # noqa: E402

ensure_app_on_path()

from app.skill_authoring import (  # noqa: E402
    ACCEPTED_EXAMPLES,
    REJECTED_EXAMPLES,
    SKILL_AUTHORING_DISCLAIMER,
    SkillAuthoringRequest,
    generate_skill,
    write_audit_files,
)


_DEFAULT_TIMESTAMP = "2026-05-13T00:00:00+00:00"


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--examples-dir",
        type=Path,
        default=Path("skill-library/examples"),
    )
    p.add_argument(
        "--audits-dir",
        type=Path,
        default=Path("skill-library/audits"),
    )
    p.add_argument(
        "--rejected-dir",
        type=Path,
        default=Path("skill-library/rejected"),
    )
    p.add_argument("--generated-at", default=_DEFAULT_TIMESTAMP)
    p.add_argument("--json", action="store_true")
    return p.parse_args(argv)


def _write_example_payload(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    args.examples_dir.mkdir(parents=True, exist_ok=True)
    args.audits_dir.mkdir(parents=True, exist_ok=True)
    args.rejected_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []

    for example in ACCEPTED_EXAMPLES:
        request = SkillAuthoringRequest(
            request_id=example.example_id,
            text=example.text,
            language=example.language,
            requested_at_utc=args.generated_at,
        )
        result = generate_skill(request, generated_at_utc=args.generated_at)
        bundle = args.audits_dir / example.example_id
        _, paths = write_audit_files(result, bundle)
        _write_example_payload(
            args.examples_dir / f"{example.example_id}.json",
            {
                "example_id": example.example_id,
                "text": example.text,
                "language": example.language,
                "expected_status": example.expected_status,
                "notes": example.notes,
            },
        )
        rows.append(
            {
                "example_id": example.example_id,
                "kind": "accepted",
                "status": result.status,
                "rejection_reason": result.rejection_reason,
                "audit_bundle": str(bundle),
            }
        )

    for example in REJECTED_EXAMPLES:
        request = SkillAuthoringRequest(
            request_id=example.example_id,
            text=example.text,
            language=example.language,
            requested_at_utc=args.generated_at,
        )
        result = generate_skill(request, generated_at_utc=args.generated_at)
        bundle = args.rejected_dir / example.example_id
        _, paths = write_audit_files(result, bundle)
        rows.append(
            {
                "example_id": example.example_id,
                "kind": "rejected",
                "status": result.status,
                "rejection_reason": result.rejection_reason,
                "audit_bundle": str(bundle),
            }
        )

    summary = {
        "generated_at_utc": args.generated_at,
        "accepted_count": sum(1 for r in rows if r["kind"] == "accepted"),
        "rejected_count": sum(1 for r in rows if r["kind"] == "rejected"),
        "rows": rows,
        "disclaimer": SKILL_AUTHORING_DISCLAIMER,
    }
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(
            f"regenerated {summary['accepted_count']} accepted, "
            f"{summary['rejected_count']} rejected examples"
        )
        for row in rows:
            print(
                f"  - {row['example_id']:32s}  kind={row['kind']:8s}  "
                f"status={row['status']:18s}  reason={row['rejection_reason'] or '-'}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
