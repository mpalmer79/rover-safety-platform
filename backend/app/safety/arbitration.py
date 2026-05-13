"""Motion arbitration.

The arbiter is the only place in the codebase allowed to construct an
:class:`AuthorizedMotionCommand`. It clamps requested motion to the
limits associated with the current safety state, drops requests that
would violate those limits, and produces explicit reason codes for
replay.
"""

from __future__ import annotations

import math
from typing import Optional

from app.domain.enums import (
    MotionConstraintReason,
    MotionDecision,
    SafetyState,
)
from app.domain.motion import (
    AuthorizedMotionCommand,
    MotionArbitrationResult,
    MotionLimits,
    RequestedMotionCommand,
    motion_limits_for_state,
)


_AUTHORIZED_SOURCE = "safety.supervisor.arbitration"


class MotionArbiter:
    """Pure function wrapped in a class for symmetry with other safety nodes."""

    def __init__(self, *, command_lifetime_ms: int = 500) -> None:
        if command_lifetime_ms <= 0:
            raise ValueError("command_lifetime_ms must be positive")
        self._lifetime_ms = command_lifetime_ms

    @property
    def command_lifetime_ms(self) -> int:
        return self._lifetime_ms

    def arbitrate(
        self,
        *,
        requested: Optional[RequestedMotionCommand],
        safety_state: SafetyState,
        now_ms: int,
        operator_estop: bool,
        confidence_score: Optional[float] = None,
    ) -> MotionArbitrationResult:
        """Return an arbitration result for the given inputs.

        ``requested`` may be ``None`` if the mission layer has not
        published a fresh command. The arbiter still produces an
        authorized command (zero motion) so the gateway never sees a
        gap.
        """

        zero_authorized = self._make_authorized(
            linear=0.0,
            angular=0.0,
            decision=MotionDecision.REJECTED_ZEROED,
            reason=self._zero_reason(safety_state, operator_estop),
            safety_state=safety_state,
            requested=requested,
            now_ms=now_ms,
        )

        # Belt-and-suspenders: the domain types reject NaN at
        # construction, but the arbiter is the choke-point that
        # authorizes motion, so it also enforces finiteness on its
        # inputs. This protects future call paths (mocks,
        # deserializers, protobuf decoders) that might bypass
        # __post_init__.
        if requested is not None and not (
            math.isfinite(requested.linear_velocity)
            and math.isfinite(requested.angular_velocity)
        ):
            return MotionArbitrationResult(
                decision=MotionDecision.REJECTED_ZEROED,
                reason=MotionConstraintReason.INVALID_INPUT_ZERO,
                authorized=self._make_authorized(
                    linear=0.0,
                    angular=0.0,
                    decision=MotionDecision.REJECTED_ZEROED,
                    reason=MotionConstraintReason.INVALID_INPUT_ZERO,
                    safety_state=safety_state,
                    requested=None,
                    now_ms=now_ms,
                ),
                requested=requested,
            )

        # E-stop and forced-zero states always emit zero motion regardless of input.
        if operator_estop or safety_state == SafetyState.E_STOP_LATCHED:
            return MotionArbitrationResult(
                decision=MotionDecision.REJECTED_ZEROED,
                reason=MotionConstraintReason.E_STOP_ZERO if (operator_estop or safety_state == SafetyState.E_STOP_LATCHED) else self._zero_reason(safety_state, operator_estop),
                authorized=self._make_authorized(
                    linear=0.0,
                    angular=0.0,
                    decision=MotionDecision.REJECTED_ZEROED,
                    reason=MotionConstraintReason.E_STOP_ZERO,
                    safety_state=safety_state,
                    requested=requested,
                    now_ms=now_ms,
                ),
                requested=requested,
            )

        if safety_state.forces_zero_motion:
            return MotionArbitrationResult(
                decision=MotionDecision.REJECTED_ZEROED,
                reason=self._zero_reason(safety_state, False),
                authorized=zero_authorized,
                requested=requested,
            )

        if requested is None:
            return MotionArbitrationResult(
                decision=MotionDecision.REJECTED_EXPIRED,
                reason=MotionConstraintReason.COMMAND_EXPIRED,
                authorized=self._make_authorized(
                    linear=0.0,
                    angular=0.0,
                    decision=MotionDecision.REJECTED_EXPIRED,
                    reason=MotionConstraintReason.COMMAND_EXPIRED,
                    safety_state=safety_state,
                    requested=None,
                    now_ms=now_ms,
                ),
                requested=None,
            )

        if requested.is_expired_at(now_ms):
            return MotionArbitrationResult(
                decision=MotionDecision.REJECTED_EXPIRED,
                reason=MotionConstraintReason.COMMAND_EXPIRED,
                authorized=self._make_authorized(
                    linear=0.0,
                    angular=0.0,
                    decision=MotionDecision.REJECTED_EXPIRED,
                    reason=MotionConstraintReason.COMMAND_EXPIRED,
                    safety_state=safety_state,
                    requested=requested,
                    now_ms=now_ms,
                ),
                requested=requested,
            )

        if confidence_score is not None and confidence_score < 0.2:
            return MotionArbitrationResult(
                decision=MotionDecision.REJECTED_DEGRADED,
                reason=MotionConstraintReason.DEGRADED_ZERO,
                authorized=self._make_authorized(
                    linear=0.0,
                    angular=0.0,
                    decision=MotionDecision.REJECTED_DEGRADED,
                    reason=MotionConstraintReason.DEGRADED_ZERO,
                    safety_state=safety_state,
                    requested=requested,
                    now_ms=now_ms,
                ),
                requested=requested,
            )

        limits = motion_limits_for_state(safety_state)
        clamped_linear, clamped_angular, clamp_reason = self._clamp(
            linear=requested.linear_velocity,
            angular=requested.angular_velocity,
            limits=limits,
        )
        was_clamped = clamp_reason is not None

        decision = MotionDecision.AUTHORIZED_CLAMPED if was_clamped else MotionDecision.AUTHORIZED
        reason = clamp_reason if clamp_reason is not None else MotionConstraintReason.NONE
        return MotionArbitrationResult(
            decision=decision,
            reason=reason,
            authorized=self._make_authorized(
                linear=clamped_linear,
                angular=clamped_angular,
                decision=decision,
                reason=reason,
                safety_state=safety_state,
                requested=requested,
                now_ms=now_ms,
            ),
            requested=requested,
        )

    def _make_authorized(
        self,
        *,
        linear: float,
        angular: float,
        decision: MotionDecision,
        reason: MotionConstraintReason,
        safety_state: SafetyState,
        requested: Optional[RequestedMotionCommand],
        now_ms: int,
    ) -> AuthorizedMotionCommand:
        return AuthorizedMotionCommand(
            linear_velocity=linear,
            angular_velocity=angular,
            source=_AUTHORIZED_SOURCE,
            issued_at_ms=now_ms,
            expires_at_ms=now_ms + self._lifetime_ms,
            decision=decision,
            constraint_reason=reason,
            safety_state=safety_state,
            requested_linear_velocity=requested.linear_velocity if requested else 0.0,
            requested_angular_velocity=requested.angular_velocity if requested else 0.0,
        )

    @staticmethod
    def _clamp(
        *,
        linear: float,
        angular: float,
        limits: MotionLimits,
    ) -> tuple[float, float, Optional[MotionConstraintReason]]:
        reason: Optional[MotionConstraintReason] = None
        if abs(linear) > limits.linear_max:
            linear = math.copysign(limits.linear_max, linear)
            reason = MotionConstraintReason.VELOCITY_CLAMP
        if abs(angular) > limits.angular_max:
            angular = math.copysign(limits.angular_max, angular)
            reason = MotionConstraintReason.ANGULAR_CLAMP if reason is None else reason
        return linear, angular, reason

    @staticmethod
    def _zero_reason(state: SafetyState, operator_estop: bool) -> MotionConstraintReason:
        if operator_estop or state == SafetyState.E_STOP_LATCHED:
            return MotionConstraintReason.E_STOP_ZERO
        if state == SafetyState.SAFE_STOP:
            return MotionConstraintReason.SAFE_STOP_ZERO
        if state == SafetyState.BOOT:
            return MotionConstraintReason.BOOT_ZERO
        if state == SafetyState.INACTIVE:
            return MotionConstraintReason.INACTIVE_ZERO
        if state == SafetyState.RECOVERY:
            return MotionConstraintReason.RECOVERY_ZERO
        return MotionConstraintReason.SAFE_STOP_ZERO  # pragma: no cover - defensive
