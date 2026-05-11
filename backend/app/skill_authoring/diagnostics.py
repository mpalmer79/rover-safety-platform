"""Diagnostic helpers and code-card metadata builder."""

from __future__ import annotations

from .models import (
    CodeCard,
    GeneratedSkill,
    SkillDiagnostic,
    SkillRiskBand,
    SkillType,
)


DIAGNOSTIC_CODES: tuple[str, ...] = (
    "request_accepted",
    "unsupported_instruction",
    "ambiguous_request",
    "direct_actuator_command",
    "safety_override",
    "estop_override",
    "unbounded_motion",
    "unbounded_speed",
    "shell_or_code_execution",
    "direct_motor_control",
    "sensor_disable",
    "network_access",
    "unknown_location",
    "out_of_range_parameter",
    "validation_passed",
    "validation_failed",
    "missing_required_parameter",
)


def info(code: str, message: str, *, parameter: str = "") -> SkillDiagnostic:
    return SkillDiagnostic(
        code=code, severity="info", message=message, parameter=parameter
    )


def warning(code: str, message: str, *, parameter: str = "") -> SkillDiagnostic:
    return SkillDiagnostic(
        code=code, severity="warning", message=message, parameter=parameter
    )


def rejection(code: str, message: str, *, parameter: str = "") -> SkillDiagnostic:
    return SkillDiagnostic(
        code=code, severity="rejection", message=message, parameter=parameter
    )


def _animation_steps_for(skill_type: str) -> tuple[str, ...]:
    """Suggest UI animation steps without building a UI."""

    base = (
        "imports",
        "constants",
        "publisher setup",
        "bounded command loop",
        "stop command",
        "safety explanation",
    )
    if skill_type == SkillType.STOP_IMMEDIATELY.value:
        return ("imports", "publisher setup", "stop command", "safety explanation")
    if skill_type == SkillType.PUBLISH_REQUESTED_MOTION.value:
        return (
            "imports",
            "publisher setup",
            "single publish",
            "safety explanation",
        )
    if skill_type == SkillType.WAYPOINT_REQUEST.value:
        return (
            "imports",
            "publisher setup",
            "mission request",
            "safety explanation",
        )
    if skill_type == SkillType.PATROL_ROUTE_TEMPLATE.value:
        return (
            "imports",
            "publisher setup",
            "build patrol message",
            "publish patrol request",
            "safety explanation",
        )
    if skill_type == SkillType.SAFE_STOP_WRAPPER.value:
        return (
            "imports",
            "publisher setup",
            "context manager entry",
            "user-callable body",
            "zero-on-exit",
            "safety explanation",
        )
    return base


def _badges_for(skill_type: str, risk_band: str) -> tuple[str, ...]:
    """Deterministic safety badges for the code card."""

    badges: list[str] = ["requested-motion-only", "supervisor-authorised"]
    if skill_type in (
        SkillType.WAYPOINT_REQUEST.value,
        SkillType.PATROL_ROUTE_TEMPLATE.value,
    ):
        badges = ["mission-request-only", "supervisor-authorised"]
    if risk_band == SkillRiskBand.LOW.value:
        badges.append("risk:low")
    elif risk_band == SkillRiskBand.GUARDED.value:
        badges.append("risk:guarded")
    elif risk_band == SkillRiskBand.RESTRICTED.value:
        badges.append("risk:restricted")
    elif risk_band == SkillRiskBand.BLOCKED.value:
        badges.append("risk:blocked")
    badges.append("not-safety-certified")
    return tuple(badges)


def code_card_metadata(
    *,
    title: str,
    subtitle: str,
    language: str,
    skill_type: str,
    code: str,
    risk_band: str,
    diagnostics: tuple[SkillDiagnostic, ...] = (),
) -> CodeCard:
    return CodeCard(
        title=title,
        subtitle=subtitle,
        language=language,
        skill_type=skill_type,
        code=code,
        line_count=len(code.splitlines()),
        copy_label=f"Copy {title}",
        safety_badges=_badges_for(skill_type, risk_band),
        animation_steps=_animation_steps_for(skill_type),
        risk_band=risk_band,
        diagnostics=tuple(diagnostics),
    )
