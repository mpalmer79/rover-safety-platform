"""Belt-and-suspenders test for :class:`MotionArbiter` (#8).

The domain type ``MotionCommand`` rejects NaN at construction, so an
attacker cannot directly produce a ``RequestedMotionCommand`` with
non-finite velocities. But the arbiter is the choke-point that
authorizes motion; future code paths (mocks, deserializers, protobuf
decoders) might bypass ``__post_init__``. The arbiter must zero
anyway, with reason ``INVALID_INPUT_ZERO``.
"""

from __future__ import annotations

import math

from app.domain.enums import (
    MotionConstraintReason,
    MotionDecision,
    SafetyState,
)
from app.domain.motion import RequestedMotionCommand
from app.safety.arbitration import MotionArbiter


def _bypass_post_init(linear: float, angular: float) -> RequestedMotionCommand:
    """Construct a RequestedMotionCommand that skips __post_init__.

    This is the only way to fabricate a non-finite command — the
    domain type's validator would otherwise refuse. We use this to
    prove the arbiter zeros even when its input is corrupted.
    """

    obj = object.__new__(RequestedMotionCommand)
    object.__setattr__(obj, "linear_velocity", linear)
    object.__setattr__(obj, "angular_velocity", angular)
    object.__setattr__(obj, "source", "test.bypass")
    object.__setattr__(obj, "issued_at_ms", 0)
    object.__setattr__(obj, "expires_at_ms", 10_000)
    return obj


def test_nan_linear_velocity_is_zeroed() -> None:
    bad = _bypass_post_init(linear=float("nan"), angular=0.3)
    result = MotionArbiter().arbitrate(
        requested=bad,
        safety_state=SafetyState.ACTIVE_NORMAL,
        now_ms=100,
        operator_estop=False,
        confidence_score=1.0,
    )
    assert result.decision == MotionDecision.REJECTED_ZEROED
    assert result.reason == MotionConstraintReason.INVALID_INPUT_ZERO
    assert result.authorized.linear_velocity == 0.0
    assert result.authorized.angular_velocity == 0.0


def test_inf_angular_velocity_is_zeroed() -> None:
    bad = _bypass_post_init(linear=0.4, angular=float("inf"))
    result = MotionArbiter().arbitrate(
        requested=bad,
        safety_state=SafetyState.ACTIVE_NORMAL,
        now_ms=100,
        operator_estop=False,
        confidence_score=1.0,
    )
    assert result.decision == MotionDecision.REJECTED_ZEROED
    assert result.reason == MotionConstraintReason.INVALID_INPUT_ZERO
    assert math.isfinite(result.authorized.linear_velocity)
    assert math.isfinite(result.authorized.angular_velocity)


def test_finite_inputs_unaffected() -> None:
    """The new guard must not regress the happy path."""

    good = RequestedMotionCommand(
        linear_velocity=0.4,
        angular_velocity=0.1,
        source="test",
        issued_at_ms=0,
        expires_at_ms=10_000,
    )
    result = MotionArbiter().arbitrate(
        requested=good,
        safety_state=SafetyState.ACTIVE_NORMAL,
        now_ms=100,
        operator_estop=False,
        confidence_score=1.0,
    )
    assert result.decision == MotionDecision.AUTHORIZED
    assert result.reason == MotionConstraintReason.NONE
    assert result.authorized.linear_velocity == 0.4
