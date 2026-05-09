"""Live TF tree validator.

Periodically inspects the TF graph and verifies that the documented
frames are present and connected. The node does not own a tf2 buffer
of its own; instead, it queries ``rclpy.Node.get_topic_names_and_types``
to confirm ``/tf`` and ``/tf_static`` are advertised, and uses the
URDF parser in :mod:`app.validation.tf_validator` to assert the
expected static topology.

Runtime TF correctness (transforms actually flowing) is monitored by
the topic freshness node via the ``/tf`` topic. This node is the
**static** half of the check.
"""

from __future__ import annotations

import json
from pathlib import Path

import rclpy
from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
from rclpy.node import Node
from std_msgs.msg import String

from app.diagnostics import HealthReport, HealthSeverity
from app.validation.tf_validator import validate_urdf_tf_tree

from rover_runtime_diagnostics._publish import reports_to_diagnostic_status_payloads


class TfValidatorNode(Node):
    def __init__(self) -> None:
        super().__init__("rover_tf_validator")
        self.declare_parameter(
            "urdf_path", "share/rover_description/urdf/rover.urdf.xacro"
        )
        self.declare_parameter("evaluation_period_s", 5.0)

        self._diag_pub = self.create_publisher(
            DiagnosticArray, "/diagnostics/tf_validator", 10
        )
        self._summary_pub = self.create_publisher(
            String, "/diagnostics/tf_validator_summary", 10
        )

        period = max(1.0, float(self.get_parameter("evaluation_period_s").value))
        self._timer = self.create_timer(period, self._tick)

    def _tick(self) -> None:
        urdf_path = Path(str(self.get_parameter("urdf_path").value))
        result = validate_urdf_tf_tree(urdf_path)

        reports: list[HealthReport] = []
        if not urdf_path.exists():
            reports.append(
                HealthReport(
                    component="tf:urdf",
                    severity=HealthSeverity.ERROR,
                    summary=f"URDF not found at {urdf_path}",
                )
            )
        else:
            severity = HealthSeverity.OK if result.ok else HealthSeverity.ERROR
            reports.append(
                HealthReport(
                    component="tf:urdf",
                    severity=severity,
                    summary=(
                        "URDF tree valid"
                        if result.ok
                        else f"URDF tree invalid ({len(result.errors)} error(s))"
                    ),
                    detail=("\n".join(result.errors) if result.errors else ""),
                    attributes={"links": len(result.links), "joints": len(result.joints)},
                )
            )

        # Live evidence: /tf and /tf_static must be advertised once
        # Gazebo and robot_state_publisher are up.
        advertised = {name for name, _ in self.get_topic_names_and_types()}
        for topic, severity_when_missing in (
            ("/tf", HealthSeverity.ERROR),
            ("/tf_static", HealthSeverity.WARN),
        ):
            present = topic in advertised
            reports.append(
                HealthReport(
                    component=f"tf:{topic}",
                    severity=HealthSeverity.OK if present else severity_when_missing,
                    summary=(
                        f"{topic} advertised"
                        if present
                        else f"{topic} not advertised"
                    ),
                )
            )

        diag = DiagnosticArray()
        diag.header.stamp = self.get_clock().now().to_msg()
        for payload in reports_to_diagnostic_status_payloads(
            hardware_id="rover", reports=reports
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
        summary.data = json.dumps(
            {
                "urdf_ok": result.ok,
                "urdf_errors": list(result.errors),
                "urdf_warnings": list(result.warnings),
                "advertised": sorted(t for t in ("/tf", "/tf_static") if t in advertised),
            },
            separators=(",", ":"),
            sort_keys=True,
        )
        self._summary_pub.publish(summary)


def main() -> None:
    rclpy.init()
    node = TfValidatorNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
