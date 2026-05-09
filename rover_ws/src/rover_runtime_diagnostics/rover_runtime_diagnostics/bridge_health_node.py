"""ros_gz_bridge health diagnostics node.

Combines :class:`app.diagnostics.TopicFreshnessMonitor` (for stream
ages) with the live ROS topic registry (for "is the bridge advertising
the topic at all?") into :class:`app.diagnostics.BridgeHealthMonitor`.
Publishes ``diagnostic_msgs/DiagnosticArray`` on
``/diagnostics/bridge_health`` and a structured JSON summary on
``/diagnostics/bridge_health_summary``.
"""

from __future__ import annotations

import json

import rclpy
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from rclpy.node import Node
from std_msgs.msg import String

from app.diagnostics import (
    BridgeHealthMonitor,
    DEFAULT_TOPIC_SPECS,
    TopicFreshnessMonitor,
)

from rover_runtime_diagnostics._publish import reports_to_diagnostic_status_payloads


class BridgeHealthNode(Node):
    def __init__(self) -> None:
        super().__init__("rover_bridge_health_diagnostics")
        self.declare_parameter("evaluation_period_ms", 1000)
        self._freshness = TopicFreshnessMonitor(specs=DEFAULT_TOPIC_SPECS)
        self._freshness.declare(now_ms=self._now_ms())
        self._monitor = BridgeHealthMonitor(self._freshness)

        self._diag_pub = self.create_publisher(
            DiagnosticArray, "/diagnostics/bridge_health", 10
        )
        self._summary_pub = self.create_publisher(
            String, "/diagnostics/bridge_health_summary", 10
        )

        period = max(0.5, float(self.get_parameter("evaluation_period_ms").value) / 1000.0)
        self._timer = self.create_timer(period, self._tick)

    def _tick(self) -> None:
        # Refresh the "advertised" view from the ROS registry. This is
        # cheap enough to do every second.
        advertised = {name for name, _ in self.get_topic_names_and_types()}
        for topic in self._monitor.required_topics:
            self._monitor.set_advertised(topic=topic, advertised=topic in advertised)

        report = self._monitor.report(now_ms=self._now_ms())

        diag = DiagnosticArray()
        diag.header.stamp = self.get_clock().now().to_msg()
        for payload in reports_to_diagnostic_status_payloads(
            hardware_id="ros_gz_bridge", reports=report.per_topic
        ):
            status = DiagnosticStatus()
            status.level = bytes([payload["level"]])
            status.name = payload["name"]
            status.message = payload["message"]
            status.hardware_id = payload["hardware_id"]
            status.values = [
                KeyValue(key=v["key"], value=v["value"]) for v in payload["values"]
            ]
            diag.status.append(status)
        self._diag_pub.publish(diag)

        summary = String()
        summary.data = json.dumps(report.to_dict(), separators=(",", ":"), sort_keys=True)
        self._summary_pub.publish(summary)

        if report.severity.value != "OK":
            self.get_logger().warn(report.summary)

    def _now_ms(self) -> int:
        return self.get_clock().now().nanoseconds // 1_000_000


def main() -> None:
    rclpy.init()
    node = BridgeHealthNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
