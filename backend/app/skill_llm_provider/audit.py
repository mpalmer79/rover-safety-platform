"""Audit bundle builder + Markdown renderer."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Mapping

from .models import (
    CandidateStatus,
    SKILL_LLM_DISCLAIMER,
    SKILL_LLM_PROVIDER_VERSION,
    SkillLLMAuditBundle,
    SkillLLMCandidate,
    SkillLLMGenerationResult,
    SkillLLMProviderResult,
    SkillLLMRequest,
    SkillLLMSanitizerResult,
    SkillLLMValidationResult,
)


def _request_to_dict(req: SkillLLMRequest) -> dict:
    return {
        "request_id": req.request_id,
        "text": req.text,
        "language": req.language,
        "requested_at_utc": req.requested_at_utc,
    }


def _provider_result_to_dict(pr: SkillLLMProviderResult) -> dict:
    payload = dict(pr.payload) if pr.payload else None
    if payload is not None:
        # Coerce lists for JSON stability.
        for key in (
            "declared_topics",
            "declared_interfaces",
            "declared_safety_constraints",
            "known_uncertainties",
        ):
            if key in payload and isinstance(payload[key], tuple):
                payload[key] = list(payload[key])
    return {
        "status": pr.status,
        "provider_mode": pr.provider_mode,
        "provider_name": pr.provider_name,
        "model_name": pr.model_name,
        "reason": pr.reason,
        "payload": payload,
    }


def _candidate_to_dict(c: SkillLLMCandidate | None) -> dict | None:
    if c is None:
        return None
    return {
        "candidate_id": c.candidate_id,
        "source_text": c.source_text,
        "provider_mode": c.provider_mode,
        "provider_name": c.provider_name,
        "model_name": c.model_name,
        "language": c.language,
        "skill_type": c.skill_type,
        "code": c.code,
        "explanation": c.explanation,
        "declared_topics": list(c.declared_topics),
        "declared_interfaces": list(c.declared_interfaces),
        "declared_safety_constraints": list(c.declared_safety_constraints),
        "confidence_label": c.confidence_label,
        "known_uncertainties": list(c.known_uncertainties),
        "raw_provider_payload": c.raw_provider_payload,
    }


def _sanitizer_to_dict(s: SkillLLMSanitizerResult) -> dict:
    return {
        "status": s.status,
        "accepted": s.accepted,
        "reason_codes": list(s.reason_codes),
        "blocked_fragments": list(s.blocked_fragments),
        "notes": list(s.notes),
        "human_review_required": s.human_review_required,
    }


def _validator_to_dict(v: SkillLLMValidationResult) -> dict:
    return {
        "invoked": v.invoked,
        "accepted": v.accepted,
        "diagnostics": [dict(d) for d in v.diagnostics],
        "skill_type": v.skill_type,
        "safety_status": v.safety_status,
    }


def build_audit_bundle(
    result: SkillLLMGenerationResult, *, generated_at_utc: str | None = None
) -> SkillLLMAuditBundle:
    timestamp = generated_at_utc or datetime.now(timezone.utc).replace(
        microsecond=0
    ).isoformat()
    return SkillLLMAuditBundle(
        request=result.request,
        provider_result=result.provider_result,
        candidate=result.candidate,
        sanitizer_result=result.sanitizer_result,
        validator_result=result.validator_result,
        safety_review=result.safety_review,
        code_card=result.code_card,
        final_status=result.final_status,
        rejection_reason=result.rejection_reason,
        generated_at_utc=timestamp,
        disclaimer=SKILL_LLM_DISCLAIMER,
    )


def audit_to_dict(audit: SkillLLMAuditBundle) -> dict:
    return {
        "skill_llm_provider_version": SKILL_LLM_PROVIDER_VERSION,
        "request": _request_to_dict(audit.request),
        "provider_result": _provider_result_to_dict(audit.provider_result),
        "candidate": _candidate_to_dict(audit.candidate),
        "sanitizer_result": _sanitizer_to_dict(audit.sanitizer_result),
        "validator_result": _validator_to_dict(audit.validator_result),
        "safety_review": dict(audit.safety_review) if audit.safety_review else None,
        "code_card": dict(audit.code_card) if audit.code_card else None,
        "final_status": audit.final_status,
        "rejection_reason": audit.rejection_reason,
        "generated_at_utc": audit.generated_at_utc,
        "disclaimer": audit.disclaimer,
    }


def render_llm_candidate_report_markdown(audit: SkillLLMAuditBundle) -> str:
    lines: list[str] = []
    lines.append(f"# LLM skill candidate audit: {audit.request.request_id or 'anon'}")
    lines.append("")
    lines.append(f"_{audit.disclaimer}_")
    lines.append("")
    lines.append(f"- **Provider mode:** `{audit.provider_result.provider_mode}`")
    lines.append(f"- **Provider name:** `{audit.provider_result.provider_name}`")
    lines.append(f"- **Provider status:** `{audit.provider_result.status}`")
    lines.append(f"- **Final status:** `{audit.final_status}`")
    if audit.rejection_reason:
        lines.append(f"- **Rejection reason:** `{audit.rejection_reason}`")
    lines.append(f"- **Generated (UTC):** {audit.generated_at_utc}")
    lines.append("")
    lines.append("## Request")
    lines.append("")
    lines.append("```text")
    lines.append(audit.request.text)
    lines.append("```")
    lines.append("")

    if audit.candidate is None:
        lines.append("## Provider envelope")
        lines.append("")
        lines.append(audit.provider_result.reason or "_(no reason supplied)_")
        lines.append("")
        lines.append("No candidate was produced by the provider.")
        lines.append("")
        lines.append("## Authority statement")
        lines.append("")
        lines.append(
            "This request did not produce executable code. The "
            "deterministic skill validator and the runtime safety "
            "supervisor remain authoritative."
        )
        lines.append("")
        return "\n".join(lines)

    c = audit.candidate
    lines.append("## Candidate (untrusted)")
    lines.append("")
    lines.append(f"- skill_type: `{c.skill_type or 'unknown'}`")
    lines.append(f"- language: `{c.language}`")
    lines.append(f"- confidence: `{c.confidence_label}`")
    lines.append(
        "- declared topics: "
        + (", ".join(f"`{t}`" for t in c.declared_topics) or "_(none)_")
    )
    if c.known_uncertainties:
        lines.append("- known uncertainties:")
        for u in c.known_uncertainties:
            lines.append(f"  - {u}")
    lines.append("")
    lines.append("Candidate explanation:")
    lines.append("")
    lines.append("> " + c.explanation.replace("\n", "\n> "))
    lines.append("")
    lines.append("## Sanitizer")
    lines.append("")
    s = audit.sanitizer_result
    lines.append(f"- status: `{s.status}`")
    lines.append(f"- accepted: {s.accepted}")
    if s.blocked_fragments:
        lines.append("- blocked fragments:")
        for frag in s.blocked_fragments:
            lines.append(f"  - `{frag}`")
    if s.reason_codes:
        lines.append("- reason codes: " + ", ".join(s.reason_codes))
    if s.notes:
        lines.append("- notes:")
        for n in s.notes:
            lines.append(f"  - {n}")
    lines.append("")
    lines.append("## Validator bridge")
    lines.append("")
    v = audit.validator_result
    lines.append(f"- invoked: {v.invoked}")
    lines.append(f"- accepted: {v.accepted}")
    lines.append(f"- safety status: `{v.safety_status}`")
    if v.diagnostics:
        lines.append("- diagnostics:")
        for d in v.diagnostics:
            lines.append(
                f"  - [{d.get('severity', '?')}] `{d.get('code', '?')}`: "
                f"{d.get('message', '')}"
            )
    lines.append("")

    if audit.final_status == CandidateStatus.ACCEPTED.value and audit.code_card:
        lines.append("## Accepted code")
        lines.append("")
        lines.append("```python")
        lines.append(c.code.rstrip())
        lines.append("```")
        lines.append("")
        lines.append("## Safety review")
        lines.append("")
        if audit.safety_review:
            for key in (
                "safety_status",
                "risk_band",
                "allowed_topics",
                "forbidden_topics",
                "reason_codes",
                "human_review_required",
            ):
                val = audit.safety_review.get(key)
                if isinstance(val, list):
                    val = ", ".join(str(v) for v in val) or "_(none)_"
                lines.append(f"- {key}: `{val}`")
            notes = audit.safety_review.get("notes") or []
            if notes:
                lines.append("- notes:")
                for n in notes:
                    lines.append(f"  - {n}")
    else:
        lines.append("## No accepted code")
        lines.append("")
        lines.append(
            "The candidate did not pass both the sanitizer and the "
            "Phase 15A skill validator; no copyable code is produced."
        )
    lines.append("")
    lines.append("## Authority statement")
    lines.append("")
    lines.append(
        "The deterministic skill validator and the runtime safety "
        "supervisor remain authoritative. This audit does not "
        "authorise actuator motion, regardless of the final status."
    )
    lines.append("")
    return "\n".join(lines)
