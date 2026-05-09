"""Fault effect dataclasses.

A :class:`FaultEffect` is a small record that the injector updates each
tick to communicate what should happen to the next sensor frame and
which gateway/watchdog signals should be suppressed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(slots=True)
class FaultEffect:
    """Aggregate effect of all currently-fired faults on one tick."""

    drop_lidar: bool = False
    delay_lidar_ms: int = 0
    encoder_drift_rate: float = 0.0  # m/s of false offset added per tick
    imu_bias_offset: float = 0.0  # rad/s
    bridge_disconnected: bool = False
    suppress_gateway_heartbeat: bool = False
    delayed_command: bool = False
    forced_disagreement_angular: float = 0.0  # rad/s applied to encoder vs imu
    wheel_slip_factor: float = 0.0  # 0..1; multiplies encoder-reported velocity
    watchdog_targets: tuple[str, ...] = field(default_factory=tuple)
    notes: tuple[str, ...] = field(default_factory=tuple)

    def merge(self, other: "FaultEffect") -> "FaultEffect":
        return FaultEffect(
            drop_lidar=self.drop_lidar or other.drop_lidar,
            delay_lidar_ms=max(self.delay_lidar_ms, other.delay_lidar_ms),
            encoder_drift_rate=self.encoder_drift_rate + other.encoder_drift_rate,
            imu_bias_offset=self.imu_bias_offset + other.imu_bias_offset,
            bridge_disconnected=self.bridge_disconnected or other.bridge_disconnected,
            suppress_gateway_heartbeat=self.suppress_gateway_heartbeat or other.suppress_gateway_heartbeat,
            delayed_command=self.delayed_command or other.delayed_command,
            forced_disagreement_angular=self.forced_disagreement_angular + other.forced_disagreement_angular,
            wheel_slip_factor=max(self.wheel_slip_factor, other.wheel_slip_factor),
            watchdog_targets=tuple(set(self.watchdog_targets) | set(other.watchdog_targets)),
            notes=tuple(self.notes) + tuple(other.notes),
        )

    @property
    def has_any_effect(self) -> bool:
        return (
            self.drop_lidar
            or self.delay_lidar_ms > 0
            or self.encoder_drift_rate != 0.0
            or self.imu_bias_offset != 0.0
            or self.bridge_disconnected
            or self.suppress_gateway_heartbeat
            or self.delayed_command
            or self.forced_disagreement_angular != 0.0
            or self.wheel_slip_factor > 0.0
            or bool(self.watchdog_targets)
        )
