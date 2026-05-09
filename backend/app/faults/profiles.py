"""Built-in fault profile factories.

Each helper returns a :class:`FaultProfile` with sensible defaults. They
are convenience functions; scenarios may construct profiles directly.
"""

from __future__ import annotations

from typing import Any

from app.domain.enums import FaultType
from app.domain.faults import FaultProfile


def stale_lidar(
    *,
    fault_id: str = "f-stale-lidar",
    activation_ms: int = 1000,
    duration_ms: int = -1,
    target: str = "/scan",
    parameters: dict[str, Any] | None = None,
) -> FaultProfile:
    return FaultProfile(
        fault_id=fault_id,
        fault_type=FaultType.STALE_LIDAR,
        target=target,
        activation_ms=activation_ms,
        duration_ms=duration_ms,
        parameters=dict(parameters or {"mode": "drop"}),
    )


def encoder_drift(
    *,
    fault_id: str = "f-enc-drift",
    activation_ms: int = 1000,
    duration_ms: int = -1,
    target: str = "/odom",
    drift_rate: float = 0.05,
) -> FaultProfile:
    return FaultProfile(
        fault_id=fault_id,
        fault_type=FaultType.ENCODER_DRIFT,
        target=target,
        activation_ms=activation_ms,
        duration_ms=duration_ms,
        parameters={"drift_rate_mps": float(drift_rate)},
    )


def imu_bias(
    *,
    fault_id: str = "f-imu-bias",
    activation_ms: int = 1000,
    duration_ms: int = -1,
    target: str = "/imu",
    bias: float = 0.25,
) -> FaultProfile:
    return FaultProfile(
        fault_id=fault_id,
        fault_type=FaultType.IMU_BIAS,
        target=target,
        activation_ms=activation_ms,
        duration_ms=duration_ms,
        parameters={"bias_rad_s": float(bias)},
    )


def bridge_disconnect(
    *,
    fault_id: str = "f-bridge",
    activation_ms: int = 1000,
    duration_ms: int = -1,
    target: str = "ros_gz_bridge",
) -> FaultProfile:
    return FaultProfile(
        fault_id=fault_id,
        fault_type=FaultType.BRIDGE_DISCONNECT,
        target=target,
        activation_ms=activation_ms,
        duration_ms=duration_ms,
        parameters={},
    )


def command_timeout(
    *,
    fault_id: str = "f-cmd-timeout",
    activation_ms: int = 1000,
    duration_ms: int = -1,
    target: str = "rover_hw_gateway",
) -> FaultProfile:
    return FaultProfile(
        fault_id=fault_id,
        fault_type=FaultType.COMMAND_TIMEOUT,
        target=target,
        activation_ms=activation_ms,
        duration_ms=duration_ms,
        parameters={"mode": "silent_consumer"},
    )


def watchdog_expiration(
    *,
    fault_id: str = "f-watchdog",
    activation_ms: int = 1000,
    duration_ms: int = -1,
    target: str,
) -> FaultProfile:
    return FaultProfile(
        fault_id=fault_id,
        fault_type=FaultType.WATCHDOG_EXPIRATION,
        target=target,
        activation_ms=activation_ms,
        duration_ms=duration_ms,
        parameters={"watchdog_name": target},
    )


def packet_delay(
    *,
    fault_id: str = "f-packet-delay",
    activation_ms: int = 1000,
    duration_ms: int = -1,
    target: str = "/scan",
    delay_ms: int = 300,
) -> FaultProfile:
    return FaultProfile(
        fault_id=fault_id,
        fault_type=FaultType.PACKET_DELAY,
        target=target,
        activation_ms=activation_ms,
        duration_ms=duration_ms,
        parameters={"delay_ms": int(delay_ms)},
    )


def sensor_disagreement(
    *,
    fault_id: str = "f-disagreement",
    activation_ms: int = 1000,
    duration_ms: int = -1,
    target: str = "/odom",
    angular_offset: float = 0.6,
) -> FaultProfile:
    return FaultProfile(
        fault_id=fault_id,
        fault_type=FaultType.SENSOR_DISAGREEMENT,
        target=target,
        activation_ms=activation_ms,
        duration_ms=duration_ms,
        parameters={"angular_offset_rad_s": float(angular_offset)},
    )


def wheel_slip(
    *,
    fault_id: str = "f-wheel-slip",
    activation_ms: int = 1000,
    duration_ms: int = -1,
    target: str = "/odom",
    slip_factor: float = 0.4,
) -> FaultProfile:
    if not 0.0 <= slip_factor <= 1.0:
        raise ValueError("slip_factor must be in [0, 1]")
    return FaultProfile(
        fault_id=fault_id,
        fault_type=FaultType.WHEEL_SLIP,
        target=target,
        activation_ms=activation_ms,
        duration_ms=duration_ms,
        parameters={"slip_factor": float(slip_factor)},
    )
