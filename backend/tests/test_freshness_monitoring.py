"""Tests for sensor freshness evaluation."""

from __future__ import annotations

from app.domain.enums import SensorStatus, SensorType
from app.domain.sensors import (
    ContactReading,
    EncoderReading,
    IMUReading,
    LiDARReading,
    SensorFrame,
)
from app.safety.freshness import (
    DEFAULT_FRESHNESS_THRESHOLDS,
    FreshnessEvaluator,
)


def _frame(*, lidar_age_ms: int = 0, imu_age_ms: int = 0, encoder_age_ms: int = 0, now_ms: int = 1000) -> SensorFrame:
    return SensorFrame(
        lidar=LiDARReading(
            sensor_id="rover-01/lidar",
            sensor_type=SensorType.LIDAR,
            timestamp_ms=now_ms - lidar_age_ms,
            status=SensorStatus.HEALTHY,
            confidence=0.9,
            source="test",
            sequence_number=1,
            min_range_m=0.4,
            max_range_m=10.0,
            mean_range_m=5.0,
            point_count=720,
        ),
        imu=IMUReading(
            sensor_id="rover-01/imu",
            sensor_type=SensorType.IMU,
            timestamp_ms=now_ms - imu_age_ms,
            status=SensorStatus.HEALTHY,
            confidence=0.85,
            source="test",
            sequence_number=1,
            angular_velocity_z=0.1,
        ),
        encoder=EncoderReading(
            sensor_id="rover-01/encoders",
            sensor_type=SensorType.WHEEL_ENCODER,
            timestamp_ms=now_ms - encoder_age_ms,
            status=SensorStatus.HEALTHY,
            confidence=0.9,
            source="test",
            sequence_number=1,
            derived_linear_velocity=0.4,
            derived_angular_velocity=0.1,
        ),
        contact=ContactReading(
            sensor_id="rover-01/contact",
            sensor_type=SensorType.CONTACT,
            timestamp_ms=now_ms,
            status=SensorStatus.HEALTHY,
            confidence=1.0,
            source="test",
            sequence_number=1,
        ),
    )


def test_all_streams_fresh() -> None:
    ev = FreshnessEvaluator()
    report = ev.evaluate(_frame(), now_ms=1000)
    assert not report.any_warn
    assert not report.any_safe_stop
    assert not report.any_missing_required


def test_lidar_warn_stale_detected() -> None:
    ev = FreshnessEvaluator()
    age = DEFAULT_FRESHNESS_THRESHOLDS[SensorType.LIDAR].warn_ms + 50
    now = 5_000
    report = ev.evaluate(_frame(lidar_age_ms=age, now_ms=now), now_ms=now)
    assert report.any_warn
    assert "stale_lidar" in report.stale_reason_codes()
    assert not report.any_safe_stop


def test_lidar_safe_stop_stale_detected() -> None:
    ev = FreshnessEvaluator()
    age = DEFAULT_FRESHNESS_THRESHOLDS[SensorType.LIDAR].safe_stop_ms + 50
    now = 5_000
    report = ev.evaluate(_frame(lidar_age_ms=age, now_ms=now), now_ms=now)
    assert report.any_safe_stop
    assert "stale_lidar" in report.safe_stop_reason_codes()


def test_missing_required_sensor_safe_stop() -> None:
    ev = FreshnessEvaluator()
    base = _frame(now_ms=5000)
    frame = SensorFrame(lidar=None, imu=base.imu, encoder=base.encoder, contact=base.contact)
    report = ev.evaluate(frame, now_ms=5000)
    assert report.any_missing_required
    assert "stale_lidar" in report.safe_stop_reason_codes()


def test_packet_delay_treated_as_freshness_problem() -> None:
    ev = FreshnessEvaluator()
    age = DEFAULT_FRESHNESS_THRESHOLDS[SensorType.LIDAR].warn_ms + 100
    now = 5_000
    report = ev.evaluate(_frame(lidar_age_ms=age, now_ms=now), now_ms=now)
    assert report.any_warn
