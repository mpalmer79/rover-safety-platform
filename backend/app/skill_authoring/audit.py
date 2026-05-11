"""Audit bundle builder for generated and rejected skills."""

from __future__ import annotations

from dataclasses import asdict

from .models import (
    GeneratedSkill,
    SKILL_AUTHORING_DISCLAIMER,
    SKILL_AUTHORING_VERSION,
    SkillAuditBundle,
    SkillAuthoringRequest,
    SkillCandidate,
    SkillDiagnostic,
    SkillGenerationResult,
    SkillGenerationStatus,
)


def build_audit_bundle(result: SkillGenerationResult) -> SkillAuditBundle:
    return SkillAuditBundle(
        request=result.request,
        candidate=result.candidate,
        generated_skill=result.generated_skill,
        status=result.status,
        rejection_reason=result.rejection_reason,
        diagnostics=result.diagnostics,
        disclaimer=SKILL_AUTHORING_DISCLAIMER,
    )


def _diagnostic_to_dict(d: SkillDiagnostic) -> dict:
    return {
        "code": d.code,
        "severity": d.severity,
        "message": d.message,
        "parameter": d.parameter,
    }


def _parameter_to_dict(p) -> dict:
    value = p.value
    if isinstance(value, tuple):
        value = list(value)
    return {"name": p.name, "value": value, "units": p.units}


def request_to_dict(req: SkillAuthoringRequest) -> dict:
    return {
        "request_id": req.request_id,
        "text": req.text,
        "language": req.language,
        "requested_at_utc": req.requested_at_utc,
    }


def candidate_to_dict(cand: SkillCandidate) -> dict:
    return {
        "skill_type": cand.skill_type,
        "parameters": [_parameter_to_dict(p) for p in cand.parameters],
        "diagnostics": [_diagnostic_to_dict(d) for d in cand.diagnostics],
        "status": cand.status,
        "rejection_reason": cand.rejection_reason,
        "normalised_text": cand.normalised_text,
    }


def generated_skill_to_dict(skill: GeneratedSkill) -> dict:
    review = skill.safety_review
    return {
        "skill_id": skill.skill_id,
        "skill_type": skill.skill_type,
        "language": skill.language,
        "title": skill.title,
        "subtitle": skill.subtitle,
        "code": skill.code,
        "parameters": [_parameter_to_dict(p) for p in skill.parameters],
        "diagnostics": [_diagnostic_to_dict(d) for d in skill.diagnostics],
        "code_card": {
            "title": skill.code_card.title,
            "subtitle": skill.code_card.subtitle,
            "language": skill.code_card.language,
            "skill_type": skill.code_card.skill_type,
            "code": skill.code_card.code,
            "line_count": skill.code_card.line_count,
            "copy_label": skill.code_card.copy_label,
            "safety_badges": list(skill.code_card.safety_badges),
            "animation_steps": list(skill.code_card.animation_steps),
            "risk_band": skill.code_card.risk_band,
            "diagnostics": [
                _diagnostic_to_dict(d) for d in skill.code_card.diagnostics
            ],
        },
        "safety_review": {
            "safety_status": review.safety_status if review else "",
            "risk_band": review.risk_band if review else "",
            "allowed_topics": list(review.allowed_topics) if review else [],
            "forbidden_topics": list(review.forbidden_topics) if review else [],
            "reason_codes": list(review.reason_codes) if review else [],
            "human_review_required": review.human_review_required if review else True,
            "notes": list(review.notes) if review else [],
        },
        "generated_at_utc": skill.generated_at_utc,
        "request_text": skill.request_text,
        "normalised_text": skill.normalised_text,
        "disclaimer": skill.disclaimer,
    }


def audit_to_dict(audit: SkillAuditBundle) -> dict:
    skill = audit.generated_skill
    return {
        "skill_authoring_version": SKILL_AUTHORING_VERSION,
        "request": request_to_dict(audit.request),
        "candidate": candidate_to_dict(audit.candidate),
        "generated_skill": (
            generated_skill_to_dict(skill) if skill is not None else None
        ),
        "status": audit.status,
        "rejection_reason": audit.rejection_reason,
        "diagnostics": [_diagnostic_to_dict(d) for d in audit.diagnostics],
        "disclaimer": audit.disclaimer,
    }


def render_skill_report_markdown(audit: SkillAuditBundle) -> str:
    skill = audit.generated_skill
    assert skill is not None, "render_skill_report_markdown called on rejection"
    review = skill.safety_review
    lines: list[str] = []
    lines.append(f"# Skill report: {skill.skill_id}")
    lines.append("")
    lines.append(f"_{audit.disclaimer}_")
    lines.append("")
    lines.append(f"- **Skill type:** `{skill.skill_type}`")
    lines.append(f"- **Language:** `{skill.language}`")
    lines.append(f"- **Title:** {skill.title}")
    lines.append(f"- **Subtitle:** {skill.subtitle}")
    lines.append(f"- **Risk band:** `{review.risk_band if review else 'unknown'}`")
    lines.append(
        f"- **Safety status:** `{review.safety_status if review else 'unknown'}`"
    )
    lines.append(f"- **Generated (UTC):** {skill.generated_at_utc}")
    lines.append("")
    lines.append("## Request")
    lines.append("")
    lines.append("```text")
    lines.append(skill.request_text)
    lines.append("```")
    lines.append("")
    lines.append("## Parameters")
    lines.append("")
    if skill.parameters:
        for p in skill.parameters:
            lines.append(f"- `{p.name}` = `{p.value}` ({p.units or 'unitless'})")
    else:
        lines.append("_(none)_")
    lines.append("")
    lines.append("## Generated code")
    lines.append("")
    lines.append(f"```{('python' if skill.language == 'python_ros2' else skill.language)}")
    lines.append(skill.code.rstrip())
    lines.append("```")
    lines.append("")
    lines.append("## Safety review")
    lines.append("")
    if review:
        lines.append(f"- allowed topics: {', '.join(review.allowed_topics) or '_(none)_'}")
        lines.append(f"- forbidden topics: {', '.join(review.forbidden_topics) or '_(none)_'}")
        lines.append(
            f"- human review required: {review.human_review_required}"
        )
        lines.append("- reason codes: " + (", ".join(review.reason_codes) or "_(none)_"))
        if review.notes:
            lines.append("")
            lines.append("Notes:")
            for n in review.notes:
                lines.append(f"- {n}")
    lines.append("")
    lines.append("## Diagnostics")
    lines.append("")
    if skill.diagnostics:
        for d in skill.diagnostics:
            lines.append(f"- [{d.severity}] `{d.code}`: {d.message}")
    else:
        lines.append("_(none)_")
    lines.append("")
    lines.append("## Authority statement")
    lines.append("")
    lines.append(
        "This snippet publishes only requested-motion or mission "
        "topics. The safety supervisor and motion arbitration "
        "remain authoritative; no copy-paste of this code grants "
        "actuator authority."
    )
    lines.append("")
    return "\n".join(lines)


def render_rejection_markdown(audit: SkillAuditBundle) -> str:
    lines: list[str] = []
    lines.append(f"# Rejection report: {audit.request.request_id or 'unknown'}")
    lines.append("")
    lines.append(f"_{audit.disclaimer}_")
    lines.append("")
    lines.append(f"- **Status:** `{audit.status}`")
    lines.append(f"- **Rejection reason:** `{audit.rejection_reason or 'unspecified'}`")
    lines.append(f"- **Normalised text:** `{audit.candidate.normalised_text}`")
    lines.append("")
    lines.append("## Request")
    lines.append("")
    lines.append("```text")
    lines.append(audit.request.text)
    lines.append("```")
    lines.append("")
    lines.append("## Diagnostics")
    lines.append("")
    for d in audit.diagnostics:
        lines.append(f"- [{d.severity}] `{d.code}`: {d.message}")
    lines.append("")
    lines.append("## Authority statement")
    lines.append("")
    lines.append(
        "This request was rejected by the deterministic skill "
        "workbench. The safety supervisor and motion arbitration "
        "remain authoritative; no code was generated and no robot "
        "action is implied by this report."
    )
    lines.append("")
    return "\n".join(lines)
