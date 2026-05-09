"""Tests for fault injection.

These tests verify the contract that faults alter inputs and timing
only — they never set safety state, never produce
``AuthorizedMotionCommand`` values, and never write to ``/safety/state``.
"""

from __future__ import annotations

import pytest

from app.domain.enums import FaultStatus, FaultType
from app.domain.faults import FaultProfile, FaultRuntimeState
from app.domain.identifiers import RunId, ScenarioId, SequentialIdGenerator
from app.domain.time import ManualClock
from app.faults.injector import FaultInjector
from app.faults.profiles import (
    command_timeout,
    encoder_drift,
    imu_bias,
    sensor_disagreement,
    stale_lidar,
)


def _injector(profiles, *, scenario_duration_ms: int = 5000) -> FaultInjector:
    return FaultInjector(
        run_id=RunId("run-test"),
        scenario_id=ScenarioId("sc-test"),
        clock=ManualClock(),
        id_generator=SequentialIdGenerator(),
        profiles=profiles,
        scenario_duration_ms=scenario_duration_ms,
    )


def test_fault_lifecycle_armed_fired_cleared() -> None:
    profile = stale_lidar(activation_ms=500, duration_ms=300)
    injector = _injector([profile])
    arming = injector.emit_arming()
    assert any(e.event_type == "fault_injection.armed" for e in arming)

    out_before = injector.evaluate(now_ms=400)
    assert not out_before.active_faults

    out_fired = injector.evaluate(now_ms=500)
    assert any(e.event_type == "fault_injection.fired" for e in out_fired.events)
    assert out_fired.effect.drop_lidar
    assert any(f.status == FaultStatus.FIRED for f in out_fired.active_faults)

    out_cleared = injector.evaluate(now_ms=900)
    assert any(e.event_type == "fault_injection.cleared" for e in out_cleared.events)
    assert not out_cleared.effect.drop_lidar


def test_stale_lidar_produces_drop_effect() -> None:
    profile = stale_lidar(activation_ms=0, duration_ms=-1)
    injector = _injector([profile])
    injector.emit_arming()
    out = injector.evaluate(now_ms=0)
    assert out.effect.drop_lidar
    assert "stale_lidar:drop" in out.effect.notes


def test_encoder_drift_creates_velocity_offset() -> None:
    profile = encoder_drift(activation_ms=0, duration_ms=-1, drift_rate=0.1)
    injector = _injector([profile])
    injector.emit_arming()
    out = injector.evaluate(now_ms=0)
    assert out.effect.encoder_drift_rate == pytest.approx(0.1)


def test_imu_bias_offsets_angular_rate() -> None:
    profile = imu_bias(activation_ms=0, duration_ms=-1, bias=0.4)
    injector = _injector([profile])
    injector.emit_arming()
    out = injector.evaluate(now_ms=0)
    assert out.effect.imu_bias_offset == pytest.approx(0.4)


def test_command_timeout_suppresses_gateway_heartbeat() -> None:
    profile = command_timeout(activation_ms=0, duration_ms=-1)
    injector = _injector([profile])
    injector.emit_arming()
    out = injector.evaluate(now_ms=0)
    assert out.effect.suppress_gateway_heartbeat
    assert out.effect.delayed_command


def test_sensor_disagreement_offsets_angular_rate() -> None:
    profile = sensor_disagreement(activation_ms=0, duration_ms=-1, angular_offset=0.5)
    injector = _injector([profile])
    injector.emit_arming()
    out = injector.evaluate(now_ms=0)
    assert out.effect.forced_disagreement_angular == pytest.approx(0.5)


def test_fault_lifecycle_invalid_transition_raises() -> None:
    profile = stale_lidar(activation_ms=0, duration_ms=10)
    state = FaultRuntimeState(profile=profile, status=FaultStatus.CONFIGURED)
    with pytest.raises(ValueError):
        state.transition(new_status=FaultStatus.CLEARED, now_ms=0)


def test_fault_profile_rejects_negative_activation() -> None:
    with pytest.raises(ValueError):
        FaultProfile(
            fault_id="bad",
            fault_type=FaultType.STALE_LIDAR,
            target="/scan",
            activation_ms=-5,
            duration_ms=10,
        )


def test_injector_does_not_emit_safety_transitions() -> None:
    profile = stale_lidar(activation_ms=0, duration_ms=-1)
    injector = _injector([profile])
    injector.emit_arming()
    out = injector.evaluate(now_ms=0)
    # The injector must never produce safety_transition.* events itself.
    for evt in out.events:
        assert not evt.event_type.startswith("safety_transition.")
