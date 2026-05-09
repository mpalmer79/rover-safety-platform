"""Synthetic sensor frame generator.

The simulator produces deterministic readings derived from the rover
state and a fault effect. The resulting :class:`SensorFrame` is what the
supervisor evaluates each tick.

This module is intentionally not perception-aware: LiDAR readings carry
only summary statistics. Reviewers needing raw scans pull them from the
recorded bag (a future addition).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from app.domain.enums import SensorStatus, SensorType
from app.domain.rover_state import RoverState
from app.domain.sensors import (
    ContactReading,
    EncoderReading,
    IMUReading,
    LiDARReading,
    SensorFrame,
)
from app.faults.models import FaultEffect


_NOMINAL_LIDAR_MIN = 0.30
_NOMINAL_LIDAR_MAX = 12.0
_NOMINAL_LIDAR_MEAN = 5.0
_NOMINAL_LIDAR_POINTS = 720


@dataclass(slots=True)
class SensorSimulator:
    """Stateful synthesizer that produces one :class:`SensorFrame` per tick."""

    rover_id: str = "rover-01"
    lidar_period_ms: int = 100
    imu_period_ms: int = 50
    encoder_period_ms: int = 50
    contact_period_ms: int = 200
    sequence_number: int = 0
    last_lidar_ms: int = -10_000_000
    last_imu_ms: int = -10_000_000
    last_encoder_ms: int = -10_000_000
    last_contact_ms: int = -10_000_000
    cached_lidar: Optional[LiDARReading] = None
    cached_imu: Optional[IMUReading] = None
    cached_encoder: Optional[EncoderReading] = None
    cached_contact: Optional[ContactReading] = None
    accumulated_left_rad: float = 0.0
    accumulated_right_rad: float = 0.0
    accumulated_drift: float = 0.0

    def generate(
        self,
        *,
        state: RoverState,
        now_ms: int,
        effect: FaultEffect,
        wheel_radius_m: float = 0.05,
        wheel_separation_m: float = 0.30,
        contact_asserted: bool = False,
    ) -> SensorFrame:
        self.sequence_number += 1

        lidar = self._maybe_lidar(state=state, now_ms=now_ms, effect=effect)
        imu = self._maybe_imu(state=state, now_ms=now_ms, effect=effect)
        encoder = self._maybe_encoder(
            state=state,
            now_ms=now_ms,
            effect=effect,
            wheel_radius_m=wheel_radius_m,
            wheel_separation_m=wheel_separation_m,
        )
        contact = self._maybe_contact(now_ms=now_ms, asserted=contact_asserted)

        return SensorFrame(lidar=lidar, imu=imu, encoder=encoder, contact=contact)

    def _maybe_lidar(
        self, *, state: RoverState, now_ms: int, effect: FaultEffect
    ) -> Optional[LiDARReading]:
        # Bridge disconnect drops every sensor frame.
        if effect.bridge_disconnected:
            return self.cached_lidar  # may be None at scenario start

        if effect.drop_lidar:
            # Do not advance the cached LiDAR timestamp.
            return self.cached_lidar

        if now_ms - self.last_lidar_ms < self.lidar_period_ms:
            return self.cached_lidar

        delay = max(0, effect.delay_lidar_ms)
        timestamp = now_ms - delay
        self.last_lidar_ms = now_ms
        # Range varies with simple bounded oscillation derived from heading.
        span = 1.5 + 0.5 * math.sin(state.heading_rad)
        reading = LiDARReading(
            sensor_id=f"{self.rover_id}/lidar",
            sensor_type=SensorType.LIDAR,
            timestamp_ms=timestamp,
            status=SensorStatus.HEALTHY if delay == 0 else SensorStatus.STALE,
            confidence=0.9 if delay == 0 else 0.6,
            source="sim",
            sequence_number=self.sequence_number,
            min_range_m=max(0.05, _NOMINAL_LIDAR_MIN - 0.1 * abs(state.linear_velocity)),
            max_range_m=_NOMINAL_LIDAR_MAX,
            mean_range_m=_NOMINAL_LIDAR_MEAN + span,
            point_count=_NOMINAL_LIDAR_POINTS,
        )
        self.cached_lidar = reading
        return reading

    def _maybe_imu(
        self, *, state: RoverState, now_ms: int, effect: FaultEffect
    ) -> Optional[IMUReading]:
        if effect.bridge_disconnected:
            return self.cached_imu
        if now_ms - self.last_imu_ms < self.imu_period_ms:
            return self.cached_imu
        self.last_imu_ms = now_ms
        bias = effect.imu_bias_offset
        # IMU reports body-frame angular rate; with bias this drifts deterministically.
        angular_z = state.angular_velocity + bias
        reading = IMUReading(
            sensor_id=f"{self.rover_id}/imu",
            sensor_type=SensorType.IMU,
            timestamp_ms=now_ms,
            status=SensorStatus.BIASED if bias != 0.0 else SensorStatus.HEALTHY,
            confidence=0.85 if bias == 0.0 else max(0.3, 0.85 - abs(bias)),
            source="sim",
            sequence_number=self.sequence_number,
            linear_accel_x=state.linear_velocity,
            linear_accel_y=0.0,
            angular_velocity_z=angular_z,
            orientation_rad=state.heading_rad,
            bias_estimate=bias,
        )
        self.cached_imu = reading
        return reading

    def _maybe_encoder(
        self,
        *,
        state: RoverState,
        now_ms: int,
        effect: FaultEffect,
        wheel_radius_m: float,
        wheel_separation_m: float,
    ) -> Optional[EncoderReading]:
        if effect.bridge_disconnected:
            return self.cached_encoder
        if now_ms - self.last_encoder_ms < self.encoder_period_ms:
            return self.cached_encoder
        dt = (now_ms - self.last_encoder_ms) / 1000.0 if self.last_encoder_ms >= 0 else self.encoder_period_ms / 1000.0
        self.last_encoder_ms = now_ms

        slip = max(0.0, min(1.0, effect.wheel_slip_factor))
        observed_linear = state.linear_velocity * (1.0 - slip)
        observed_angular = state.angular_velocity * (1.0 - slip)

        # Encoder drift adds a deterministic offset to derived linear velocity.
        self.accumulated_drift += effect.encoder_drift_rate * dt
        observed_linear += effect.encoder_drift_rate
        observed_angular += effect.forced_disagreement_angular  # disagreement vs IMU

        # Convert body-frame velocities to wheel deltas.
        v_left = observed_linear - observed_angular * wheel_separation_m * 0.5
        v_right = observed_linear + observed_angular * wheel_separation_m * 0.5
        delta_left = (v_left / wheel_radius_m) * dt
        delta_right = (v_right / wheel_radius_m) * dt
        self.accumulated_left_rad += delta_left
        self.accumulated_right_rad += delta_right

        reading = EncoderReading(
            sensor_id=f"{self.rover_id}/encoders",
            sensor_type=SensorType.WHEEL_ENCODER,
            timestamp_ms=now_ms,
            status=SensorStatus.HEALTHY if (effect.encoder_drift_rate == 0.0 and slip == 0.0) else SensorStatus.DISAGREEING,
            confidence=0.9 - 0.3 * slip,
            source="sim",
            sequence_number=self.sequence_number,
            left_wheel_rad=self.accumulated_left_rad,
            right_wheel_rad=self.accumulated_right_rad,
            delta_left_rad=delta_left,
            delta_right_rad=delta_right,
            derived_linear_velocity=observed_linear,
            derived_angular_velocity=observed_angular,
        )
        self.cached_encoder = reading
        return reading

    def _maybe_contact(self, *, now_ms: int, asserted: bool) -> Optional[ContactReading]:
        if now_ms - self.last_contact_ms < self.contact_period_ms and not asserted:
            return self.cached_contact
        self.last_contact_ms = now_ms
        reading = ContactReading(
            sensor_id=f"{self.rover_id}/contact",
            sensor_type=SensorType.CONTACT,
            timestamp_ms=now_ms,
            status=SensorStatus.HEALTHY,
            confidence=1.0,
            source="sim",
            sequence_number=self.sequence_number,
            activated=asserted,
            contact_count=1 if asserted else 0,
        )
        self.cached_contact = reading
        return reading
