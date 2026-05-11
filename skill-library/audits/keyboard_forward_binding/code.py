# This snippet only publishes /cmd_vel_requested.
# The rover safety supervisor authorises actual motion via
# /cmd_vel_authorized. This code is not safety-certified.
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

KEY = "w"
LINEAR_SPEED_MPS = 0.20
PUBLISH_RATE_HZ = 10.0
WATCHDOG_SECONDS = 0.50


class KeyboardForwardBinding(Node):
    def __init__(self) -> None:
        super().__init__("keyboard_forward_binding")
        # NOTE: /cmd_vel_requested, not /cmd_vel.
        self.publisher = self.create_publisher(Twist, "/cmd_vel_requested", 10)
        self.timer = self.create_timer(1.0 / PUBLISH_RATE_HZ, self._tick)
        self.last_key_event = self.get_clock().now()
        self.key_held = False

    def on_key_down(self, key: str) -> None:
        if key == KEY:
            self.key_held = True
            self.last_key_event = self.get_clock().now()

    def on_key_up(self, key: str) -> None:
        if key == KEY:
            self.key_held = False

    def _tick(self) -> None:
        elapsed_since_event = (
            self.get_clock().now() - self.last_key_event
        ).nanoseconds * 1e-9
        if not self.key_held or elapsed_since_event > WATCHDOG_SECONDS:
            # Watchdog timeout: zero motion to /cmd_vel_requested.
            zero = Twist()
            self.publisher.publish(zero)
            return
        cmd = Twist()
        cmd.linear.x = LINEAR_SPEED_MPS
        self.publisher.publish(cmd)


def main() -> None:
    rclpy.init()
    node = KeyboardForwardBinding()
    try:
        rclpy.spin(node)
    finally:
        # Always send a final zero before exit.
        zero = Twist()
        node.publisher.publish(zero)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
