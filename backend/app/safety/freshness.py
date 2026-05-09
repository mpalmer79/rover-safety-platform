"""Freshness evaluation for required sensor streams.

The supervisor must refuse to authorize motion if any required input is
stale. Two thresholds are tracked per stream: a *warn* threshold that
demotes the system to ``ACTIVE_DEGRADED`` and a *safe-stop* threshold
that escalates to ``SAFE_STOP``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Optional

from app.domain.enums import SensorType
from app.domain.sensors import SensorFrame, SensorReading


@dataclass(frozen=True, slots=True)
class FreshnessThresholds:
    """Per-stream freshness thresholds, in milliseconds."""

    warn_ms: int
    safe_stop_ms: int

    def __post_init__(self) -> None:
        if self.warn_ms <= 0:
            raise ValueError("warn_ms must be positive")
        if self.safe_stop_ms <= self.warn_ms:
            raise ValueError("safe_stop_ms must be strictly greater than warn_ms")


DEFAULT_FRESHNESS_THRESHOLDS: dict[SensorType, FreshnessThresholds] = {
    SensorType.LIDAR: FreshnessThresholds(warn_ms=250, safe_stop_ms=750),
    SensorType.IMU: FreshnessThresholds(warn_ms=200, safe_stop_ms=600),
    SensorType.WHEEL_ENCODER: FreshnessThresholds(warn_ms=200, safe_stop_ms=600),
    SensorType.CONTACT: FreshnessThresholds(warn_ms=500, safe_stop_ms=1500),
}


@dataclass(frozen=True, slots=True)
class StreamReport:
    sensor_type: SensorType
    is_present: bool
    is_fresh: bool
    is_safe_stop_stale: bool
    age_ms: Optional[int]
    reason_code: Optional[str]
    message: str


@dataclass(frozen=True, slots=True)
class FreshnessReport:
    """Aggregate freshness report for one tick."""

    streams: dict[SensorType, StreamReport] = field(default_factory=dict)

    @property
    def any_warn(self) -> bool:
        return any(not s.is_fresh and not s.is_safe_stop_stale for s in self.streams.values())

    @property
    def any_safe_stop(self) -> bool:
        return any(s.is_safe_stop_stale for s in self.streams.values())

    @property
    def any_missing_required(self) -> bool:
        return any(not s.is_present for s in self.streams.values())

    def stale_reason_codes(self) -> tuple[str, ...]:
        return tuple(
            s.reason_code
            for s in self.streams.values()
            if s.reason_code is not None and (not s.is_fresh or s.is_safe_stop_stale)
        )

    def safe_stop_reason_codes(self) -> tuple[str, ...]:
        return tuple(
            s.reason_code
            for s in self.streams.values()
            if s.reason_code is not None and s.is_safe_stop_stale
        )


_REASON_CODES: dict[SensorType, str] = {
    SensorType.LIDAR: "stale_lidar",
    SensorType.IMU: "stale_imu",
    SensorType.WHEEL_ENCODER: "stale_encoders",
    SensorType.CONTACT: "stale_contact",
}


def is_fresh(reading: SensorReading, *, now_ms: int, max_age_ms: int) -> bool:
    """Module-level helper used by tests and external code."""

    return reading.is_fresh(now_ms=now_ms, max_age_ms=max_age_ms)


class FreshnessEvaluator:
    """Evaluates a :class:`SensorFrame` against per-stream thresholds.

    Required streams are configurable; by default the four MVP sensors
    are required.
    """

    def __init__(
        self,
        *,
        thresholds: Optional[Mapping[SensorType, FreshnessThresholds]] = None,
        required: Optional[set[SensorType]] = None,
    ) -> None:
        self._thresholds = dict(thresholds or DEFAULT_FRESHNESS_THRESHOLDS)
        self._required = (
            set(required) if required is not None else {SensorType.LIDAR, SensorType.IMU, SensorType.WHEEL_ENCODER}
        )

    def evaluate(self, frame: SensorFrame, *, now_ms: int) -> FreshnessReport:
        streams: dict[SensorType, StreamReport] = {}

        for sensor_type in (
            SensorType.LIDAR,
            SensorType.IMU,
            SensorType.WHEEL_ENCODER,
            SensorType.CONTACT,
        ):
            reading = self._extract(frame, sensor_type)
            thresholds = self._thresholds.get(sensor_type)
            required = sensor_type in self._required
            if reading is None:
                if required:
                    streams[sensor_type] = StreamReport(
                        sensor_type=sensor_type,
                        is_present=False,
                        is_fresh=False,
                        is_safe_stop_stale=True,
                        age_ms=None,
                        reason_code=_REASON_CODES.get(sensor_type),
                        message=f"required sensor {sensor_type.value} missing",
                    )
                else:
                    streams[sensor_type] = StreamReport(
                        sensor_type=sensor_type,
                        is_present=False,
                        is_fresh=True,
                        is_safe_stop_stale=False,
                        age_ms=None,
                        reason_code=None,
                        message=f"optional sensor {sensor_type.value} absent",
                    )
                continue

            age_ms = max(0, now_ms - reading.timestamp_ms)
            if thresholds is None:
                streams[sensor_type] = StreamReport(
                    sensor_type=sensor_type,
                    is_present=True,
                    is_fresh=True,
                    is_safe_stop_stale=False,
                    age_ms=age_ms,
                    reason_code=None,
                    message=f"{sensor_type.value} has no thresholds configured",
                )
                continue
            is_warn_stale = age_ms > thresholds.warn_ms
            is_safe_stop_stale = age_ms > thresholds.safe_stop_ms
            streams[sensor_type] = StreamReport(
                sensor_type=sensor_type,
                is_present=True,
                is_fresh=not is_warn_stale,
                is_safe_stop_stale=is_safe_stop_stale,
                age_ms=age_ms,
                reason_code=_REASON_CODES.get(sensor_type),
                message=(
                    f"{sensor_type.value} stale {age_ms}ms > {thresholds.safe_stop_ms}ms"
                    if is_safe_stop_stale
                    else (
                        f"{sensor_type.value} stale {age_ms}ms > {thresholds.warn_ms}ms"
                        if is_warn_stale
                        else f"{sensor_type.value} fresh ({age_ms}ms)"
                    )
                ),
            )
        return FreshnessReport(streams=streams)

    @staticmethod
    def _extract(frame: SensorFrame, sensor_type: SensorType) -> Optional[SensorReading]:
        if sensor_type == SensorType.LIDAR:
            return frame.lidar
        if sensor_type == SensorType.IMU:
            return frame.imu
        if sensor_type == SensorType.WHEEL_ENCODER:
            return frame.encoder
        if sensor_type == SensorType.CONTACT:
            return frame.contact
        return None  # pragma: no cover - defensive
