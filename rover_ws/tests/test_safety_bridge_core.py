"""Tests for :class:`SafetyBridgeCore` without a ROS environment.

The core does not import ``rclpy`` — only the node module does. We
import the core directly and exercise the conversion from
``IncomingX`` dataclasses to supervisor inputs and back to outbound
publications. These tests are the most important static-validation
tests in this suite: they assert that the architectural authority
boundary (only the supervisor authorises motion) is preserved.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


# Make the rover_safety_bridge package importable without ROS.
_PKG_ROOT = Path(__file__).resolve().parents[1] / "src" / "rover_safety_bridge"
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))


from rover_safety_bridge.safety_bridge_core import (  # noqa: E402
    HostedClock,
    IncomingContact,
    IncomingImu,
    IncomingOdom,
    IncomingRequestedMotion,
    IncomingScan,
    OperatorPulses,
    SafetyBridgeCore,
)

from app.domain.enums import MotionDecision, SafetyState  # noqa: E402
from app.domain.identifiers import RunId, ScenarioId, SequentialIdGenerator  # noqa: E402


@pytest.fixture
def core() -> SafetyBridgeCore:
    clock = HostedClock()
    return SafetyBridgeCore(
        run_id=RunId("run-test-001"),
        scenario_id=ScenarioId("ros-bridge-core-test"),
        clock=clock,
        id_generator=SequentialIdGenerator(),
    )


def _populate_healthy_inputs(core: SafetyBridgeCore, *, now_ms: int) -> None:
    core.cache_scan(
        IncomingScan(
            timestamp_ms=now_ms,
            sequence_number=1,
            min_range_m=0.5,
            max_range_m=10.0,
            mean_range_m=4.0,
            point_count=720,
        )
    )
    core.cache_imu(
        IncomingImu(
            timestamp_ms=now_ms,
            sequence_number=1,
            angular_velocity_z=0.0,
            linear_accel_x=0.0,
            linear_accel_y=0.0,
            orientation_rad=0.0,
        )
    )
    core.cache_odom(
        IncomingOdom(
            timestamp_ms=now_ms,
            sequence_number=1,
            derived_linear_velocity=0.0,
            derived_angular_velocity=0.0,
            pose_x=0.0,
            pose_y=0.0,
            heading_rad=0.0,
        )
    )
    core.cache_contact(
        IncomingContact(timestamp_ms=now_ms, sequence_number=1, asserted=False)
    )


def test_boot_event_emitted(core: SafetyBridgeCore) -> None:
    evt = core.emit_boot_event()
    assert evt.event_type == "system_lifecycle.boot"
    assert evt.run_id == RunId("run-test-001")


def test_supervisor_authorizes_motion_when_healthy(core: SafetyBridgeCore) -> None:
    core.update_clock(now_ns=0)
    _populate_healthy_inputs(core, now_ms=0)
    # First tick: reach INACTIVE.
    out0 = core.evaluate(operator=OperatorPulses())
    core.update_clock(now_ns=200_000_000)
    _populate_healthy_inputs(core, now_ms=200)
    # Second tick: operator activates.
    out1 = core.evaluate(operator=OperatorPulses(activate=True))
    core.update_clock(now_ns=400_000_000)
    _populate_healthy_inputs(core, now_ms=400)
    core.cache_request(
        IncomingRequestedMotion(
            timestamp_ms=400, linear_velocity=0.4, angular_velocity=0.0, lifetime_ms=500
        )
    )
    out2 = core.evaluate(operator=OperatorPulses())
    assert out2.safety_state == SafetyState.ACTIVE_NORMAL
    assert out2.authorized.linear_velocity == pytest.approx(0.4)
    assert out2.authorized.decision == MotionDecision.AUTHORIZED


def test_safe_stop_zeros_motion(core: SafetyBridgeCore) -> None:
    core.update_clock(now_ns=0)
    _populate_healthy_inputs(core, now_ms=0)
    core.evaluate(operator=OperatorPulses())
    core.update_clock(now_ns=200_000_000)
    _populate_healthy_inputs(core, now_ms=200)
    core.evaluate(operator=OperatorPulses(activate=True))
    # Drop the LiDAR completely. Beyond the safe-stop threshold the
    # supervisor must transition to SAFE_STOP and zero the authorized
    # motion regardless of the request.
    for tick_ms in (300, 500, 800, 1100, 1500, 2000):
        core.update_clock(now_ns=tick_ms * 1_000_000)
        # Refresh IMU and odom so only LiDAR is stale.
        core.cache_imu(
            IncomingImu(
                timestamp_ms=tick_ms, sequence_number=tick_ms,
                angular_velocity_z=0.0, linear_accel_x=0.0, linear_accel_y=0.0,
                orientation_rad=0.0,
            )
        )
        core.cache_odom(
            IncomingOdom(
                timestamp_ms=tick_ms, sequence_number=tick_ms,
                derived_linear_velocity=0.0, derived_angular_velocity=0.0,
                pose_x=0.0, pose_y=0.0, heading_rad=0.0,
            )
        )
        core.cache_contact(
            IncomingContact(timestamp_ms=tick_ms, sequence_number=tick_ms, asserted=False)
        )
        core.cache_request(
            IncomingRequestedMotion(
                timestamp_ms=tick_ms, linear_velocity=0.4, angular_velocity=0.0,
                lifetime_ms=500,
            )
        )
        out = core.evaluate(operator=OperatorPulses())
    assert out.safety_state == SafetyState.SAFE_STOP
    assert out.authorized.linear_velocity == 0.0
    assert out.authorized.angular_velocity == 0.0


def test_estop_latches_until_explicit_reset(core: SafetyBridgeCore) -> None:
    core.update_clock(now_ns=0)
    _populate_healthy_inputs(core, now_ms=0)
    core.evaluate(operator=OperatorPulses())
    core.update_clock(now_ns=200_000_000)
    _populate_healthy_inputs(core, now_ms=200)
    core.evaluate(operator=OperatorPulses(activate=True))

    core.update_clock(now_ns=300_000_000)
    _populate_healthy_inputs(core, now_ms=300)
    out_estop = core.evaluate(operator=OperatorPulses(estop=True))
    assert out_estop.safety_state == SafetyState.E_STOP_LATCHED
    assert out_estop.authorized.is_zero_authorization

    # Subsequent ticks without a reset must not self-clear.
    for tick_ms in (400, 500, 800, 1500):
        core.update_clock(now_ns=tick_ms * 1_000_000)
        _populate_healthy_inputs(core, now_ms=tick_ms)
        out = core.evaluate(operator=OperatorPulses())
        assert out.safety_state == SafetyState.E_STOP_LATCHED


def test_velocity_clamped_in_restricted_state() -> None:
    """A second core uses a higher requested velocity than the limits.

    Even in ACTIVE_NORMAL the request is clamped to the limit. We assert
    the supervisor publishes a motion_arbitration.clamped event for the
    clamp.
    """

    clock = HostedClock()
    core = SafetyBridgeCore(
        run_id=RunId("run-clamp"),
        scenario_id=ScenarioId("clamp-test"),
        clock=clock,
        id_generator=SequentialIdGenerator(),
    )
    clock.set_now_ns(0)
    _populate_healthy_inputs(core, now_ms=0)
    core.evaluate(operator=OperatorPulses())
    clock.set_now_ns(200_000_000)
    _populate_healthy_inputs(core, now_ms=200)
    core.evaluate(operator=OperatorPulses(activate=True))
    clock.set_now_ns(400_000_000)
    _populate_healthy_inputs(core, now_ms=400)
    core.cache_request(
        IncomingRequestedMotion(
            timestamp_ms=400, linear_velocity=2.5, angular_velocity=0.0, lifetime_ms=500,
        )
    )
    out = core.evaluate(operator=OperatorPulses())
    assert out.authorized.linear_velocity <= 0.6 + 1e-9
    assert any(
        e.event_type == "motion_arbitration.clamped"
        for e in out.motion_arbitration_events
    )


def test_authorized_command_source_is_supervisor(core: SafetyBridgeCore) -> None:
    """Architectural invariant: every AuthorizedMotionCommand the bridge
    publishes carries the supervisor's arbitration source string. No
    other producer is allowed.
    """

    core.update_clock(now_ns=0)
    _populate_healthy_inputs(core, now_ms=0)
    out = core.evaluate(operator=OperatorPulses())
    assert out.authorized.source == "safety.supervisor.arbitration"
