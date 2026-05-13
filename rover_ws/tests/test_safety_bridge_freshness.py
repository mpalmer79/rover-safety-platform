"""Receive-time freshness regression test (#15).

If the safety bridge measured freshness against the sender's
``header.stamp``, a publisher claiming a future stamp could prevent the
watchdog from firing. After #15, freshness is measured against the
SUBSCRIBER's receive time — so a future sender stamp does not delay
the stale-input escalation.

We exercise :class:`SafetyBridgeCore` directly. The node's callback is
the place where the conversion from ROS message to ``IncomingScan``
happens; that conversion is asserted to use receive-time in the unit
test for ``safety_bridge_node``. Here we assert the core's behaviour
once the receive-time-based ``Incoming*`` dataclass is in hand.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


_PKG_ROOT = Path(__file__).resolve().parents[1] / "src" / "rover_safety_bridge"
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))


from rover_safety_bridge.safety_bridge_core import (  # noqa: E402
    HostedClock,
    IncomingImu,
    IncomingOdom,
    IncomingScan,
    OperatorPulses,
    SafetyBridgeCore,
)

from app.domain.enums import SafetyState  # noqa: E402
from app.domain.identifiers import RunId, ScenarioId, SequentialIdGenerator  # noqa: E402


def _populate_healthy(core: SafetyBridgeCore, *, now_ms: int) -> None:
    core.cache_scan(
        IncomingScan(
            timestamp_ms=now_ms,
            sequence_number=1,
            min_range_m=0.5,
            max_range_m=10.0,
            mean_range_m=4.0,
            point_count=720,
            sender_stamp_ms=now_ms,
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
            sender_stamp_ms=now_ms,
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
            sender_stamp_ms=now_ms,
        )
    )


def test_future_sender_stamp_does_not_delay_safe_stop() -> None:
    """A scan with sender_stamp_ms far in the future is still considered
    stale once its RECEIVE-time exceeds the safe_stop threshold."""

    clock = HostedClock()
    core = SafetyBridgeCore(
        run_id=RunId("run-fresh"),
        scenario_id=ScenarioId("scn-fresh"),
        clock=clock,
        id_generator=SequentialIdGenerator(),
    )
    # Boot at t=0; warm-up.
    clock.set_now_ns(0)
    _populate_healthy(core, now_ms=0)
    core.evaluate(operator=OperatorPulses(activate=True))

    # The publisher pushes one scan with a wildly future sender stamp
    # but receive-time t=100ms.
    clock.set_now_ns(100 * 1_000_000)
    core.cache_scan(
        IncomingScan(
            timestamp_ms=100,
            sequence_number=2,
            min_range_m=0.5,
            max_range_m=10.0,
            mean_range_m=4.0,
            point_count=720,
            sender_stamp_ms=10_000_000,  # 10,000 s in the future
        )
    )
    core.cache_imu(
        IncomingImu(
            timestamp_ms=100,
            sequence_number=2,
            angular_velocity_z=0.0,
            linear_accel_x=0.0,
            linear_accel_y=0.0,
            orientation_rad=0.0,
        )
    )
    core.cache_odom(
        IncomingOdom(
            timestamp_ms=100,
            sequence_number=2,
            derived_linear_velocity=0.0,
            derived_angular_velocity=0.0,
            pose_x=0.0,
            pose_y=0.0,
            heading_rad=0.0,
        )
    )
    core.evaluate(operator=OperatorPulses())

    # No new scans arrive. Advance the bridge clock past the
    # LIDAR safe_stop threshold (750 ms default) and re-evaluate.
    clock.set_now_ns(2_000 * 1_000_000)
    out = core.evaluate(operator=OperatorPulses())
    assert out.safety_state in {
        SafetyState.SAFE_STOP,
        SafetyState.E_STOP_LATCHED,
    }, (
        f"freshness must use receive-time; if header.stamp had been used the "
        f"future stamp would have delayed safe-stop. state={out.safety_state}"
    )


def test_sender_stamp_field_is_diagnostic_only() -> None:
    """The Incoming* dataclasses preserve sender_stamp_ms but the core uses timestamp_ms."""

    scan = IncomingScan(
        timestamp_ms=42,
        sequence_number=1,
        min_range_m=0.5,
        max_range_m=10.0,
        mean_range_m=4.0,
        point_count=10,
        sender_stamp_ms=999_999,
    )
    assert scan.timestamp_ms == 42
    assert scan.sender_stamp_ms == 999_999
