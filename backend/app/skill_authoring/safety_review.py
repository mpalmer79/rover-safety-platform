"""Safety-review builder for a generated skill."""

from __future__ import annotations

from .catalog import find_template
from .models import (
    GeneratedSkill,
    SkillRiskBand,
    SkillSafetyReview,
    SkillSafetyStatus,
    SkillType,
)
from .validator import validate_generated_skill


def review_generated_skill(skill: GeneratedSkill) -> SkillSafetyReview:
    """Build a :class:`SkillSafetyReview` from a generated skill."""

    template = find_template(skill.skill_type, skill.language)
    diags = validate_generated_skill(skill)
    has_rejection = any(d.severity == "rejection" for d in diags)

    if has_rejection:
        return SkillSafetyReview(
            safety_status=SkillSafetyStatus.UNSAFE_REJECTED.value,
            risk_band=SkillRiskBand.BLOCKED.value,
            allowed_topics=(template.generated_topics if template else ()),
            forbidden_topics=(template.forbidden_topics if template else ()),
            reason_codes=tuple(d.code for d in diags),
            human_review_required=True,
            notes=tuple(d.message for d in diags),
        )

    if template is None:
        return SkillSafetyReview(
            safety_status=SkillSafetyStatus.NEEDS_REVIEW.value,
            risk_band=SkillRiskBand.RESTRICTED.value,
            allowed_topics=(),
            forbidden_topics=(),
            reason_codes=("template_missing",),
            human_review_required=True,
            notes=("no catalog entry for this skill type",),
        )

    notes: list[str] = [
        "Uses /cmd_vel_requested instead of /cmd_vel."
        if "/cmd_vel_requested" in skill.code
        else "Snippet does not publish to actuator topics.",
        "Final zero command is sent."
        if skill.skill_type
        in (
            SkillType.MOVE_FORWARD_DISTANCE.value,
            SkillType.ROTATE_DEGREES.value,
            SkillType.KEYBOARD_FORWARD_BINDING.value,
            SkillType.CONTROLLER_BUTTON_BINDING.value,
            SkillType.SAFE_STOP_WRAPPER.value,
            SkillType.STOP_IMMEDIATELY.value,
        )
        else "No motion is published.",
        "Safety supervisor remains authoritative for actual motion.",
    ]
    if template.timeout_required:
        notes.append("Command expires after the computed duration.")
    notes.extend(template.review_notes)

    return SkillSafetyReview(
        safety_status=SkillSafetyStatus.SAFE_TEMPLATE.value
        if template.risk_band == SkillRiskBand.LOW.value
        else SkillSafetyStatus.GUARDED.value,
        risk_band=template.risk_band,
        allowed_topics=template.generated_topics,
        forbidden_topics=template.forbidden_topics,
        reason_codes=("validation_passed",),
        human_review_required=template.risk_band
        in (
            SkillRiskBand.RESTRICTED.value,
            SkillRiskBand.BLOCKED.value,
        ),
        notes=tuple(notes),
    )
