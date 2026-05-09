"""Runtime summary aggregator.

Subscribes to the per-component summary topics published by the other
diagnostic nodes (topic freshness, bridge health, TF validator) and
publishes a single aggregated ``/diagnostics/runtime_summary`` JSON
record plus a structured ``rover_msgs/SystemHealth`` message.

The summary is the operator's single pane of glass into runtime
liveliness. It does not subscribe to ``/safety/state`` for the
purpose of changing diagnostics behaviour — diagnostics monitor
liveliness; the supervisor owns safety.
"""

from __future__ import annotations

import json
from typing import Any, Optional

import rclpy
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from rclpy.node import Node
from std_msgs.msg import String

from app.diagnostics import (
    HealthReport,
    HealthSeverity,
    aggregate_health,
)
from rover_msgs.msg import SafetyState as SafetyStateMsg, SystemHealth


_SEVERITY_TO_EVENT_SEVERITY = {
    HealthSeverity.OK: "INFO",
    HealthSeverity.WARN: "WARNING",
    HealthSeverity.ERROR: "ERROR",
    HealthSeverity.CRITICAL: "CRITICAL",
}


class RuntimeSummaryNode(Node):
    def __init__(self) -> None:
        super().__init__("rover_runtime_summary")
        self.declare_parameter("evaluation_period_s", 1.0)
        self.declare_parameter("run_id", "unknown")
        self.declare_parameter("scenario_id", "unknown")

        self._latest_topic_summary: Optional[dict] = None
        self._latest_bridge_summary: Optional[dict] = None
        self._latest_tf_summary: Optional[dict] = None
        self._latest_safety_state: Optional[SafetyStateMsg] = None

        self.create_subscription(
            String, "/diagnostics/topic_freshness_summary", self._on_topic, 10
        )
        self.create_subscription(
            String, "/diagnostics/bridge_health_summary", self._on_bridge, 10
        )
        self.create_subscription(
            String, "/diagnostics/tf_validator_summary", self._on_tf, 10
        )
        self.create_subscription(
            SafetyStateMsg, "/safety/state", self._on_safety_state, 10
        )

        self._summary_pub = self.create_publisher(
            String, "/diagnostics/runtime_summary", 10
        )
        self._system_health_pub = self.create_publisher(
            SystemHealth, "/system/health", 10
        )

        period = max(0.5, float(self.get_parameter("evaluation_period_s").value))
        self._timer = self.create_timer(period, self._tick)

    # ------------------------------------------------------------------
    def _on_topic(self, msg: String) -> None:
        self._latest_topic_summary = self._safe_json(msg.data)

    def _on_bridge(self, msg: String) -> None:
        self._latest_bridge_summary = self._safe_json(msg.data)

    def _on_tf(self, msg: String) -> None:
        self._latest_tf_summary = self._safe_json(msg.data)

    def _on_safety_state(self, msg: SafetyStateMsg) -> None:
        self._latest_safety_state = msg

    # ------------------------------------------------------------------
    def _tick(self) -> None:
        reports: list[HealthReport] = []
        for source, payload in (
            ("topic_freshness", self._latest_topic_summary),
            ("bridge_health", self._latest_bridge_summary),
            ("tf_validator", self._latest_tf_summary),
        ):
            if payload is None:
                reports.append(
                    HealthReport(
                        component=f"summary:{source}",
                        severity=HealthSeverity.WARN,
                        summary=f"awaiting first {source} summary",
                    )
                )
                continue
            severity = HealthSeverity(payload.get("severity", "OK"))
            reports.append(
                HealthReport(
                    component=f"summary:{source}",
                    severity=severity,
                    summary=payload.get("summary", source),
                    attributes={"raw": json.dumps(payload, sort_keys=True)},
                )
            )

        runtime = aggregate_health(reports)
        summary_msg = String()
        summary_msg.data = json.dumps(
            {
                "severity": runtime.severity.value,
                "components": [r.to_dict() for r in runtime.reports],
            },
            separators=(",", ":"),
            sort_keys=True,
        )
        self._summary_pub.publish(summary_msg)

        # SystemHealth message for the standard health topic.
        system = SystemHealth()
        system.stamp = self.get_clock().now().to_msg()
        system.run_id = str(self.get_parameter("run_id").value)
        system.scenario_id = str(self.get_parameter("scenario_id").value)
        system.severity = _SEVERITY_TO_EVENT_SEVERITY[runtime.severity]
        system.any_input_unhealthy = runtime.severity != HealthSeverity.OK
        # Bridge / watchdog signals are populated lazily from the bridge
        # summary when present.
        bridge = self._latest_bridge_summary or {}
        system.expired_watchdogs = []
        if isinstance(bridge.get("per_topic"), list):
            unhealthy_topics = [
                r["component"].replace("bridge:", "")
                for r in bridge["per_topic"]
                if r.get("severity") not in (HealthSeverity.OK.value, "OK")
            ]
            system.summary = (
                f"runtime severity {runtime.severity.value}; "
                f"unhealthy bridge topics: {','.join(unhealthy_topics) or 'none'}"
            )
        else:
            system.summary = f"runtime severity {runtime.severity.value}"
        # Per-stream ages are best-effort: we read them from the topic
        # freshness summary.
        topic = self._latest_topic_summary or {}
        ages = {"lidar": -1, "imu": -1, "wheel_encoder": -1, "contact": -1}
        if isinstance(topic.get("per_topic"), list):
            for entry in topic["per_topic"]:
                attrs = entry.get("attributes") or {}
                age = attrs.get("age_ms")
                if not isinstance(age, int):
                    continue
                if entry.get("component") == "topic:/scan":
                    ages["lidar"] = age
                elif entry.get("component") == "topic:/imu":
                    ages["imu"] = age
                elif entry.get("component") == "topic:/odom":
                    ages["wheel_encoder"] = age
                elif entry.get("component") == "topic:/contact":
                    ages["contact"] = age
        system.lidar_age_ms = ages["lidar"]
        system.imu_age_ms = ages["imu"]
        system.encoder_age_ms = ages["wheel_encoder"]
        system.contact_age_ms = ages["contact"]
        system.any_watchdog_expired = False
        system.confidence_score = (
            float(self._latest_safety_state.confidence_score)
            if self._latest_safety_state is not None
            else -1.0
        )
        self._system_health_pub.publish(system)

        if runtime.severity != HealthSeverity.OK:
            self.get_logger().warn(summary_msg.data)

    @staticmethod
    def _safe_json(text: str) -> Optional[dict]:
        try:
            value = json.loads(text)
        except json.JSONDecodeError:
            return None
        return value if isinstance(value, dict) else None


def main() -> None:
    rclpy.init()
    node = RuntimeSummaryNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
