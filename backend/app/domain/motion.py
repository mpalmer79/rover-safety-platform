"""Motion command and arbitration models.

The two-channel separation between *requested* and *authorized* motion is
the architectural enforcement of the safety supervisor's authority. See
docs/SAFETY_MODEL.md sections 3 and 13, and ADR-004.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field, replace
from typing import Any, Optional

from app.domain.enums import (
    MotionConstraintReason,
    MotionDecision,
    SafetyState,
)


@dataclass(frozen=True, slots=True)
class MotionLimits:
    """Per-state motion limits.

    Values are SI: linear in meters/second, angular in radians/second,
    accelerations in their derivatives.
    """

    linear_max: float
    angular_max: float
    linear_accel_max: float
    angular_accel_max: float

    def __post_init__(self) -> None:
        for name in ("linear_max", "angular_max", "linear_accel_max", "angular_accel_max"):
            value = getattr(self, name)
            if value < 0 or not math.isfinite(value):
                raise ValueError(f"MotionLimits.{name} must be non-negative and finite, got {value!r}")


# Limits taken from docs/ODD.md section 6.
_LIMITS_BY_STATE: dict[SafetyState, MotionLimits] = {
    SafetyState.ACTIVE_NORMAL: MotionLimits(
        linear_max=0.6, angular_max=1.0, linear_accel_max=0.5, angular_accel_max=1.0
    ),
    SafetyState.ACTIVE_RESTRICTED: MotionLimits(
        linear_max=0.3, angular_max=0.6, linear_accel_max=0.25, angular_accel_max=0.5
    ),
    SafetyState.ACTIVE_DEGRADED: MotionLimits(
        linear_max=0.15, angular_max=0.3, linear_accel_max=0.15, angular_accel_max=0.3
    ),
    SafetyState.SAFE_STOP: MotionLimits(0.0, 0.0, 0.0, 0.0),
    SafetyState.E_STOP_LATCHED: MotionLimits(0.0, 0.0, 0.0, 0.0),
    SafetyState.BOOT: MotionLimits(0.0, 0.0, 0.0, 0.0),
    SafetyState.INACTIVE: MotionLimits(0.0, 0.0, 0.0, 0.0),
    SafetyState.RECOVERY: MotionLimits(0.0, 0.0, 0.0, 0.0),
}


def motion_limits_for_state(state: SafetyState) -> MotionLimits:
    """Return the motion limits associated with a safety state."""
    return _LIMITS_BY_STATE[state]


@dataclass(frozen=True)
class MotionCommand:
    """Base motion command.

    ``source`` identifies the producer (e.g., ``"mission.bt.waypoint_follow"``
    for a request, ``"safety.supervisor"`` for an authorization).
    ``issued_at`` and ``expires_at`` are simulation-time milliseconds.
    """

    linear_velocity: float
    angular_velocity: float
    source: str
    issued_at_ms: int
    expires_at_ms: int

    def __post_init__(self) -> None:
        if not math.isfinite(self.linear_velocity) or not math.isfinite(self.angular_velocity):
            raise ValueError("Motion velocities must be finite numbers")
        if self.expires_at_ms <= self.issued_at_ms:
            raise ValueError("expires_at_ms must be strictly greater than issued_at_ms")
        if not self.source:
            raise ValueError("source must be non-empty")

    @property
    def is_zero(self) -> bool:
        return self.linear_velocity == 0.0 and self.angular_velocity == 0.0

    def is_expired_at(self, now_ms: int) -> bool:
        return now_ms >= self.expires_at_ms

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["kind"] = type(self).__name__
        return d


@dataclass(frozen=True)
class RequestedMotionCommand(MotionCommand):
    """Motion request from the mission / planner layer.

    By construction this type is **not** consumed by the hardware gateway.
    Only the safety supervisor reads it.
    """


@dataclass(frozen=True)
class AuthorizedMotionCommand(MotionCommand):
    """The supervisor's final authorization.

    Always the only motion-bearing message accepted by the hardware
    gateway. Carries decision provenance for replay.
    """

    decision: MotionDecision = MotionDecision.AUTHORIZED
    constraint_reason: MotionConstraintReason = MotionConstraintReason.NONE
    safety_state: SafetyState = SafetyState.ACTIVE_NORMAL
    requested_linear_velocity: float = 0.0
    requested_angular_velocity: float = 0.0

    @property
    def was_clamped(self) -> bool:
        return self.decision == MotionDecision.AUTHORIZED_CLAMPED

    @property
    def is_zero_authorization(self) -> bool:
        return self.linear_velocity == 0.0 and self.angular_velocity == 0.0


@dataclass(frozen=True, slots=True)
class MotionArbitrationResult:
    """Outcome of a single arbitration evaluation.

    The arbiter produces one of these for every cycle. The caller can use
    the outcome to emit events, update the rover, or feed the gateway.
    """

    decision: MotionDecision
    reason: MotionConstraintReason
    authorized: AuthorizedMotionCommand
    requested: Optional[RequestedMotionCommand]
    notes: tuple[str, ...] = field(default_factory=tuple)

    def with_notes(self, *notes: str) -> "MotionArbitrationResult":
        return replace(self, notes=tuple(self.notes) + tuple(notes))

    def is_zero(self) -> bool:
        return self.authorized.is_zero_authorization
