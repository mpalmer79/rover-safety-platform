#!/usr/bin/env python3
"""Phase 15B: re-run sanitizer + validator on a candidate JSON.

The platform is **not safety-certified**. This CLI takes a stored
``candidate.json`` (the structured payload the LLM provider
returned) and re-runs the deterministic sanitizer and the Phase 15A
skill validator. It NEVER executes the candidate code.

Usage:
    rover_ws/tools/validate_skill_llm_candidate.py
        --candidate skill-llm-candidates/audits/<id>/candidate.json
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
    SkillLLMCandidate,
    sanitize_candidate,
)
from app.skill_llm_provider.validator_bridge import (  # noqa: E402
    run_skill_validator_bridge,
)


def _str_tuple(value) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, (list, tuple)):
        return tuple(str(v) for v in value)
    return ()


def _candidate_from_dict(payload) -> SkillLLMCandidate:
    return SkillLLMCandidate(
        candidate_id=str(payload.get("candidate_id") or ""),
        source_text=str(payload.get("source_text") or ""),
        provider_mode=str(payload.get("provider_mode") or ""),
        provider_name=str(payload.get("provider_name") or ""),
        model_name=str(payload.get("model_name") or ""),
        language=str(payload.get("language") or "python_ros2"),
        skill_type=str(payload.get("skill_type") or ""),
        code=str(payload.get("code") or ""),
        explanation=str(payload.get("explanation") or ""),
        declared_topics=_str_tuple(payload.get("declared_topics")),
        declared_interfaces=_str_tuple(payload.get("declared_interfaces")),
        declared_safety_constraints=_str_tuple(
            payload.get("declared_safety_constraints")
        ),
        confidence_label=str(payload.get("confidence_label") or "medium"),
        known_uncertainties=_str_tuple(payload.get("known_uncertainties")),
        raw_provider_payload=str(payload.get("raw_provider_payload") or ""),
    )


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--candidate", required=True, type=Path)
    p.add_argument("--json", action="store_true")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    try:
        payload = json.loads(args.candidate.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"candidate file not found: {args.candidate}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"candidate file is not valid JSON: {exc}", file=sys.stderr)
        return 2

    candidate = _candidate_from_dict(payload)
    sanitizer_result = sanitize_candidate(candidate)
    validator_result, safety_review, code_card = run_skill_validator_bridge(
        candidate, sanitizer_result
    )

    summary = {
        "candidate_id": candidate.candidate_id,
        "sanitizer": {
            "status": sanitizer_result.status,
            "accepted": sanitizer_result.accepted,
            "reason_codes": list(sanitizer_result.reason_codes),
            "blocked_fragments": list(sanitizer_result.blocked_fragments),
            "notes": list(sanitizer_result.notes),
        },
        "validator": {
            "invoked": validator_result.invoked,
            "accepted": validator_result.accepted,
            "skill_type": validator_result.skill_type,
            "safety_status": validator_result.safety_status,
            "diagnostics": [dict(d) for d in validator_result.diagnostics],
        },
        "code_card": dict(code_card) if code_card is not None else None,
        "safety_review": dict(safety_review) if safety_review is not None else None,
    }
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"sanitizer accepted: {sanitizer_result.accepted}")
        print(f"validator invoked:  {validator_result.invoked}")
        print(f"validator accepted: {validator_result.accepted}")
        for d in validator_result.diagnostics:
            if isinstance(d, dict):
                print(f"  [{d.get('severity')}] {d.get('code')}: {d.get('message')}")

    if not sanitizer_result.accepted or not validator_result.accepted:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
