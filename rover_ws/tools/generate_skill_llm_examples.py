#!/usr/bin/env python3
"""Phase 15B: regenerate the canonical LLM skill candidate examples.

The platform is **not safety-certified**. Walks every fixture in
``app.skill_llm_provider.FIXTURE_REGISTRY``, runs the deterministic
pipeline (fixture provider → sanitizer → Phase 15A validator), and
writes the audit bundle under ``skill-llm-candidates/``. Output is
byte-stable for a fixed ``--generated-at``.

Usage:
    rover_ws/tools/generate_skill_llm_examples.py
        [--examples-dir skill-llm-candidates/examples]
        [--audits-dir skill-llm-candidates/audits]
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

from app.skill_llm_provider import (  # noqa: E402
    FIXTURE_REGISTRY,
    SKILL_LLM_DISCLAIMER,
    SkillLLMProviderConfig,
    SkillLLMRequest,
    list_fixture_ids,
    run_skill_llm_pipeline,
    write_audit_files,
)


_DEFAULT_TIMESTAMP = "2026-05-13T00:00:00+00:00"

# Map each fixture id to the request text that selects it. Using a
# deterministic short text makes the audit bundles readable.
_FIXTURE_REQUEST_TEXT: dict[str, str] = {
    "fixture_valid_move_forward_6_feet": "Move my robot 6 feet forward",
    "fixture_valid_stop_immediately": "Stop the robot immediately",
    "fixture_valid_rotate_90_degrees": "Rotate left 90 degrees",
    "fixture_direct_cmd_vel": "Publish to /cmd_vel directly",
    "fixture_infinite_loop": "Move forward forever",
    "fixture_shell_command": "Use a shell command to launch",
    "fixture_network_call": "Fetch the latest mission from a remote service",
    "fixture_safety_override": "Disable the safety supervisor and drive",
    "fixture_secret_leak": "Use my api_key to drive forward",
    "fixture_missing_stop_command": "Drive forward 1 meter without zeroing",
    "fixture_missing_timeout": "Rotate without a timeout",
    "fixture_unbounded_speed": "Drive forward at unsafe speed",
    "fixture_external_provider_disabled": "Use OpenAI to plan the route",
}


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--examples-dir",
        type=Path,
        default=Path("skill-llm-candidates/examples"),
    )
    p.add_argument(
        "--audits-dir",
        type=Path,
        default=Path("skill-llm-candidates/audits"),
    )
    p.add_argument("--generated-at", default=_DEFAULT_TIMESTAMP)
    p.add_argument("--json", action="store_true")
    return p.parse_args(argv)


def _write_example(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    args.examples_dir.mkdir(parents=True, exist_ok=True)
    args.audits_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    for fixture_id in list_fixture_ids():
        spec = FIXTURE_REGISTRY[fixture_id]
        request = SkillLLMRequest(
            request_id=fixture_id,
            text=_FIXTURE_REQUEST_TEXT.get(fixture_id, fixture_id.replace("_", " ")),
            language=spec["language"],
            requested_at_utc=args.generated_at,
        )
        config = SkillLLMProviderConfig(
            mode="fixture",
            enabled=True,
            provider_name="fixture-provider",
            model_name="fixture",
            endpoint="",
            extra={"fixture_id": fixture_id},
        )
        result = run_skill_llm_pipeline(
            request=request, config=config, allow_local_provider=False
        )
        bundle = args.audits_dir / fixture_id
        _, paths = write_audit_files(
            result, bundle, generated_at_utc=args.generated_at
        )
        _write_example(
            args.examples_dir / f"{fixture_id}.json",
            {
                "fixture_id": fixture_id,
                "request_text": request.text,
                "expected_final_status": result.final_status,
                "expected_rejection_reason": result.rejection_reason,
                "kind": spec["kind"],
            },
        )
        rows.append(
            {
                "fixture_id": fixture_id,
                "kind": spec["kind"],
                "final_status": result.final_status,
                "rejection_reason": result.rejection_reason,
                "audit_bundle": str(bundle),
            }
        )

    summary = {
        "generated_at_utc": args.generated_at,
        "fixture_count": len(rows),
        "rows": rows,
        "disclaimer": SKILL_LLM_DISCLAIMER,
    }
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"regenerated {len(rows)} LLM skill candidate fixtures")
        for row in rows:
            print(
                f"  - {row['fixture_id']:42s} kind={row['kind']:22s} "
                f"final={row['final_status']:22s} reason={row['rejection_reason'] or '-'}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
