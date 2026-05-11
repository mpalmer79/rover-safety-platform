# Skill report: skill-controller_stop_button

_This generated skill is an engineering development aid. It does not represent autonomous execution, safety certification, or regulatory approval._

- **Skill type:** `controller_button_binding`
- **Language:** `python_ros2`
- **Title:** Bind controller button 'a' to stop
- **Subtitle:** Publishes /cmd_vel_requested while held; zeroes on release.
- **Risk band:** `guarded`
- **Safety status:** `guarded`
- **Generated (UTC):** 2026-05-13T00:00:00+00:00

## Request

```text
Controller button to stop
```

## Parameters

- `button` = `a` (unitless)
- `verb` = `stop` (unitless)

## Generated code

```python
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
- Generated snippet expects a Joy / sensor_msgs subscriber.
- Safety supervisor remains authoritative for actual motion.

## Diagnostics

- [info] `request_accepted`: controller button 'a' bound to stop
- [info] `validation_passed`: generated code passed safety validation

## Authority statement

This snippet publishes only requested-motion or mission topics. The safety supervisor and motion arbitration remain authoritative; no copy-paste of this code grants actuator authority.
