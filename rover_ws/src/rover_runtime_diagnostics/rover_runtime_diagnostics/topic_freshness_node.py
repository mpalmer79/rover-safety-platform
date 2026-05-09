"""Topic freshness diagnostics node.

Subscribes to the documented runtime topics, feeds observations into
:class:`app.diagnostics.TopicFreshnessMonitor`, and publishes a
``diagnostic_msgs/DiagnosticArray`` on ``/diagnostics/topic_freshness``
plus a structured ``std_msgs/String`` JSON payload on
``/diagnostics/topic_freshness_summary`` for Foxglove dashboards.
"""

from __future__ import annotations

import json
from typing import Any

import rclpy
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rosgraph_msgs.msg import Clock
from sensor_msgs.msg import Imu, LaserScan
from std_msgs.msg import Bool, String

from app.diagnostics import (
    DEFAULT_TOPIC_SPECS,
    TopicFreshnessMonitor,
)
from rover_msgs.msg import SafetyState as SafetyStateMsg

from rover_runtime_diagnostics._publish import (
    reports_to_diagnostic_status_payloads,
    severity_to_diagnostic_level,
)


class TopicFreshnessNode(Node):
    def __init__(self) -> None:
        super().__init__("rover_topic_freshness_diagnostics")
        self.declare_parameter("evaluation_period_ms", 250)
        self._monitor = TopicFreshnessMonitor(specs=DEFAULT_TOPIC_SPECS)
        self._monitor.declare(now_ms=self._now_ms())

        self._diag_pub = self.create_publisher(
            DiagnosticArray, "/diagnostics/topic_freshness", 10
        )
        self._summary_pub = self.create_publisher(
            String, "/diagnostics/topic_freshness_summary", 10
        )

        self.create_subscription(Clock, "/clock", self._on_clock, 50)
        self.create_subscription(LaserScan, "/scan", self._on_scan, 10)
        self.create_subscription(Imu, "/imu", self._on_imu, 20)
        self.create_subscription(Odometry, "/odom", self._on_odom, 20)
        self.create_subscription(Bool, "/contact", self._on_contact, 10)
        self.create_subscription(Twist, "/cmd_vel_authorized", self._on_authorized, 10)
        self.create_subscription(SafetyStateMsg, "/safety/state", self._on_safety_state, 10)
        self.create_subscription(String, "/safety/events", self._on_safety_events, 50)

        period = max(0.05, float(self.get_parameter("evaluation_period_ms").value) / 1000.0)
        self._timer = self.create_timer(period, self._tick)

    # --------------------------------------------------------------
    # Subscriber callbacks. Each one only feeds the monitor; no logic.
    # --------------------------------------------------------------
    def _on_clock(self, _msg: Clock) -> None:
        self._monitor.observe(topic="/clock", now_ms=self._now_ms())

    def _on_scan(self, _msg: LaserScan) -> None:
        self._monitor.observe(topic="/scan", now_ms=self._now_ms())

    def _on_imu(self, _msg: Imu) -> None:
        self._monitor.observe(topic="/imu", now_ms=self._now_ms())

    def _on_odom(self, _msg: Odometry) -> None:
        self._monitor.observe(topic="/odom", now_ms=self._now_ms())

    def _on_contact(self, _msg: Bool) -> None:
        self._monitor.observe(topic="/contact", now_ms=self._now_ms())

    def _on_authorized(self, _msg: Twist) -> None:
        self._monitor.observe(topic="/cmd_vel_authorized", now_ms=self._now_ms())

    def _on_safety_state(self, _msg: SafetyStateMsg) -> None:
        self._monitor.observe(topic="/safety/state", now_ms=self._now_ms())

    def _on_safety_events(self, _msg: String) -> None:
        self._monitor.observe(topic="/safety/events", now_ms=self._now_ms())

    # --------------------------------------------------------------
    # Tick.
    # --------------------------------------------------------------
    def _tick(self) -> None:
        report = self._monitor.report(now_ms=self._now_ms())

        diag = DiagnosticArray()
        diag.header.stamp = self.get_clock().now().to_msg()
        for payload in reports_to_diagnostic_status_payloads(
            hardware_id="rover", reports=report.per_topic
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

    # --------------------------------------------------------------
    # Helpers.
    # --------------------------------------------------------------
    def _now_ms(self) -> int:
        return self.get_clock().now().nanoseconds // 1_000_000


def main() -> None:
    rclpy.init()
    node = TopicFreshnessNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
