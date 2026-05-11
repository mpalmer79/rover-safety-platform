"""Filesystem reporter for LLM candidate audit bundles.

Bundle layout
=============

For every pipeline run:

    <bundle_dir>/request.json
    <bundle_dir>/provider-result.json
    <bundle_dir>/sanitizer-result.json
    <bundle_dir>/validator-result.json
    <bundle_dir>/llm-candidate-report.md

When the provider produced a candidate:

    <bundle_dir>/candidate.json

When the candidate was fully accepted:

    <bundle_dir>/safety-review.json
    <bundle_dir>/code-card.json
"""

from __future__ import annotations

import json
from pathlib import Path

from .audit import (
    audit_to_dict,
    build_audit_bundle,
    render_llm_candidate_report_markdown,
)
from .models import (
    CandidateStatus,
    SkillLLMAuditBundle,
    SkillLLMGenerationResult,
)


def _dump_json(path: Path, payload) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_audit_files(
    result: SkillLLMGenerationResult,
    bundle_dir: Path,
    *,
    generated_at_utc: str | None = None,
) -> tuple[SkillLLMAuditBundle, dict]:
    bundle_dir = Path(bundle_dir)
    bundle_dir.mkdir(parents=True, exist_ok=True)

    audit = build_audit_bundle(result, generated_at_utc=generated_at_utc)
    audit_dict = audit_to_dict(audit)

    paths: dict[str, str] = {}

    request_path = bundle_dir / "request.json"
    provider_path = bundle_dir / "provider-result.json"
    sanitizer_path = bundle_dir / "sanitizer-result.json"
    validator_path = bundle_dir / "validator-result.json"
    report_path = bundle_dir / "llm-candidate-report.md"

    _dump_json(request_path, audit_dict["request"])
    _dump_json(provider_path, audit_dict["provider_result"])
    _dump_json(sanitizer_path, audit_dict["sanitizer_result"])
    _dump_json(validator_path, audit_dict["validator_result"])
    report_path.write_text(
        render_llm_candidate_report_markdown(audit), encoding="utf-8"
    )

    paths["request"] = str(request_path)
    paths["provider_result"] = str(provider_path)
    paths["sanitizer_result"] = str(sanitizer_path)
    paths["validator_result"] = str(validator_path)
    paths["llm_candidate_report"] = str(report_path)

    if audit_dict["candidate"] is not None:
        cand_path = bundle_dir / "candidate.json"
        _dump_json(cand_path, audit_dict["candidate"])
        paths["candidate"] = str(cand_path)

    if audit.final_status == CandidateStatus.ACCEPTED.value:
        if audit_dict["safety_review"] is not None:
            sr_path = bundle_dir / "safety-review.json"
            _dump_json(sr_path, audit_dict["safety_review"])
            paths["safety_review"] = str(sr_path)
        if audit_dict["code_card"] is not None:
            cc_path = bundle_dir / "code-card.json"
            _dump_json(cc_path, audit_dict["code_card"])
            paths["code_card"] = str(cc_path)

    return audit, paths
