"""Confidence and disagreement scoring.

The confidence subsystem produces a single bounded score per tick. The
score and a small set of disagreement signals drive the supervisor's
choice between ``ACTIVE_NORMAL``, ``ACTIVE_RESTRICTED``, and
``ACTIVE_DEGRADED``. The supervisor escalates to ``SAFE_STOP`` based on
freshness, watchdogs, and contact assertions, never on confidence alone.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from app.domain.enums import SensorType
from app.domain.sensors import SensorFrame
from app.safety.freshness import FreshnessReport


# Tunable weights. Picked to keep the score in [0.0, 1.0] under typical
# operating conditions while making single-stream issues visible.
_WEIGHT_LIDAR = 0.35
_WEIGHT_IMU = 0.25
_WEIGHT_ENCODER = 0.30
_WEIGHT_CONTACT = 0.10

_DISAGREEMENT_PENALTY = 0.30
_BIAS_PENALTY = 0.15

# Velocity disagreement threshold between IMU-derived angular rate and
# encoder-derived angular rate, in rad/s.
_ANGULAR_DISAGREEMENT_THRESHOLD = 0.40
_LINEAR_DISAGREEMENT_THRESHOLD = 0.20


@dataclass(frozen=True, slots=True)
class ConfidenceReport:
    """Output of one confidence evaluation."""

    score: float
    contact_asserted: bool
    sensor_disagreement: bool
    bias_detected: bool
    notes: tuple[str, ...] = field(default_factory=tuple)
    angular_disagreement: float = 0.0
    linear_disagreement: float = 0.0
    contributing_reasons: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("ConfidenceReport.score must be in [0.0, 1.0]")


class ConfidenceScorer:
    """Compute a per-tick confidence score and disagreement signals.

    The scorer is fully deterministic: same frame in, same report out.
    """

    def __init__(
        self,
        *,
        weight_lidar: float = _WEIGHT_LIDAR,
        weight_imu: float = _WEIGHT_IMU,
        weight_encoder: float = _WEIGHT_ENCODER,
        weight_contact: float = _WEIGHT_CONTACT,
        disagreement_penalty: float = _DISAGREEMENT_PENALTY,
        bias_penalty: float = _BIAS_PENALTY,
        angular_disagreement_threshold: float = _ANGULAR_DISAGREEMENT_THRESHOLD,
        linear_disagreement_threshold: float = _LINEAR_DISAGREEMENT_THRESHOLD,
    ) -> None:
        self._w = {
            SensorType.LIDAR: weight_lidar,
            SensorType.IMU: weight_imu,
            SensorType.WHEEL_ENCODER: weight_encoder,
            SensorType.CONTACT: weight_contact,
        }
        self._disagreement_penalty = disagreement_penalty
        self._bias_penalty = bias_penalty
        self._angular_threshold = angular_disagreement_threshold
        self._linear_threshold = linear_disagreement_threshold

    def evaluate(
        self,
        *,
        frame: SensorFrame,
        freshness: FreshnessReport,
    ) -> ConfidenceReport:
        notes: list[str] = []
        reasons: list[str] = []
        # Per-stream contribution.
        score = 0.0
        # LiDAR.
        lidar = frame.lidar
        lidar_stream = freshness.streams.get(SensorType.LIDAR)
        if lidar is not None and lidar_stream is not None and lidar_stream.is_present:
            if lidar_stream.is_safe_stop_stale:
                notes.append("lidar safe-stop stale")
                reasons.append("stale_lidar")
            elif not lidar_stream.is_fresh:
                score += self._w[SensorType.LIDAR] * lidar.confidence * 0.5
                notes.append("lidar warn-stale")
                reasons.append("stale_lidar")
            else:
                score += self._w[SensorType.LIDAR] * lidar.confidence
        else:
            notes.append("lidar missing")
            reasons.append("stale_lidar")

        # IMU.
        imu = frame.imu
        imu_stream = freshness.streams.get(SensorType.IMU)
        if imu is not None and imu_stream is not None and imu_stream.is_present:
            base = imu.confidence
            if abs(imu.bias_estimate) > 0.1:
                base *= 1 - self._bias_penalty
                notes.append(f"imu bias {imu.bias_estimate:+.2f}")
                reasons.append("imu_bias")
            if imu_stream.is_safe_stop_stale:
                base = 0.0
                reasons.append("stale_imu")
            elif not imu_stream.is_fresh:
                base *= 0.5
                reasons.append("stale_imu")
            score += self._w[SensorType.IMU] * base
        else:
            notes.append("imu missing")
            reasons.append("stale_imu")

        # Encoder.
        enc = frame.encoder
        enc_stream = freshness.streams.get(SensorType.WHEEL_ENCODER)
        if enc is not None and enc_stream is not None and enc_stream.is_present:
            base = enc.confidence
            if enc_stream.is_safe_stop_stale:
                base = 0.0
                reasons.append("stale_encoders")
            elif not enc_stream.is_fresh:
                base *= 0.5
                reasons.append("stale_encoders")
            score += self._w[SensorType.WHEEL_ENCODER] * base
        else:
            notes.append("encoder missing")
            reasons.append("stale_encoders")

        # Contact.
        contact = frame.contact
        contact_asserted = bool(contact and contact.activated)
        if contact is not None:
            score += self._w[SensorType.CONTACT] * contact.confidence
            if contact_asserted:
                reasons.append("contact_asserted")
                notes.append("contact asserted")

        # Disagreement. We only compare directly observable channels.
        # Linear-velocity comparisons require integrating the IMU, which
        # the simulation core does not do; that comparison is left to a
        # future state estimator.
        ang_disagreement = 0.0
        lin_disagreement = 0.0
        sensor_disagreement = False
        if imu is not None and enc is not None:
            ang_disagreement = abs(imu.angular_velocity_z - enc.derived_angular_velocity)
            if ang_disagreement > self._angular_threshold:
                sensor_disagreement = True
                score *= 1 - self._disagreement_penalty
                notes.append(f"sensor disagreement ang={ang_disagreement:.2f}")
                reasons.append("sensor_disagreement")

        score = max(0.0, min(1.0, score))
        bias_detected = imu is not None and abs(imu.bias_estimate) > 0.1
        return ConfidenceReport(
            score=score,
            contact_asserted=contact_asserted,
            sensor_disagreement=sensor_disagreement,
            bias_detected=bias_detected,
            notes=tuple(notes),
            angular_disagreement=ang_disagreement,
            linear_disagreement=lin_disagreement,
            contributing_reasons=tuple(dict.fromkeys(reasons)),
        )


