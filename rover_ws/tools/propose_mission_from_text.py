#!/usr/bin/env python3
"""Run a natural-language proposal through the Phase 14B pipeline.

The platform is **not safety-certified**. This CLI is the operator
entry point to the offline pluggable LLM proposal layer. It NEVER
executes user intent, NEVER authorises motion, and NEVER calls a
remote API. External provider modes are intentionally disabled in
Phase 14B.

Usage:
    rover_ws/tools/propose_mission_from_text.py
        --text "Inspect loading_zone_two slowly"
        --provider mock
        --proposal-id p-001
        --output mission-proposals/audits/p-001
        [--fixture-id mock_valid_inspection]
        [--generated-at <iso8601>]
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

from app.mission_proposal import (  # noqa: E402
    AdapterResult,
    MISSION_PROPOSAL_DISCLAIMER,
    MockProposalProvider,
    ProposalProviderError,
    PROVIDER_MODES,
    PROVIDER_MODE_EXTERNAL_DISABLED,
    PROVIDER_MODE_MOCK,
    PROVIDER_MODE_OFFLINE_FIXTURE,
    external_provider_disabled_response,
    resolve_provider,
    run_adapter_pipeline,
    write_audit_files,
)
from app.mission_proposal.audit import build_audit, write_audit_bundle


_EXTERNAL_ALIASES: tuple[str, ...] = (
    "external",
    "openai",
    "anthropic",
    "cohere",
    "external-disabled",
    "external_disabled",
)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text", required=True, help="Natural-language request")
    parser.add_argument(
        "--provider",
        default=PROVIDER_MODE_MOCK,
        help=(
            "Provider mode. One of mock / offline_fixture; any other "
            "value returns the deterministic external-disabled response."
        ),
    )
    parser.add_argument("--proposal-id", default="", help="Proposal identifier")
    parser.add_argument(
        "--fixture-id",
        default=None,
        help="Optional fixture id (offline_fixture mode)",
    )
    parser.add_argument("--output", type=Path, required=True, help="Audit bundle directory")
    parser.add_argument(
        "--generated-at",
        default=None,
        help="ISO-8601 timestamp; defaults to current UTC",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON status to stdout")
    return parser.parse_args(argv)


def _resolve_proposal_id(explicit: str, output: Path) -> str:
    if explicit:
        return explicit
    if output.name and output.name not in (".", ""):
        return output.name
    return "proposal-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _emit_external_disabled(
    args: argparse.Namespace,
) -> int:
    payload = external_provider_disabled_response(
        source_text=args.text,
        proposal_id=_resolve_proposal_id(args.proposal_id, args.output),
    )
    args.output.mkdir(parents=True, exist_ok=True)
    out_path = args.output / "provider-disabled.json"
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"provider disabled: {payload['reason']}")
        print(f"  proposal_id: {payload['proposal_id']}")
        print(f"  wrote {out_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])

    provider_mode = args.provider
    if provider_mode in _EXTERNAL_ALIASES:
        provider_mode = PROVIDER_MODE_EXTERNAL_DISABLED

    if provider_mode not in PROVIDER_MODES:
        print(
            f"unsupported provider mode {provider_mode!r}; expected one of "
            f"{PROVIDER_MODES} or one of {_EXTERNAL_ALIASES}",
            file=sys.stderr,
        )
        return 2

    if provider_mode == PROVIDER_MODE_EXTERNAL_DISABLED:
        return _emit_external_disabled(args)

    try:
        provider = resolve_provider(provider_mode)
    except ProposalProviderError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if provider is None:
        # Should not happen — only external_disabled returns None.
        return _emit_external_disabled(args)

    proposal_id = _resolve_proposal_id(args.proposal_id, args.output)
    options: dict = {}
    if args.fixture_id:
        options["fixture_id"] = args.fixture_id

    proposal = provider.propose(
        source_text=args.text,
        proposal_id=proposal_id,
        options=options,
    )

    timestamp = args.generated_at or _now_iso()
    adapter_result: AdapterResult = run_adapter_pipeline(
        proposal, generated_at_utc=timestamp
    )
    audit, paths = write_audit_files(
        adapter_result, args.output, generated_at_utc=timestamp
    )

    summary = {
        "proposal_id": proposal.proposal_id,
        "provider_name": proposal.provider_name,
        "provider_mode": proposal.provider_mode,
        "sanitizer_status": adapter_result.sanitizer_result.status,
        "compiler_status": adapter_result.compiler_status,
        "final_outcome": adapter_result.final_outcome,
        "disclaimer": MISSION_PROPOSAL_DISCLAIMER,
        "paths": paths,
        "generated_at_utc": timestamp,
    }

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"proposal_id: {summary['proposal_id']}")
        print(f"provider:    {summary['provider_name']} ({summary['provider_mode']})")
        print(f"sanitizer:   {summary['sanitizer_status']}")
        print(f"compiler:    {summary['compiler_status'] or 'not_invoked'}")
        print(f"outcome:     {summary['final_outcome']}")
        for label, path in paths.items():
            print(f"  wrote {label}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
