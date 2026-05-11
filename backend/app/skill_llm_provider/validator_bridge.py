"""Bridge between the LLM sanitizer and the Phase 15A skill validator.

The bridge invokes the Phase 15A deterministic safety validator on
candidate code only after the sanitizer accepts it. If the
sanitizer rejected, the validator is intentionally not invoked, and
the bridge records ``invoked=False``.

The bridge also produces a Phase 15A-style ``SkillSafetyReview``-equivalent
payload (as a plain dict) and a code-card payload so the audit
bundle can render the same UI metadata that Phase 15A emits.
"""

from __future__ import annotations

from typing import Mapping

from app.skill_authoring import (
    SKILL_AUTHORING_DISCLAIMER,
)
from app.skill_authoring.diagnostics import code_card_metadata
from app.skill_authoring.models import (
    SkillLanguage as PhaseAlanguage,
    SkillRiskBand,
    SkillType,
)
from app.skill_authoring.validator import (
    REQUIRED_CODE_TOKENS,
    validate_generated_code,
)

from .models import (
    CandidateRejectionReason,
    CandidateSafetyStatus,
    SkillLLMCandidate,
    SkillLLMSanitizerResult,
    SkillLLMValidationResult,
)


def _diagnostic_to_dict(d) -> dict:
    return {
        "code": d.code,
        "severity": d.severity,
        "message": d.message,
        "parameter": getattr(d, "parameter", ""),
    }


def _classify_diagnostics(diags) -> tuple[bool, str]:
    """Return (accepted, safety_status) from a list of Phase 15A diagnostics."""

    if not diags:
        return True, CandidateSafetyStatus.SAFE_AFTER_VALIDATION.value
    has_rejection = any(d.severity == "rejection" for d in diags)
    if has_rejection:
        return False, CandidateSafetyStatus.REJECTED.value
    return True, CandidateSafetyStatus.GUARDED.value


def run_skill_validator_bridge(
    candidate: SkillLLMCandidate,
    sanitizer_result: SkillLLMSanitizerResult,
) -> tuple[SkillLLMValidationResult, Mapping[str, object] | None, Mapping[str, object] | None]:
    """Validate a sanitized candidate using the Phase 15A validator.

    Returns ``(validation_result, safety_review, code_card)``.

    * ``validation_result.invoked`` is False when the sanitizer
      rejected the candidate; the validator is not run.
    * ``safety_review`` and ``code_card`` are ``None`` for
      validator-rejected or sanitizer-rejected candidates.
    """

    if not sanitizer_result.accepted:
        return (
            SkillLLMValidationResult(
                invoked=False,
                accepted=False,
                diagnostics=(),
                skill_type=candidate.skill_type,
                safety_status=CandidateSafetyStatus.REJECTED.value,
            ),
            None,
            None,
        )

    if candidate.skill_type not in REQUIRED_CODE_TOKENS:
        # Phase 15A only validates skill types it knows about. An
        # unsupported skill type is itself a rejection at the
        # validator bridge.
        return (
            SkillLLMValidationResult(
                invoked=True,
                accepted=False,
                diagnostics=(
                    {
                        "code": CandidateRejectionReason.UNSUPPORTED_SKILL_TYPE.value,
                        "severity": "rejection",
                        "message": (
                            f"skill_type {candidate.skill_type!r} is not in "
                            "the Phase 15A catalog; cannot be validated"
                        ),
                        "parameter": "skill_type",
                    },
                ),
                skill_type=candidate.skill_type,
                safety_status=CandidateSafetyStatus.REJECTED.value,
            ),
            None,
            None,
        )

    diagnostics = validate_generated_code(candidate.code, candidate.skill_type)
    accepted, safety_status = _classify_diagnostics(diagnostics)
    diag_dicts = tuple(_diagnostic_to_dict(d) for d in diagnostics)

    validation_result = SkillLLMValidationResult(
        invoked=True,
        accepted=accepted,
        diagnostics=diag_dicts,
        skill_type=candidate.skill_type,
        safety_status=safety_status,
    )

    if not accepted:
        return validation_result, None, None

    # Accepted: build a safety review payload mirroring Phase 15A and
    # a code-card payload for the future reviewer UI.
    safety_review: dict = {
        "safety_status": safety_status,
        "risk_band": _risk_band_for(candidate.skill_type),
        "allowed_topics": list(candidate.declared_topics) or ["/cmd_vel_requested"],
        "forbidden_topics": ["/cmd_vel"],
        "reason_codes": ["validation_passed"],
        "human_review_required": sanitizer_result.human_review_required,
        "notes": list(sanitizer_result.notes)
        + [
            "Validated against Phase 15A REQUIRED_CODE_TOKENS for "
            f"skill_type='{candidate.skill_type}'.",
            "Safety supervisor remains authoritative for actual motion.",
            SKILL_AUTHORING_DISCLAIMER,
        ],
    }

    card = code_card_metadata(
        title=_title_for(candidate),
        subtitle=candidate.explanation.split("\n", 1)[0][:140] or "LLM-proposed skill candidate",
        language=candidate.language,
        skill_type=candidate.skill_type,
        code=candidate.code,
        risk_band=_risk_band_for(candidate.skill_type),
        diagnostics=(),
    )
    card_dict: dict = {
        "title": card.title,
        "subtitle": card.subtitle,
        "language": card.language,
        "skill_type": card.skill_type,
        "code": card.code,
        "line_count": card.line_count,
        "copy_label": card.copy_label,
        "safety_badges": list(card.safety_badges) + ["llm-proposed"],
        "animation_steps": list(card.animation_steps),
        "risk_band": card.risk_band,
        "diagnostics": [],
    }

    return validation_result, safety_review, card_dict


def _risk_band_for(skill_type: str) -> str:
    # Mirror the Phase 15A catalog's risk-band conventions.
    if skill_type in {
        SkillType.STOP_IMMEDIATELY.value,
        SkillType.SAFE_STOP_WRAPPER.value,
        SkillType.WAYPOINT_REQUEST.value,
        SkillType.PATROL_ROUTE_TEMPLATE.value,
    }:
        return SkillRiskBand.LOW.value
    return SkillRiskBand.GUARDED.value


def _title_for(candidate: SkillLLMCandidate) -> str:
    return f"LLM candidate: {candidate.skill_type}"
