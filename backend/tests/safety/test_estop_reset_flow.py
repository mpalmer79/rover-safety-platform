"""End-to-end tests for the two-step armed-reset flow (#3 + #4).

Invariants pinned here:

* A bare ``operator_reset`` pulse is refused while latched, and the
  refusal is emitted as ``safety_transition.refused`` with reason
  ``estop_reset_unsafe``.
* An armed-then-reset sequence is honoured: the prior tick must carry
  ``operator_reset_armed=True``.
* Even an armed reset is refused if freshness is stale or contact is
  asserted on the reset tick.
* The state graph itself rejects ``RECOVERY -> ACTIVE_NORMAL`` directly.
"""

from __future__ import annotations

import pytest

from app.domain.enums import EventSeverity, SafetyState, SensorStatus, SensorType
from app.domain.identifiers import RunId, ScenarioId, SequentialIdGenerator
from app.domain.sensors import (
    ContactReading,
    EncoderReading,
    IMUReading,
    LiDARReading,
    SensorFrame,
)
from app.domain.time import ManualClock
from app.safety.supervisor import SafetySupervisor, SupervisorInputs
from app.safety.transitions import is_transition_allowed


def _fresh_frame(now_ms: int, *, contact: bool = False, with_lidar: bool = True) -> SensorFrame:
    lidar = None
    if with_lidar:
        lidar = LiDARReading(
            sensor_id="lidar",
            sensor_type=SensorType.LIDAR,
            timestamp_ms=now_ms,
            status=SensorStatus.HEALTHY,
            confidence=1.0,
            source="sim",
            sequence_number=now_ms,
            min_range_m=1.0,
            max_range_m=10.0,
            mean_range_m=5.0,
            point_count=120,
        )
    imu = IMUReading(
        sensor_id="imu",
        sensor_type=SensorType.IMU,
        timestamp_ms=now_ms,
        status=SensorStatus.HEALTHY,
        confidence=1.0,
        source="sim",
        sequence_number=now_ms,
    )
    encoder = EncoderReading(
        sensor_id="encoder",
        sensor_type=SensorType.WHEEL_ENCODER,
        timestamp_ms=now_ms,
        status=SensorStatus.HEALTHY,
        confidence=1.0,
        source="sim",
        sequence_number=now_ms,
    )
    contact_reading = ContactReading(
        sensor_id="contact",
        sensor_type=SensorType.CONTACT,
        timestamp_ms=now_ms,
        status=SensorStatus.HEALTHY,
        confidence=1.0,
        source="sim",
        sequence_number=now_ms,
        activated=contact,
    )
    return SensorFrame(lidar=lidar, imu=imu, encoder=encoder, contact=contact_reading)


def _make_supervisor() -> tuple[SafetySupervisor, ManualClock]:
    clock = ManualClock()
    sup = SafetySupervisor(
        run_id=RunId("run-estop"),
        scenario_id=ScenarioId("scn-estop"),
        clock=clock,
        id_generator=SequentialIdGenerator(),
        recovery_required_warm_ms=200,
    )
    return sup, clock


def _step(
    sup: SafetySupervisor,
    clock: ManualClock,
    now_ms: int,
    **kwargs: bool,
) -> object:
    # Drive the supervisor's clock alongside the input timestamp so
    # internal time-anchored state matches the input pulse times.
    while clock.now_ms() < now_ms:
        clock.advance_ms(100)
    return sup.evaluate(
        SupervisorInputs(
            frame=_fresh_frame(now_ms, contact=kwargs.pop("contact", False)),
            requested_motion=None,
            now_ms=now_ms,
            **kwargs,
        )
    )


def test_graph_rejects_recovery_direct_to_active_normal() -> None:
    assert not is_transition_allowed(SafetyState.RECOVERY, SafetyState.ACTIVE_NORMAL)
    assert not is_transition_allowed(SafetyState.RECOVERY, SafetyState.ACTIVE_RESTRICTED)
    assert not is_transition_allowed(SafetyState.RECOVERY, SafetyState.ACTIVE_DEGRADED)
    # The only legal exit from RECOVERY is SAFE_STOP.
    assert is_transition_allowed(SafetyState.RECOVERY, SafetyState.SAFE_STOP)


def test_single_pulse_reset_is_refused() -> None:
    sup, clock = _make_supervisor()
    # Warm up freshness for a couple of ticks.
    _step(sup, clock, now_ms=0)
    _step(sup, clock, now_ms=100, operator_activate=True)
    # E-stop.
    _step(sup, clock, now_ms=200, operator_estop=True)
    assert sup.safety_state == SafetyState.E_STOP_LATCHED

    # Bare reset (no prior armed tick) — must be refused.
    eval_ = _step(sup, clock, now_ms=300, operator_reset=True)
    assert sup.safety_state == SafetyState.E_STOP_LATCHED
    refusal = [e for e in eval_.events if e.event_type == "safety_transition.refused"]
    assert refusal, "expected safety_transition.refused event"
    assert refusal[0].reason_code == "estop_reset_unsafe"
    assert refusal[0].severity == EventSeverity.ERROR


def test_armed_then_reset_is_accepted() -> None:
    sup, clock = _make_supervisor()
    _step(sup, clock, now_ms=0)
    _step(sup, clock, now_ms=100, operator_activate=True)
    _step(sup, clock, now_ms=200, operator_estop=True)
    assert sup.safety_state == SafetyState.E_STOP_LATCHED

    # Tick 1: arm.
    _step(sup, clock, now_ms=300, operator_reset_armed=True)
    assert sup.safety_state == SafetyState.E_STOP_LATCHED
    # Tick 2: reset.
    _step(sup, clock, now_ms=400, operator_reset=True)
    assert sup.safety_state == SafetyState.RECOVERY


def test_armed_reset_under_stale_lidar_is_refused() -> None:
    sup, clock = _make_supervisor()
    _step(sup, clock, now_ms=0)
    _step(sup, clock, now_ms=100, operator_activate=True)
    _step(sup, clock, now_ms=200, operator_estop=True)

    # Arm the reset.
    _step(sup, clock, now_ms=300, operator_reset_armed=True)

    # Now reset, but supply a frame with no lidar (missing required).
    eval_ = sup.evaluate(
        SupervisorInputs(
            frame=_fresh_frame(400, with_lidar=False),
            requested_motion=None,
            operator_reset=True,
            now_ms=400,
        )
    )
    assert sup.safety_state == SafetyState.E_STOP_LATCHED
    codes = [e.reason_code for e in eval_.events if e.event_type == "safety_transition.refused"]
    assert "estop_reset_unsafe" in codes


def test_reactivation_path_lands_in_safe_stop_before_active() -> None:
    """Recovery validation must promote SAFE_STOP -> ACTIVE_NORMAL, not RECOVERY -> ACTIVE_NORMAL."""

    sup, clock = _make_supervisor()
    _step(sup, clock, now_ms=0)
    _step(sup, clock, now_ms=100, operator_activate=True)
    _step(sup, clock, now_ms=200, operator_estop=True)
    _step(sup, clock, now_ms=300, operator_reset_armed=True)
    _step(sup, clock, now_ms=400, operator_reset=True)
    assert sup.safety_state == SafetyState.RECOVERY
    # warm < 200 -> hold RECOVERY.
    _step(sup, clock, now_ms=500)
    assert sup.safety_state == SafetyState.RECOVERY
    # warm == 200 -> validates and lands in SAFE_STOP (NOT directly in ACTIVE).
    _step(sup, clock, now_ms=600)
    assert sup.safety_state == SafetyState.SAFE_STOP
    # Next eligible tick promotes SAFE_STOP -> ACTIVE_NORMAL.
    _step(sup, clock, now_ms=700)
    assert sup.safety_state == SafetyState.ACTIVE_NORMAL
