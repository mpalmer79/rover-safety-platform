#!/usr/bin/env python3
"""Phase 15B: propose a robotics skill candidate via a local LLM provider.

The platform is **not safety-certified**. This CLI is disabled by
default. It NEVER calls a cloud API, NEVER executes generated code,
and NEVER publishes to ROS. Local providers (``local_http``,
``ollama``, ``llama_cpp``) require BOTH ``--allow-local-provider``
AND an enabled provider config; even then, Phase 15B does not open
a network socket — providers return a deterministic
``not_configured`` envelope so the operator can audit the intended
opt-in path without running a model.

Usage:
    rover_ws/tools/propose_robotics_skill_with_local_llm.py
        --text "What code moves my robot 6 feet forward?"
        --provider disabled|fixture|local_http|ollama|llama_cpp
        --output skill-llm-candidates/audits/<id>
        [--config <path>]
        [--fixture-id fixture_valid_move_forward_6_feet]
        [--request-id move_forward_6_feet]
        [--language python_ros2]
        [--allow-local-provider]
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

from app.skill_llm_provider import (  # noqa: E402
    DEFAULT_PROVIDER_MODE,
    KNOWN_PROVIDER_MODES,
    PROVIDER_MODES,
    SKILL_LLM_DISCLAIMER,
    SkillLLMProviderConfig,
    SkillLLMRequest,
    load_provider_config,
    parse_provider_config,
    run_skill_llm_pipeline,
    write_audit_files,
)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--text", required=True)
    p.add_argument(
        "--provider",
        default=DEFAULT_PROVIDER_MODE,
        choices=list(KNOWN_PROVIDER_MODES),
    )
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--config", type=Path, default=None)
    p.add_argument("--fixture-id", default=None)
    p.add_argument("--request-id", default="")
    p.add_argument("--language", default="python_ros2")
    p.add_argument("--allow-local-provider", action="store_true")
    p.add_argument("--generated-at", default=None)
    p.add_argument("--json", action="store_true")
    return p.parse_args(argv)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _build_config(args: argparse.Namespace) -> SkillLLMProviderConfig:
    if args.config is not None and args.config.is_file():
        config = load_provider_config(args.config)
        # CLI --provider overrides config.mode for the operator's clarity.
        if config.mode != args.provider:
            config = SkillLLMProviderConfig(
                mode=args.provider,
                enabled=config.enabled,
                provider_name=config.provider_name,
                model_name=config.model_name,
                endpoint=config.endpoint,
                extra=config.extra,
                notes=config.notes,
            )
    else:
        config = parse_provider_config(
            {
                "mode": args.provider,
                "enabled": args.provider == "fixture",
                "provider_name": f"{args.provider}-provider",
                "model_name": "",
                "endpoint": "",
                "extra": {},
            }
        )
    if args.fixture_id:
        extra = dict(config.extra)
        extra["fixture_id"] = args.fixture_id
        config = SkillLLMProviderConfig(
            mode=config.mode,
            enabled=config.enabled,
            provider_name=config.provider_name,
            model_name=config.model_name,
            endpoint=config.endpoint,
            extra=extra,
            notes=config.notes,
        )
    return config


def _resolve_request_id(explicit: str, output: Path) -> str:
    if explicit:
        return explicit
    if output.name and output.name not in (".", ""):
        return output.name
    return "candidate-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    timestamp = args.generated_at or _now_iso()
    request = SkillLLMRequest(
        request_id=_resolve_request_id(args.request_id, args.output),
        text=args.text,
        language=args.language,
        requested_at_utc=timestamp,
    )

    try:
        config = _build_config(args)
    except ValueError as exc:
        print(f"provider config error: {exc}", file=sys.stderr)
        return 2

    result = run_skill_llm_pipeline(
        request=request,
        config=config,
        allow_local_provider=args.allow_local_provider,
    )
    audit, paths = write_audit_files(
        result, args.output, generated_at_utc=timestamp
    )

    summary = {
        "request_id": request.request_id,
        "provider_mode": result.provider_result.provider_mode,
        "provider_status": result.provider_result.status,
        "final_status": result.final_status,
        "rejection_reason": result.rejection_reason,
        "sanitizer_accepted": result.sanitizer_result.accepted,
        "validator_invoked": result.validator_result.invoked,
        "validator_accepted": result.validator_result.accepted,
        "paths": paths,
        "disclaimer": SKILL_LLM_DISCLAIMER,
        "generated_at_utc": timestamp,
    }
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"request_id:        {summary['request_id']}")
        print(f"provider_mode:     {summary['provider_mode']}")
        print(f"provider_status:   {summary['provider_status']}")
        print(f"final_status:      {summary['final_status']}")
        if summary["rejection_reason"]:
            print(f"rejection_reason:  {summary['rejection_reason']}")
        for label, path in paths.items():
            print(f"  wrote {label}: {path}")

    return 0 if result.accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
