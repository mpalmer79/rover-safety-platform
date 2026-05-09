"""Run manager node.

Owns the run lifecycle for a ROS-driven simulation. Responsibilities:

* on startup, allocate (or accept) a ``run_id``, create the run
  directory, and publish a ``run_started`` :class:`rover_msgs/ReplayMarker`,
* periodically publish a ``checkpoint`` marker so replay tools can detect
  liveness,
* on shutdown, finalise the recorder and emit a ``run_finalized`` marker.

The node is intentionally narrow: it does not own any safety logic and
does not subscribe to ``/safety/state``. Run lifecycle is independent of
safety state.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSProfile, QoSReliabilityPolicy

from app.domain.enums import ReplayStatus
from app.domain.identifiers import RunId, ScenarioId
from rover_msgs.msg import ReplayMarker

from rover_observability.run_directory import finalise_run, open_run


class RunManagerNode(Node):
    def __init__(self) -> None:
        super().__init__("rover_run_manager")
        self.declare_parameter("run_id", "")
        self.declare_parameter("scenario_id", "unknown")
        self.declare_parameter("runs_root", str(Path.cwd() / "runs"))
        self.declare_parameter("checkpoint_period_s", 5.0)

        scenario_id = ScenarioId(str(self.get_parameter("scenario_id").value))
        run_id_param = str(self.get_parameter("run_id").value)
        runs_root = Path(str(self.get_parameter("runs_root").value))
        run_id = RunId(run_id_param) if run_id_param else None

        self._run_id, self._recorder = open_run(
            runs_root=runs_root,
            run_id=run_id,
            scenario_id=scenario_id,
        )

        latched = QoSProfile(
            depth=10,
            reliability=QoSReliabilityPolicy.RELIABLE,
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
        )
        self._marker_pub = self.create_publisher(
            ReplayMarker, "/replay/markers", latched
        )

        self._publish_marker(
            kind="run_started",
            label=f"run started run_id={self._run_id} scenario_id={scenario_id}",
            reason_code="run_started",
            payload={"runs_root": str(runs_root)},
        )
        self._publish_marker(
            kind="scenario_loaded",
            label=f"scenario {scenario_id}",
            reason_code="scenario_loaded",
            payload={},
        )

        period = max(0.5, float(self.get_parameter("checkpoint_period_s").value))
        self._timer = self.create_timer(period, self._on_checkpoint)
        self.get_logger().info(
            "rover_run_manager active. run_id=%s scenario_id=%s runs_root=%s",
            str(self._run_id),
            str(scenario_id),
            str(runs_root),
        )

    def _on_checkpoint(self) -> None:
        self._publish_marker(
            kind="checkpoint",
            label="checkpoint",
            reason_code="checkpoint",
            payload={},
        )

    def _publish_marker(
        self,
        *,
        kind: str,
        label: str,
        reason_code: str,
        payload: dict,
    ) -> None:
        msg = ReplayMarker()
        msg.stamp = self.get_clock().now().to_msg()
        msg.run_id = str(self._run_id)
        msg.scenario_id = str(self.get_parameter("scenario_id").value)
        msg.kind = kind
        msg.label = label
        msg.reason_code = reason_code
        msg.payload_json = json.dumps(payload, separators=(",", ":"))
        self._marker_pub.publish(msg)

    def destroy_node(self):  # pragma: no cover - rclpy lifecycle
        try:
            self._publish_marker(
                kind="run_finalized",
                label="run finalised",
                reason_code="run_finalized",
                payload={},
            )
            finalise_run(
                self._recorder,
                ended_sim_ns=int(self.get_clock().now().nanoseconds),
                status=ReplayStatus.FINALIZED,
            )
        except Exception:  # pragma: no cover - defensive shutdown
            self.get_logger().warn("Failed to finalise run cleanly.")
        return super().destroy_node()


def main() -> None:
    rclpy.init()
    node = RunManagerNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
