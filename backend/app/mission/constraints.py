"""Operational constraints applied to mission requested motion.

Constraints are declarative limits the orchestrator imposes on the
requested motion it produces. They are independent of the supervisor's
arbiter, which clamps as a backstop. The two layers serve different
purposes: the orchestrator constrains *what we ask for*; the
arbiter constrains *what we authorise*.

Constraints are deterministic and may be evaluated as a pure function:
given the current operational context (zone speed limits, world-model
hazards, supervisor confidence, sensor health), the evaluator yields
the effective per-tick limits.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class MissionConstraints:
    """Per-mission operational constraints."""

    max_linear_velocity: float = 0.5
    max_angular_velocity: float = 0.8
    minimum_confidence_for_motion: float = 0.5
    maximum_allowed_drift_m: float = 1.0
    minimum_forward_clearance_m: float = 0.30
    """When forward clearance falls below this, the orchestrator stops
    requesting forward motion."""

    minimum_sensor_health: int = 3
    """How many of the four MVP sensors must be reporting healthy
    before the orchestrator will request non-zero motion."""

    def __post_init__(self) -> None:
        for name in (
            "max_linear_velocity",
            "max_angular_velocity",
            "minimum_confidence_for_motion",
            "maximum_allowed_drift_m",
            "minimum_forward_clearance_m",
        ):
            value = getattr(self, name)
            if value < 0 or not math.isfinite(value):
                raise ValueError(
                    f"MissionConstraints.{name} must be non-negative and finite"
                )
        if not 0 <= self.minimum_sensor_health <= 4:
            raise ValueError("minimum_sensor_health must be in [0, 4]")


@dataclass(frozen=True)
class ConstraintEvaluation:
    """Outcome of evaluating constraints on a single tick."""

    effective_max_linear: float
    effective_max_angular: float
    motion_inhibited: bool
    reason_code: Optional[str] = None
    summary: str = ""
    contributing_signals: tuple[str, ...] = field(default_factory=tuple)


def evaluate_constraints(
    *,
    constraints: MissionConstraints,
    confidence_score: float,
    sensor_healthy_count: int,
    zone_max_linear: Optional[float] = None,
    zone_max_angular: Optional[float] = None,
    forward_clearance_m: Optional[float] = None,
    inside_keepout: bool = False,
    operator_paused: bool = False,
    safety_state_inhibits_motion: bool = False,
) -> ConstraintEvaluation:
    """Combine all sources of motion-inhibition / clamp into one decision.

    The orchestrator passes its observed context here and reads the
    resulting per-tick limits. The supervisor's clamp still runs after
    the orchestrator publishes its request; this function is the
    *requester*-side analogue of that clamp.
    """

    signals: list[str] = []
    inhibited = False
    reason: Optional[str] = None

    eff_lin = constraints.max_linear_velocity
    eff_ang = constraints.max_angular_velocity

    if zone_max_linear is not None and zone_max_linear < eff_lin:
        eff_lin = zone_max_linear
        signals.append(f"restricted_speed_linear:{zone_max_linear:.2f}")
    if zone_max_angular is not None and zone_max_angular < eff_ang:
        eff_ang = zone_max_angular
        signals.append(f"restricted_speed_angular:{zone_max_angular:.2f}")

    if confidence_score < constraints.minimum_confidence_for_motion:
        inhibited = True
        reason = "confidence_below_minimum"
        signals.append(f"confidence:{confidence_score:.2f}")
    if sensor_healthy_count < constraints.minimum_sensor_health:
        inhibited = True
        reason = reason or "sensor_health_below_minimum"
        signals.append(f"sensor_healthy:{sensor_healthy_count}")
    if (
        forward_clearance_m is not None
        and forward_clearance_m < constraints.minimum_forward_clearance_m
    ):
        inhibited = True
        reason = reason or "forward_clearance_below_minimum"
        signals.append(f"forward_clearance:{forward_clearance_m:.2f}")
    if inside_keepout:
        inhibited = True
        reason = reason or "keepout_violation"
        signals.append("inside_keepout")
    if operator_paused:
        inhibited = True
        reason = reason or "operator_paused"
        signals.append("operator_paused")
    if safety_state_inhibits_motion:
        inhibited = True
        reason = reason or "safety_state_inhibits_motion"
        signals.append("safety_state_inhibits_motion")

    if inhibited:
        eff_lin = 0.0
        eff_ang = 0.0

    summary = (
        f"motion inhibited: {reason}"
        if inhibited
        else f"clamp linear={eff_lin:.2f} angular={eff_ang:.2f}"
    )

    return ConstraintEvaluation(
        effective_max_linear=eff_lin,
        effective_max_angular=eff_ang,
        motion_inhibited=inhibited,
        reason_code=reason,
        summary=summary,
        contributing_signals=tuple(signals),
    )
