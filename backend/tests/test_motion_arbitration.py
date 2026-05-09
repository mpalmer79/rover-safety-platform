"""Tests for motion arbitration."""

from __future__ import annotations

import pytest

from app.domain.enums import MotionConstraintReason, MotionDecision, SafetyState
from app.domain.motion import RequestedMotionCommand, motion_limits_for_state
from app.safety.arbitration import MotionArbiter


def _request(*, linear: float, angular: float, now_ms: int = 0, lifetime: int = 500) -> RequestedMotionCommand:
    return RequestedMotionCommand(
        linear_velocity=linear,
        angular_velocity=angular,
        source="mission.test",
        issued_at_ms=now_ms,
        expires_at_ms=now_ms + lifetime,
    )


def test_active_normal_authorizes_request_within_limits() -> None:
    arbiter = MotionArbiter()
    res = arbiter.arbitrate(
        requested=_request(linear=0.4, angular=0.0),
        safety_state=SafetyState.ACTIVE_NORMAL,
        now_ms=10,
        operator_estop=False,
        confidence_score=0.9,
    )
    assert res.decision == MotionDecision.AUTHORIZED
    assert res.authorized.linear_velocity == 0.4
    assert res.authorized.angular_velocity == 0.0
    assert res.authorized.constraint_reason == MotionConstraintReason.NONE


def test_active_normal_clamps_overspeed() -> None:
    arbiter = MotionArbiter()
    res = arbiter.arbitrate(
        requested=_request(linear=2.0, angular=0.0),
        safety_state=SafetyState.ACTIVE_NORMAL,
        now_ms=10,
        operator_estop=False,
        confidence_score=0.9,
    )
    assert res.decision == MotionDecision.AUTHORIZED_CLAMPED
    assert res.authorized.linear_velocity == motion_limits_for_state(SafetyState.ACTIVE_NORMAL).linear_max
    assert res.authorized.constraint_reason == MotionConstraintReason.VELOCITY_CLAMP


def test_active_restricted_clamps_more_aggressively() -> None:
    arbiter = MotionArbiter()
    res = arbiter.arbitrate(
        requested=_request(linear=0.5, angular=0.0),
        safety_state=SafetyState.ACTIVE_RESTRICTED,
        now_ms=10,
        operator_estop=False,
        confidence_score=0.9,
    )
    assert res.decision == MotionDecision.AUTHORIZED_CLAMPED
    assert res.authorized.linear_velocity == motion_limits_for_state(SafetyState.ACTIVE_RESTRICTED).linear_max


def test_safe_stop_forces_zero() -> None:
    arbiter = MotionArbiter()
    res = arbiter.arbitrate(
        requested=_request(linear=0.4, angular=0.0),
        safety_state=SafetyState.SAFE_STOP,
        now_ms=10,
        operator_estop=False,
        confidence_score=0.9,
    )
    assert res.decision == MotionDecision.REJECTED_ZEROED
    assert res.authorized.is_zero_authorization
    assert res.authorized.constraint_reason == MotionConstraintReason.SAFE_STOP_ZERO


def test_estop_forces_zero_even_in_active_normal() -> None:
    arbiter = MotionArbiter()
    res = arbiter.arbitrate(
        requested=_request(linear=0.4, angular=0.0),
        safety_state=SafetyState.ACTIVE_NORMAL,
        now_ms=10,
        operator_estop=True,
        confidence_score=0.9,
    )
    assert res.decision == MotionDecision.REJECTED_ZEROED
    assert res.authorized.is_zero_authorization
    assert res.authorized.constraint_reason == MotionConstraintReason.E_STOP_ZERO


def test_expired_command_rejected() -> None:
    arbiter = MotionArbiter()
    cmd = _request(linear=0.4, angular=0.0, now_ms=0, lifetime=100)
    res = arbiter.arbitrate(
        requested=cmd,
        safety_state=SafetyState.ACTIVE_NORMAL,
        now_ms=200,  # past expiry
        operator_estop=False,
        confidence_score=0.9,
    )
    assert res.decision == MotionDecision.REJECTED_EXPIRED
    assert res.authorized.is_zero_authorization
    assert res.authorized.constraint_reason == MotionConstraintReason.COMMAND_EXPIRED


def test_missing_request_authorizes_zero_motion() -> None:
    arbiter = MotionArbiter()
    res = arbiter.arbitrate(
        requested=None,
        safety_state=SafetyState.ACTIVE_NORMAL,
        now_ms=10,
        operator_estop=False,
        confidence_score=0.9,
    )
    assert res.decision == MotionDecision.REJECTED_EXPIRED
    assert res.authorized.is_zero_authorization


def test_low_confidence_drops_to_zero() -> None:
    arbiter = MotionArbiter()
    res = arbiter.arbitrate(
        requested=_request(linear=0.4, angular=0.0),
        safety_state=SafetyState.ACTIVE_DEGRADED,
        now_ms=10,
        operator_estop=False,
        confidence_score=0.05,
    )
    assert res.decision == MotionDecision.REJECTED_DEGRADED
    assert res.authorized.is_zero_authorization
    assert res.authorized.constraint_reason == MotionConstraintReason.DEGRADED_ZERO


def test_authorized_command_carries_provenance() -> None:
    arbiter = MotionArbiter()
    res = arbiter.arbitrate(
        requested=_request(linear=2.0, angular=0.0),
        safety_state=SafetyState.ACTIVE_NORMAL,
        now_ms=10,
        operator_estop=False,
        confidence_score=0.9,
    )
    assert res.authorized.requested_linear_velocity == pytest.approx(2.0)
    assert res.authorized.requested_angular_velocity == 0.0
    assert res.authorized.safety_state == SafetyState.ACTIVE_NORMAL
