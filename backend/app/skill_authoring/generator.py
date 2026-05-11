"""Top-level skill generator.

Pipeline:

    SkillAuthoringRequest
      → parse_request (deterministic intent parser)
      → catalog lookup
      → templates.render_template (code text)
      → validator.validate_generated_code (rejection check)
      → diagnostics.code_card_metadata
      → safety_review.review_generated_skill
"""

from __future__ import annotations

from datetime import datetime, timezone

from .catalog import find_template
from .diagnostics import code_card_metadata, info, rejection
from .intent_parser import parse_request
from .models import (
    GeneratedSkill,
    SKILL_AUTHORING_DISCLAIMER,
    SkillAuthoringRequest,
    SkillCandidate,
    SkillDiagnostic,
    SkillGenerationResult,
    SkillGenerationStatus,
    SkillLanguage,
    SkillRejectionReason,
)
from .safety_review import review_generated_skill
from .templates import render_template
from .validator import validate_generated_code, validate_intent_request


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def generate_skill(
    request: SkillAuthoringRequest,
    *,
    generated_at_utc: str | None = None,
) -> SkillGenerationResult:
    """Run the full pipeline and return a :class:`SkillGenerationResult`."""

    timestamp = generated_at_utc or _now_iso()

    # 0) Envelope validation.
    envelope_diags = validate_intent_request(request)
    if envelope_diags:
        return _build_rejection(
            request=request,
            candidate=SkillCandidate(
                skill_type=None,
                parameters=(),
                diagnostics=envelope_diags,
                status=SkillGenerationStatus.REJECTED.value,
                rejection_reason=envelope_diags[0].code,
                normalised_text="",
            ),
            extra_diags=(),
            rejection_reason=envelope_diags[0].code,
            status=SkillGenerationStatus.REJECTED.value,
        )

    # 1) Parse.
    candidate = parse_request(request.text)

    if candidate.status != SkillGenerationStatus.GENERATED.value:
        return SkillGenerationResult(
            request=request,
            candidate=candidate,
            generated_skill=None,
            diagnostics=candidate.diagnostics,
            status=candidate.status,
            rejection_reason=candidate.rejection_reason,
        )

    # 2) Catalog lookup.
    assert candidate.skill_type is not None  # guaranteed by status
    template = find_template(candidate.skill_type, request.language)
    if template is None:
        return SkillGenerationResult(
            request=request,
            candidate=candidate,
            generated_skill=None,
            diagnostics=candidate.diagnostics
            + (
                rejection(
                    "unsupported_instruction",
                    f"no template for skill {candidate.skill_type!r} in language {request.language!r}",
                ),
            ),
            status=SkillGenerationStatus.UNSUPPORTED.value,
            rejection_reason=SkillRejectionReason.UNSUPPORTED_INSTRUCTION.value,
        )

    # 3) Render template.
    code, title, subtitle = render_template(
        skill_type=template.skill_type,
        language=template.language,
        params=candidate.parameters,
        defaults=template.default_parameters,
    )

    # 4) Validate the generated code.
    validation_diags = validate_generated_code(code, template.skill_type)
    if validation_diags:
        return SkillGenerationResult(
            request=request,
            candidate=candidate,
            generated_skill=None,
            diagnostics=candidate.diagnostics + validation_diags,
            status=SkillGenerationStatus.VALIDATION_FAILED.value,
            rejection_reason=validation_diags[0].code,
        )

    # 5) Build code card.
    accepted_diag = info(
        "validation_passed",
        "generated code passed safety validation",
    )
    diagnostics = candidate.diagnostics + (accepted_diag,)
    card = code_card_metadata(
        title=title,
        subtitle=subtitle,
        language=template.language,
        skill_type=template.skill_type,
        code=code,
        risk_band=template.risk_band,
        diagnostics=diagnostics,
    )

    # 6) Build GeneratedSkill, then a SafetyReview.
    skill_id = _skill_id_from(request)
    generated = GeneratedSkill(
        skill_id=skill_id,
        skill_type=template.skill_type,
        language=template.language,
        title=title,
        subtitle=subtitle,
        code=code,
        parameters=candidate.parameters,
        diagnostics=diagnostics,
        code_card=card,
        safety_review=None,  # filled below
        generated_at_utc=timestamp,
        request_text=request.text,
        normalised_text=candidate.normalised_text,
        disclaimer=SKILL_AUTHORING_DISCLAIMER,
    )
    # Fill the safety review (immutability dance).
    safety_review = review_generated_skill(generated)
    generated = GeneratedSkill(
        skill_id=generated.skill_id,
        skill_type=generated.skill_type,
        language=generated.language,
        title=generated.title,
        subtitle=generated.subtitle,
        code=generated.code,
        parameters=generated.parameters,
        diagnostics=generated.diagnostics,
        code_card=generated.code_card,
        safety_review=safety_review,
        generated_at_utc=generated.generated_at_utc,
        request_text=generated.request_text,
        normalised_text=generated.normalised_text,
        disclaimer=generated.disclaimer,
    )

    return SkillGenerationResult(
        request=request,
        candidate=candidate,
        generated_skill=generated,
        diagnostics=diagnostics,
        status=SkillGenerationStatus.GENERATED.value,
        rejection_reason="",
    )


def _skill_id_from(request: SkillAuthoringRequest) -> str:
    if request.request_id:
        return f"skill-{request.request_id}"
    return "skill-anon"


def _build_rejection(
    *,
    request: SkillAuthoringRequest,
    candidate: SkillCandidate,
    extra_diags: tuple[SkillDiagnostic, ...],
    rejection_reason: str,
    status: str,
) -> SkillGenerationResult:
    return SkillGenerationResult(
        request=request,
        candidate=candidate,
        generated_skill=None,
        diagnostics=candidate.diagnostics + extra_diags,
        status=status,
        rejection_reason=rejection_reason,
    )
