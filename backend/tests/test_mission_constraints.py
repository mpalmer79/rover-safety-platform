"""Tests for mission constraint evaluation."""

from __future__ import annotations

from app.mission.constraints import (
    MissionConstraints,
    evaluate_constraints,
)


def _baseline() -> MissionConstraints:
    return MissionConstraints(
        max_linear_velocity=0.5,
        max_angular_velocity=0.8,
        minimum_confidence_for_motion=0.4,
        minimum_sensor_health=3,
        minimum_forward_clearance_m=0.30,
    )


def test_healthy_passes() -> None:
    out = evaluate_constraints(
        constraints=_baseline(),
        confidence_score=0.9,
        sensor_healthy_count=4,
        forward_clearance_m=2.0,
    )
    assert not out.motion_inhibited
    assert out.effective_max_linear == 0.5
    assert out.effective_max_angular == 0.8


def test_low_confidence_inhibits_motion() -> None:
    out = evaluate_constraints(
        constraints=_baseline(),
        confidence_score=0.1,
        sensor_healthy_count=4,
        forward_clearance_m=2.0,
    )
    assert out.motion_inhibited
    assert out.reason_code == "confidence_below_minimum"
    assert out.effective_max_linear == 0.0


def test_keepout_violation_inhibits_motion() -> None:
    out = evaluate_constraints(
        constraints=_baseline(),
        confidence_score=0.9,
        sensor_healthy_count=4,
        forward_clearance_m=2.0,
        inside_keepout=True,
    )
    assert out.motion_inhibited
    assert out.reason_code == "keepout_violation"


def test_zone_speed_clamp_takes_precedence() -> None:
    out = evaluate_constraints(
        constraints=_baseline(),
        confidence_score=0.9,
        sensor_healthy_count=4,
        forward_clearance_m=2.0,
        zone_max_linear=0.15,
        zone_max_angular=0.3,
    )
    assert not out.motion_inhibited
    assert out.effective_max_linear == 0.15
    assert out.effective_max_angular == 0.3


def test_safety_state_inhibits_motion() -> None:
    out = evaluate_constraints(
        constraints=_baseline(),
        confidence_score=0.9,
        sensor_healthy_count=4,
        forward_clearance_m=2.0,
        safety_state_inhibits_motion=True,
    )
    assert out.motion_inhibited
    assert out.reason_code == "safety_state_inhibits_motion"


def test_forward_clearance_inhibits_motion() -> None:
    out = evaluate_constraints(
        constraints=_baseline(),
        confidence_score=0.9,
        sensor_healthy_count=4,
        forward_clearance_m=0.10,
    )
    assert out.motion_inhibited
    assert out.reason_code == "forward_clearance_below_minimum"
