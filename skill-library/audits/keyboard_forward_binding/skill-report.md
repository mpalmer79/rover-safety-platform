# Skill report: skill-keyboard_forward_binding

_This generated skill is an engineering development aid. It does not represent autonomous execution, safety certification, or regulatory approval._

- **Skill type:** `keyboard_forward_binding`
- **Language:** `python_ros2`
- **Title:** Bind keyboard key 'w' to forward motion
- **Subtitle:** Publishes /cmd_vel_requested while held; zeroes on release.
- **Risk band:** `guarded`
- **Safety status:** `guarded`
- **Generated (UTC):** 2026-05-13T00:00:00+00:00

## Request

```text
Bind keyboard key 'w' to move forward
```

## Parameters

- `key` = `w` (unitless)

## Generated code

```python
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
```

## Safety review

- allowed topics: /cmd_vel_requested
- forbidden topics: /cmd_vel
- human review required: False
- reason codes: validation_passed

Notes:
- Uses /cmd_vel_requested instead of /cmd_vel.
- Final zero command is sent.
- Safety supervisor remains authoritative for actual motion.
- Command expires after the computed duration.
- Generated snippet uses a polled loop; integrate with your input library.
- Safety supervisor remains authoritative for actual motion.

## Diagnostics

- [info] `request_accepted`: keyboard key 'w' bound to forward motion
- [info] `validation_passed`: generated code passed safety validation

## Authority statement

This snippet publishes only requested-motion or mission topics. The safety supervisor and motion arbitration remain authoritative; no copy-paste of this code grants actuator authority.
