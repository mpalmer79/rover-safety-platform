"""Sensor reading models.

Readings are immutable value objects. Each reading carries enough
metadata for replay-grade analysis without depending on the simulation
engine that produced it.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from app.domain.enums import SensorStatus, SensorType


@dataclass(frozen=True)
class SensorReading:
    """Common base fields shared by every sensor reading."""

    sensor_id: str
    sensor_type: SensorType
    timestamp_ms: int
    status: SensorStatus
    confidence: float
    source: str
    sequence_number: int

    def __post_init__(self) -> None:
        if not self.sensor_id:
            raise ValueError("sensor_id must be non-empty")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be in [0.0, 1.0], got {self.confidence!r}")
        if self.timestamp_ms < 0:
            raise ValueError("timestamp_ms must be non-negative")
        if self.sequence_number < 0:
            raise ValueError("sequence_number must be non-negative")

    def is_fresh(self, *, now_ms: int, max_age_ms: int) -> bool:
        """Freshness check used by the safety supervisor.

        ``now_ms`` is the current simulation time. Readings whose timestamp
        is in the future relative to ``now_ms`` are treated as fresh; the
        supervisor's clock is the authority.
        """

        if max_age_ms < 0:
            raise ValueError("max_age_ms must be non-negative")
        if now_ms < self.timestamp_ms:
            return True
        return (now_ms - self.timestamp_ms) <= max_age_ms

    def base_payload(self) -> dict[str, Any]:
        return {
            "sensor_id": self.sensor_id,
            "sensor_type": self.sensor_type.value,
            "timestamp_ms": self.timestamp_ms,
            "status": self.status.value,
            "confidence": self.confidence,
            "source": self.source,
            "sequence_number": self.sequence_number,
        }


@dataclass(frozen=True)
class LiDARReading(SensorReading):
    """2D LiDAR scan reduced to a small set of summary statistics.

    Full ranges are not retained here; the simulation core does not
    perform perception. Reviewers needing raw scans pull them from the
    bag.
    """

    min_range_m: float = field(default=math.inf)
    max_range_m: float = field(default=0.0)
    mean_range_m: float = field(default=0.0)
    point_count: int = 0

    def __post_init__(self) -> None:
        SensorReading.__post_init__(self)
        if self.point_count < 0:
            raise ValueError("point_count must be non-negative")
        if self.point_count > 0:
            if not math.isfinite(self.min_range_m) or self.min_range_m < 0:
                raise ValueError("min_range_m must be finite and non-negative")
            if not math.isfinite(self.max_range_m) or self.max_range_m < 0:
                raise ValueError("max_range_m must be finite and non-negative")
            if self.max_range_m < self.min_range_m:
                raise ValueError("max_range_m must be >= min_range_m")
            if not math.isfinite(self.mean_range_m) or self.mean_range_m < 0:
                raise ValueError("mean_range_m must be finite and non-negative")

    def to_dict(self) -> dict[str, Any]:
        d = self.base_payload()
        d["min_range_m"] = self.min_range_m
        d["max_range_m"] = self.max_range_m
        d["mean_range_m"] = self.mean_range_m
        d["point_count"] = self.point_count
        return d


@dataclass(frozen=True)
class IMUReading(SensorReading):
    """Inertial measurement reduced to the channels we actually consume."""

    linear_accel_x: float = 0.0
    linear_accel_y: float = 0.0
    angular_velocity_z: float = 0.0
    orientation_rad: float = 0.0
    bias_estimate: float = 0.0

    def __post_init__(self) -> None:
        SensorReading.__post_init__(self)
        for name in (
            "linear_accel_x",
            "linear_accel_y",
            "angular_velocity_z",
            "orientation_rad",
            "bias_estimate",
        ):
            value = getattr(self, name)
            if not math.isfinite(value):
                raise ValueError(f"IMUReading.{name} must be finite")

    def to_dict(self) -> dict[str, Any]:
        d = self.base_payload()
        d.update(
            {
                "linear_accel_x": self.linear_accel_x,
                "linear_accel_y": self.linear_accel_y,
                "angular_velocity_z": self.angular_velocity_z,
                "orientation_rad": self.orientation_rad,
                "bias_estimate": self.bias_estimate,
            }
        )
        return d


@dataclass(frozen=True)
class EncoderReading(SensorReading):
    """Wheel encoder summary."""

    left_wheel_rad: float = 0.0
    right_wheel_rad: float = 0.0
    delta_left_rad: float = 0.0
    delta_right_rad: float = 0.0
    derived_linear_velocity: float = 0.0
    derived_angular_velocity: float = 0.0

    def __post_init__(self) -> None:
        SensorReading.__post_init__(self)
        for name in (
            "left_wheel_rad",
            "right_wheel_rad",
            "delta_left_rad",
            "delta_right_rad",
            "derived_linear_velocity",
            "derived_angular_velocity",
        ):
            value = getattr(self, name)
            if not math.isfinite(value):
                raise ValueError(f"EncoderReading.{name} must be finite")

    def to_dict(self) -> dict[str, Any]:
        d = self.base_payload()
        d.update(
            {
                "left_wheel_rad": self.left_wheel_rad,
                "right_wheel_rad": self.right_wheel_rad,
                "delta_left_rad": self.delta_left_rad,
                "delta_right_rad": self.delta_right_rad,
                "derived_linear_velocity": self.derived_linear_velocity,
                "derived_angular_velocity": self.derived_angular_velocity,
            }
        )
        return d


@dataclass(frozen=True)
class ContactReading(SensorReading):
    """Contact / bumper assertion.

    A single reading represents the current state of the contact channel.
    ``activated`` is the high-priority signal; the supervisor escalates
    immediately on assertion.
    """

    activated: bool = False
    contact_count: int = 0
    location_hint: Optional[str] = None

    def __post_init__(self) -> None:
        SensorReading.__post_init__(self)
        if self.contact_count < 0:
            raise ValueError("contact_count must be non-negative")

    def to_dict(self) -> dict[str, Any]:
        d = self.base_payload()
        d["activated"] = self.activated
        d["contact_count"] = self.contact_count
        d["location_hint"] = self.location_hint
        return d


@dataclass(frozen=True, slots=True)
class SensorFrame:
    """A snapshot of all sensors observed at one tick.

    Convenience aggregation used by the simulation engine and the safety
    supervisor. Any field may be ``None`` if the corresponding stream
    failed to produce a reading this tick (this is itself a meaningful
    signal).
    """

    lidar: Optional[LiDARReading] = None
    imu: Optional[IMUReading] = None
    encoder: Optional[EncoderReading] = None
    contact: Optional[ContactReading] = None

    def all_readings(self) -> tuple[SensorReading, ...]:
        return tuple(r for r in (self.lidar, self.imu, self.encoder, self.contact) if r is not None)

    def to_dict(self) -> dict[str, Any]:
        return {
            "lidar": self.lidar.to_dict() if self.lidar else None,
            "imu": self.imu.to_dict() if self.imu else None,
            "encoder": self.encoder.to_dict() if self.encoder else None,
            "contact": self.contact.to_dict() if self.contact else None,
        }
