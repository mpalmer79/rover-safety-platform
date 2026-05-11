# This snippet only publishes /cmd_vel_requested.
# The rover safety supervisor authorises actual motion via
# /cmd_vel_authorized. This code is not safety-certified.
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

PUBLISH_COUNT = 5
PUBLISH_RATE_HZ = 10.0


class StopRequester(Node):
    def __init__(self) -> None:
        super().__init__("stop_requester")
        # NOTE: /cmd_vel_requested, not /cmd_vel.
        self.publisher = self.create_publisher(Twist, "/cmd_vel_requested", 10)
        self.zero = Twist()
        self.remaining = PUBLISH_COUNT
        self.timer = self.create_timer(1.0 / PUBLISH_RATE_HZ, self._tick)

    def _tick(self) -> None:
        if self.remaining <= 0:
            self.timer.cancel()
            return
        self.publisher.publish(self.zero)
        self.remaining -= 1


def main() -> None:
    rclpy.init()
    node = StopRequester()
    try:
        while rclpy.ok() and node.remaining > 0:
            rclpy.spin_once(node, timeout_sec=0.1)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
