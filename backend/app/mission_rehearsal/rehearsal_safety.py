"""Safety rules + bounded-motion limits for rehearsal plans.

These limits mirror the Phase 15A catalog. Plans whose bounded
motion exceeds these limits are rejected before the supervisor ever
sees them.
"""

from __future__ import annotations

import re
from typing import Mapping

from .models import (
    RehearsalFailureReason,
    RehearsalSafetyStatus,
)


SAFETY_LIMITS: Mapping[str, float] = {
    "max_distance_meters": 25.0,
    "max_angle_degrees": 720.0,
    "max_linear_speed_mps": 0.5,
    "max_angular_speed_rad_s": 1.0,
}


# Forbidden patterns in proposal source text or mission notes.
REHEARSAL_FORBIDDEN_PATTERNS: tuple[tuple[str, str, str], ...] = (
    (
        r"(?<!_requested)/cmd_vel\b(?!_)",
        RehearsalFailureReason.DIRECT_ACTUATOR_COMMAND.value,
        "direct /cmd_vel reference",
    ),
    (
        r"\bwhile\s+True\s*:",
        RehearsalFailureReason.UNBOUNDED_LOOP.value,
        "unbounded while True loop",
    ),
    (
        r"\b(?:forever|infinitely|indefinitely|unbounded)\b",
        RehearsalFailureReason.UNBOUNDED_LOOP.value,
        "unbounded motion request",
    ),
    (
        r"\b(?:disable|bypass)\s+(?:the\s+)?safety(?:\s+supervisor)?\b",
        RehearsalFailureReason.SAFETY_OVERRIDE.value,
        "safety supervisor override",
    ),
    (
        r"\bignore\s+safety\b",
        RehearsalFailureReason.SAFETY_OVERRIDE.value,
        "ignore safety phrase",
    ),
    (
        r"\b(?:ignore|override|disable)\s+(?:the\s+)?(?:e[-_ ]?stop|estop)\b",
        RehearsalFailureReason.ESTOP_OVERRIDE.value,
        "estop override",
    ),
    (
        r"restricted[_\s-]?corridor",
        RehearsalFailureReason.RESTRICTED_ZONE.value,
        "restricted corridor entry attempt",
    ),
    (
        r"forbidden[_\s-]?zone",
        RehearsalFailureReason.RESTRICTED_ZONE.value,
        "forbidden zone entry attempt",
    ),
    (
        r"\bas\s+fast\s+as\s+possible\b",
        RehearsalFailureReason.UNSAFE_SPEED.value,
        "unbounded speed request",
    ),
    (
        r"\b(?:max(?:imum)?|full)\s+speed\b",
        RehearsalFailureReason.UNSAFE_SPEED.value,
        "unbounded speed request",
    ),
)


def scan_text(text: str) -> list[tuple[str, str, str]]:
    """Return ``(matched, reason, message)`` triples for forbidden text.

    A descriptive ``/cmd_vel`` / ``safety override`` mention in a
    sentence that contains ``never`` / ``do not`` / ``must not`` is
    NOT flagged — operators are allowed to describe the boundary.
    """

    out: list[tuple[str, str, str]] = []
    if not text:
        return out
    descriptive = bool(
        re.search(r"\b(?:never|do not|must not)\b", text, flags=re.IGNORECASE)
    )
    for pattern, reason, message in REHEARSAL_FORBIDDEN_PATTERNS:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match is None:
            continue
        if descriptive and reason in {
            RehearsalFailureReason.DIRECT_ACTUATOR_COMMAND.value,
            RehearsalFailureReason.SAFETY_OVERRIDE.value,
            RehearsalFailureReason.ESTOP_OVERRIDE.value,
        }:
            # Allow a descriptive boundary statement.
            continue
        out.append((match.group(0), reason, message))
    return out


def classify_safety_status(
    *,
    validation_passed: bool,
    supervisor_approved: bool,
    runtime_completed: bool,
    safety_escalations: int,
) -> str:
    """Roll up a single safety status from pipeline outcomes."""

    if not validation_passed:
        return RehearsalSafetyStatus.UNSAFE_REJECTED.value
    if not supervisor_approved:
        return RehearsalSafetyStatus.UNSAFE_REJECTED.value
    if safety_escalations > 0:
        return RehearsalSafetyStatus.UNSAFE_REJECTED.value
    if runtime_completed:
        return RehearsalSafetyStatus.SAFE.value
    return RehearsalSafetyStatus.GUARDED.value
