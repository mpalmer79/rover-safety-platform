#!/usr/bin/env python3
"""Regenerate the canonical Phase 14B mission proposal examples.

The platform is **not safety-certified**. This CLI walks every
mock fixture, runs the proposal through the sanitizer + compiler,
and writes the canonical proposal JSON + audit bundle into
``mission-proposals/``. It is deterministic; the output is
byte-stable across repeated runs against the same ``--generated-at``.

Usage:
    rover_ws/tools/generate_mission_proposal_examples.py
        [--examples-dir mission-proposals/examples]
        [--audits-dir mission-proposals/audits]
        [--generated-at 2026-05-12T00:00:00+00:00]
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
    MISSION_PROPOSAL_DISCLAIMER,
    MockProposalProvider,
    list_mock_fixtures,
    run_adapter_pipeline,
    write_audit_files,
)


_DEFAULT_TIMESTAMP = "2026-05-12T00:00:00+00:00"


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--examples-dir",
        type=Path,
        default=Path("mission-proposals/examples"),
    )
    parser.add_argument(
        "--audits-dir",
        type=Path,
        default=Path("mission-proposals/audits"),
    )
    parser.add_argument(
        "--generated-at",
        default=_DEFAULT_TIMESTAMP,
        help="Deterministic ISO-8601 timestamp embedded in every audit",
    )
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def _proposal_to_payload(proposal) -> dict:
    return {
        "proposal_id": proposal.proposal_id,
        "source_text": proposal.source_text,
        "provider_name": proposal.provider_name,
        "provider_mode": proposal.provider_mode,
        "proposed_intent": proposal.proposed_intent,
        "proposed_location": proposal.proposed_location,
        "proposed_motion_style": proposal.proposed_motion_style,
        "proposed_constraints": list(proposal.proposed_constraints),
        "proposed_recovery_policy": proposal.proposed_recovery_policy,
        "confidence_label": proposal.confidence_label,
        "known_uncertainties": list(proposal.known_uncertainties),
        "raw_response": proposal.raw_response,
    }


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])

    args.examples_dir.mkdir(parents=True, exist_ok=True)
    args.audits_dir.mkdir(parents=True, exist_ok=True)

    provider = MockProposalProvider(use_fixtures=True)
    rows: list[dict] = []
    for fixture_id in list_mock_fixtures():
        # source_text is empty in fixture mode; the fixture id drives.
        proposal = provider.propose(
            source_text=fixture_id.replace("_", " "),
            proposal_id=fixture_id,
            options={"fixture_id": fixture_id},
        )
        example_path = args.examples_dir / f"{fixture_id}.json"
        example_path.write_text(
            json.dumps(_proposal_to_payload(proposal), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        adapter_result = run_adapter_pipeline(proposal, generated_at_utc=args.generated_at)
        bundle_dir = args.audits_dir / fixture_id
        audit, paths = write_audit_files(
            adapter_result, bundle_dir, generated_at_utc=args.generated_at
        )

        rows.append(
            {
                "fixture_id": fixture_id,
                "provider_mode": proposal.provider_mode,
                "sanitizer_status": adapter_result.sanitizer_result.status,
                "compiler_status": adapter_result.compiler_status,
                "final_outcome": adapter_result.final_outcome,
                "example_path": str(example_path),
                "audit_bundle": str(bundle_dir),
            }
        )

    summary = {
        "generated_at_utc": args.generated_at,
        "fixture_count": len(rows),
        "rows": rows,
        "disclaimer": MISSION_PROPOSAL_DISCLAIMER,
    }
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"regenerated {summary['fixture_count']} proposal examples")
        for row in rows:
            print(
                f"  - {row['fixture_id']:30s}  sanitizer={row['sanitizer_status']:10s}"
                f"  compiler={row['compiler_status'] or 'not_invoked':25s}"
                f"  outcome={row['final_outcome']}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
