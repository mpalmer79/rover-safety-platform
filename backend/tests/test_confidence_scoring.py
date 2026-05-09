"""Tests for the confidence scorer."""

from __future__ import annotations

from app.domain.enums import SensorStatus, SensorType
from app.domain.sensors import (
    ContactReading,
    EncoderReading,
    IMUReading,
    LiDARReading,
    SensorFrame,
)
from app.safety.confidence import ConfidenceScorer
from app.safety.freshness import FreshnessEvaluator


def _healthy_frame(*, now_ms: int = 1000, contact: bool = False) -> SensorFrame:
    return SensorFrame(
        lidar=LiDARReading(
            sensor_id="r/lidar",
            sensor_type=SensorType.LIDAR,
            timestamp_ms=now_ms,
            status=SensorStatus.HEALTHY,
            confidence=0.9,
            source="t",
            sequence_number=1,
            min_range_m=0.4,
            max_range_m=10.0,
            mean_range_m=5.0,
            point_count=720,
        ),
        imu=IMUReading(
            sensor_id="r/imu",
            sensor_type=SensorType.IMU,
            timestamp_ms=now_ms,
            status=SensorStatus.HEALTHY,
            confidence=0.85,
            source="t",
            sequence_number=1,
            angular_velocity_z=0.1,
        ),
        encoder=EncoderReading(
            sensor_id="r/encoders",
            sensor_type=SensorType.WHEEL_ENCODER,
            timestamp_ms=now_ms,
            status=SensorStatus.HEALTHY,
            confidence=0.9,
            source="t",
            sequence_number=1,
            derived_linear_velocity=0.4,
            derived_angular_velocity=0.1,
        ),
        contact=ContactReading(
            sensor_id="r/contact",
            sensor_type=SensorType.CONTACT,
            timestamp_ms=now_ms,
            status=SensorStatus.HEALTHY,
            confidence=1.0,
            source="t",
            sequence_number=1,
            activated=contact,
        ),
    )


def test_healthy_high_confidence() -> None:
    fr = _healthy_frame()
    fresh = FreshnessEvaluator().evaluate(fr, now_ms=1000)
    rep = ConfidenceScorer().evaluate(frame=fr, freshness=fresh)
    assert rep.score >= 0.85
    assert not rep.contact_asserted
    assert not rep.sensor_disagreement


def test_disagreement_lowers_confidence() -> None:
    fr = _healthy_frame()
    # Replace IMU with one whose angular_velocity_z disagrees with encoder.
    bad_imu = IMUReading(
        sensor_id="r/imu",
        sensor_type=SensorType.IMU,
        timestamp_ms=1000,
        status=SensorStatus.HEALTHY,
        confidence=0.85,
        source="t",
        sequence_number=1,
        angular_velocity_z=0.1 + 1.5,  # well above threshold
    )
    fr2 = SensorFrame(lidar=fr.lidar, imu=bad_imu, encoder=fr.encoder, contact=fr.contact)
    fresh = FreshnessEvaluator().evaluate(fr2, now_ms=1000)
    rep = ConfidenceScorer().evaluate(frame=fr2, freshness=fresh)
    assert rep.sensor_disagreement
    assert "sensor_disagreement" in rep.contributing_reasons


def test_contact_asserted_signal_present() -> None:
    fr = _healthy_frame(contact=True)
    fresh = FreshnessEvaluator().evaluate(fr, now_ms=1000)
    rep = ConfidenceScorer().evaluate(frame=fr, freshness=fresh)
    assert rep.contact_asserted


def test_imu_bias_detected() -> None:
    fr = _healthy_frame()
    bad_imu = IMUReading(
        sensor_id="r/imu",
        sensor_type=SensorType.IMU,
        timestamp_ms=1000,
        status=SensorStatus.BIASED,
        confidence=0.5,
        source="t",
        sequence_number=1,
        angular_velocity_z=0.1,
        bias_estimate=0.3,
    )
    fr2 = SensorFrame(lidar=fr.lidar, imu=bad_imu, encoder=fr.encoder, contact=fr.contact)
    fresh = FreshnessEvaluator().evaluate(fr2, now_ms=1000)
    rep = ConfidenceScorer().evaluate(frame=fr2, freshness=fresh)
    assert rep.bias_detected
    assert "imu_bias" in rep.contributing_reasons


def test_missing_lidar_drops_to_zero_score_path() -> None:
    fr = _healthy_frame()
    fr2 = SensorFrame(lidar=None, imu=fr.imu, encoder=fr.encoder, contact=fr.contact)
    fresh = FreshnessEvaluator().evaluate(fr2, now_ms=1000)
    rep = ConfidenceScorer().evaluate(frame=fr2, freshness=fresh)
    assert rep.score < 0.85
    assert "stale_lidar" in rep.contributing_reasons
