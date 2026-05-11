# This snippet only publishes /cmd_vel_requested.
# The rover safety supervisor authorises actual motion via
# /cmd_vel_authorized. This code is not safety-certified.
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

BUTTON = "a"
VERB = "stop"
LINEAR_SPEED_MPS = 0.00
PUBLISH_RATE_HZ = 10.0
WATCHDOG_SECONDS = 0.50


class ControllerButtonBinding(Node):
    def __init__(self) -> None:
        super().__init__("controller_button_binding")
        # NOTE: /cmd_vel_requested, not /cmd_vel.
        self.publisher = self.create_publisher(Twist, "/cmd_vel_requested", 10)
        self.timer = self.create_timer(1.0 / PUBLISH_RATE_HZ, self._tick)
        self.last_button_event = self.get_clock().now()
        self.button_held = False

    def on_button_event(self, button: str, pressed: bool) -> None:
        if button == BUTTON:
            self.button_held = pressed
            self.last_button_event = self.get_clock().now()

    def _tick(self) -> None:
        elapsed_since_event = (
            self.get_clock().now() - self.last_button_event
        ).nanoseconds * 1e-9
        cmd = Twist()
        if (
            not self.button_held
            or elapsed_since_event > WATCHDOG_SECONDS
        ):
            self.publisher.publish(cmd)  # zero
            return
        cmd.linear.x = LINEAR_SPEED_MPS
        self.publisher.publish(cmd)


def main() -> None:
    rclpy.init()
    node = ControllerButtonBinding()
    try:
        rclpy.spin(node)
    finally:
        zero = Twist()
        node.publisher.publish(zero)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
