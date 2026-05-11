# This snippet only publishes /cmd_vel_requested.
# The rover safety supervisor authorises actual motion via
# /cmd_vel_authorized. This code is not safety-certified.
import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

# --- bounded parameters -----------------------------------------------
ANGLE_DEG = 45.00            # requested angle magnitude
DIRECTION_SIGN = -1.0        # +1.0 = left, -1.0 = right
ANGULAR_SPEED_RAD_S = 0.40
PUBLISH_RATE_HZ = 10.0
ANGLE_RAD = math.radians(ANGLE_DEG)
DURATION_S = ANGLE_RAD / ANGULAR_SPEED_RAD_S
TIMEOUT_S = DURATION_S * 1.50


class RotateRequester(Node):
    def __init__(self) -> None:
        super().__init__("rotate_requester")
        # NOTE: /cmd_vel_requested, not /cmd_vel.
        self.publisher = self.create_publisher(Twist, "/cmd_vel_requested", 10)
        self.timer = self.create_timer(1.0 / PUBLISH_RATE_HZ, self._tick)
        self.start_time = self.get_clock().now()
        self.cmd = Twist()
        self.cmd.angular.z = DIRECTION_SIGN * ANGULAR_SPEED_RAD_S
        self.finished = False

    def _tick(self) -> None:
        elapsed = (self.get_clock().now() - self.start_time).nanoseconds * 1e-9
        if self.finished:
            return
        if elapsed >= DURATION_S or elapsed >= TIMEOUT_S:
            self._publish_zero_and_finish()
            return
        self.publisher.publish(self.cmd)

    def _publish_zero_and_finish(self) -> None:
        zero = Twist()
        self.publisher.publish(zero)
        self.finished = True
        self.get_logger().info("rotate complete; requested zero motion")


def main() -> None:
    rclpy.init()
    node = RotateRequester()
    try:
        while rclpy.ok() and not node.finished:
            rclpy.spin_once(node, timeout_sec=0.1)
    finally:
        node._publish_zero_and_finish()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
