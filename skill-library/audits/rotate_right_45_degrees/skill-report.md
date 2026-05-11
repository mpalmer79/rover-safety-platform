# Skill report: skill-rotate_right_45_degrees

_This generated skill is an engineering development aid. It does not represent autonomous execution, safety certification, or regulatory approval._

- **Skill type:** `rotate_degrees`
- **Language:** `python_ros2`
- **Title:** Rotate right 45.00 deg
- **Subtitle:** Publishes /cmd_vel_requested at 0.40 rad/s for 1.96 s, then zero.
- **Risk band:** `guarded`
- **Safety status:** `guarded`
- **Generated (UTC):** 2026-05-13T00:00:00+00:00

## Request

```text
Turn right 45 degrees
```

## Parameters

- `angle_degrees` = `45.0` (deg)
- `direction` = `right` (unitless)

## Generated code

```python
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
- Safety supervisor authorises actual motion via /cmd_vel_authorized.
- Angle is a *request*; the supervisor may clamp or reject.

## Diagnostics

- [info] `request_accepted`: rotate right 45.0 degrees
- [info] `validation_passed`: generated code passed safety validation

## Authority statement

This snippet publishes only requested-motion or mission topics. The safety supervisor and motion arbitration remain authoritative; no copy-paste of this code grants actuator authority.
