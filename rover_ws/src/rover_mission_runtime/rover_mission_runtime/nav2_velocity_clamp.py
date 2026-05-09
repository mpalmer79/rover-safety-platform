"""Nav2 velocity-clamp boundary node.

This node is the architectural bridge that lets a Nav2 controller
participate in the platform without bypassing the safety supervisor.

The contract is:

* Nav2 publishes onto ``/cmd_vel_nav2`` (NOT ``/cmd_vel`` and NOT
  ``/cmd_vel_authorized``).
* This node subscribes to ``/cmd_vel_nav2`` and to
  ``/mission/state`` (for the orchestrator's effective per-state
  velocity envelope).
* The node clamps the Nav2 command to the envelope and republishes
  onto ``/cmd_vel_requested``.
* The safety bridge then arbitrates ``/cmd_vel_requested`` exactly as
  it would for any other mission-layer producer.

The safety supervisor still owns ``/cmd_vel_authorized``. The Gazebo
diff-drive plugin still subscribes only to ``/cmd_vel_authorized``.
There is no path by which a Nav2-published Twist could reach the
actuator interface unauthenticated.

The clamp itself uses the documented ``MotionConstraints`` for the
mission's current state: ``ACTIVE_NORMAL`` allows the configured
maximum, while ``MISSION_DEGRADED`` / ``MISSION_RECOVERY`` clamp to
their reduced envelopes. Operator pause/abort produces zero-velocity
output regardless of Nav2's command.
"""

from __future__ import annotations

from typing import Optional

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node

from rover_msgs.msg import MissionState as MissionStateMsg


_INPUT_TOPIC = "/cmd_vel_nav2"
_OUTPUT_TOPIC = "/cmd_vel_requested"

# Per-mission-state envelope in (linear, angular). Mirrors the
# mission orchestrator's defaults; deployments that override the
# orchestrator's constraints should pass parameters here so the two
# layers agree.
_DEFAULT_ENVELOPE: dict[str, tuple[float, float]] = {
    "MISSION_IDLE": (0.0, 0.0),
    "MISSION_PREPARING": (0.0, 0.0),
    "MISSION_ACTIVE": (0.5, 0.8),
    "MISSION_PAUSED": (0.0, 0.0),
    "MISSION_RECOVERY": (0.15, 0.4),
    "MISSION_DEGRADED": (0.15, 0.3),
    "MISSION_ABORTING": (0.0, 0.0),
    "MISSION_ABORTED": (0.0, 0.0),
    "MISSION_COMPLETE": (0.0, 0.0),
}


class Nav2VelocityClampNode(Node):
    def __init__(self) -> None:
        super().__init__("rover_nav2_velocity_clamp")
        self.declare_parameter("input_topic", _INPUT_TOPIC)
        self.declare_parameter("output_topic", _OUTPUT_TOPIC)
        self.declare_parameter("max_linear_velocity", 0.5)
        self.declare_parameter("max_angular_velocity", 0.8)

        self._latest_state = "MISSION_IDLE"
        self._envelope = dict(_DEFAULT_ENVELOPE)
        # Apply the configured maximums to ``MISSION_ACTIVE``.
        self._envelope["MISSION_ACTIVE"] = (
            float(self.get_parameter("max_linear_velocity").value),
            float(self.get_parameter("max_angular_velocity").value),
        )

        self._pub = self.create_publisher(
            Twist, str(self.get_parameter("output_topic").value), 10
        )
        self.create_subscription(
            Twist, str(self.get_parameter("input_topic").value), self._on_input, 10
        )
        self.create_subscription(
            MissionStateMsg, "/mission/state", self._on_state, 10
        )
        self.get_logger().info(
            "rover_nav2_velocity_clamp active. %s -> %s",
            self.get_parameter("input_topic").value,
            self.get_parameter("output_topic").value,
        )

    def _on_state(self, msg: MissionStateMsg) -> None:
        self._latest_state = msg.state

    def _on_input(self, msg: Twist) -> None:
        envelope = self._envelope.get(self._latest_state, (0.0, 0.0))
        clamped = Twist()
        clamped.linear.x = _clamp(msg.linear.x, envelope[0])
        clamped.angular.z = _clamp(msg.angular.z, envelope[1])
        self._pub.publish(clamped)


def _clamp(value: float, limit: float) -> float:
    if limit <= 0:
        return 0.0
    if value > limit:
        return limit
    if value < -limit:
        return -limit
    return float(value)


def main() -> None:
    rclpy.init()
    node = Nav2VelocityClampNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
