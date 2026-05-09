"""Shared scaffolding for sensor adapter nodes.

Adapters share three concerns: parameter declaration (run_id,
scenario_id, freshness thresholds), publication of
:class:`rover_msgs/SensorHealth`, and freshness evaluation. This
module exposes those utilities so the per-sensor adapters stay short
and focused on the message-shape work specific to their stream.
"""

from __future__ import annotations

from dataclasses import dataclass

import rclpy
from builtin_interfaces.msg import Time
from rclpy.node import Node

from rover_msgs.msg import SensorHealth


@dataclass(frozen=True)
class FreshnessThresholds:
    warn_ms: int
    safe_stop_ms: int


class BaseAdapter(Node):
    """Common base for sensor adapter nodes.

    Subclasses are expected to declare additional parameters and
    subscribe to their raw input topic. They call
    :meth:`publish_health` once per evaluation tick and may call
    :meth:`publish_health_for_missing` when no reading has been
    received within the safe-stop window.
    """

    SENSOR_TYPE: str = "unknown"

    def __init__(self, node_name: str, sensor_type: str) -> None:
        super().__init__(node_name)
        self.SENSOR_TYPE = sensor_type
        self.declare_parameter("run_id", "unknown")
        self.declare_parameter("scenario_id", "unknown")
        self.declare_parameter("sensor_id", f"{sensor_type}-0")
        self.declare_parameter("warn_ms", 250)
        self.declare_parameter("safe_stop_ms", 750)
        self.declare_parameter("evaluation_period_ms", 100)
        self.declare_parameter("health_topic", f"/sensors/{sensor_type}/health")
        self._health_pub = self.create_publisher(
            SensorHealth,
            self._param_str("health_topic"),
            10,
        )
        self._sequence_number = 0
        self._last_msg_stamp: Time | None = None
        period_s = max(0.01, float(self._param_int("evaluation_period_ms")) / 1000.0)
        self._timer = self.create_timer(period_s, self._on_tick)

    # --------------------------------------------------------------
    # Helpers exposed to subclasses.
    # --------------------------------------------------------------
    def thresholds(self) -> FreshnessThresholds:
        return FreshnessThresholds(
            warn_ms=self._param_int("warn_ms"),
            safe_stop_ms=self._param_int("safe_stop_ms"),
        )

    def run_id(self) -> str:
        return self._param_str("run_id")

    def scenario_id(self) -> str:
        return self._param_str("scenario_id")

    def sensor_id(self) -> str:
        return self._param_str("sensor_id")

    def record_message(self, stamp: Time) -> None:
        """Subclass hook called when a fresh raw message arrives."""

        self._last_msg_stamp = stamp
        self._sequence_number += 1

    def _on_tick(self) -> None:
        """Default tick: publish current freshness; subclasses may override."""

        self.publish_health(self._derive_status())

    def _derive_status(self) -> tuple[str, str, int, float]:
        """Return (status, reason_code, age_ms, confidence)."""

        thresholds = self.thresholds()
        if self._last_msg_stamp is None:
            return ("disconnected", f"stale_{self.SENSOR_TYPE}", -1, 0.0)
        now = self.get_clock().now().nanoseconds // 1_000_000
        last_ms = self._last_msg_stamp.sec * 1000 + self._last_msg_stamp.nanosec // 1_000_000
        age_ms = max(0, int(now - last_ms))
        if age_ms > thresholds.safe_stop_ms:
            return ("stale", f"stale_{self.SENSOR_TYPE}", age_ms, 0.0)
        if age_ms > thresholds.warn_ms:
            return ("stale", f"stale_{self.SENSOR_TYPE}", age_ms, 0.4)
        return ("healthy", "", age_ms, 1.0)

    def publish_health(self, status_tuple: tuple[str, str, int, float]) -> None:
        status, reason, age_ms, confidence = status_tuple
        msg = SensorHealth()
        msg.stamp = self.get_clock().now().to_msg()
        msg.run_id = self.run_id()
        msg.scenario_id = self.scenario_id()
        msg.sensor_type = self.SENSOR_TYPE
        msg.sensor_id = self.sensor_id()
        msg.status = status
        msg.reason_code = reason
        msg.age_ms = age_ms
        msg.confidence_score = confidence
        msg.sequence_number = self._sequence_number
        self._health_pub.publish(msg)

    # --------------------------------------------------------------
    # Internal helpers.
    # --------------------------------------------------------------
    def _param_int(self, name: str) -> int:
        return int(self.get_parameter(name).value)

    def _param_str(self, name: str) -> str:
        return str(self.get_parameter(name).value)


def spin_node(node_factory):
    """Convenience entry point used by the per-sensor `main` functions."""

    rclpy.init()
    node = node_factory()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
