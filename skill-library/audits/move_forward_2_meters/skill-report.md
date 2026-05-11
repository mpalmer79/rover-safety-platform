# Skill report: skill-move_forward_2_meters

_This generated skill is an engineering development aid. It does not represent autonomous execution, safety certification, or regulatory approval._

- **Skill type:** `move_forward_distance`
- **Language:** `python_ros2`
- **Title:** Move forward 2.0000 m
- **Subtitle:** Publishes /cmd_vel_requested at 0.25 m/s for 8.00 s, then zero.
- **Risk band:** `guarded`
- **Safety status:** `guarded`
- **Generated (UTC):** 2026-05-13T00:00:00+00:00

## Request

```text
Drive forward 2 meters
```

## Parameters

- `distance_meters` = `2.0` (m)
- `source_distance` = `2.0` (m)

## Generated code

```python
# This snippet only publishes /cmd_vel_requested.
# The rover safety supervisor authorises actual motion via
# /cmd_vel_authorized. This code is not safety-certified.
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

# --- bounded parameters -----------------------------------------------
DISTANCE_M = 2.0000           # requested distance
LINEAR_SPEED_MPS = 0.25        # conservative speed
PUBLISH_RATE_HZ = 10.0       # Twist publish rate
DURATION_S = DISTANCE_M / LINEAR_SPEED_MPS
TIMEOUT_S = DURATION_S * 1.50        # hard timeout guard


class MoveForwardRequester(Node):
    def __init__(self) -> None:
        super().__init__("move_forward_requester")
        # NOTE: /cmd_vel_requested, not /cmd_vel. The safety supervisor
        # validates this request and may clamp or reject it.
        self.publisher = self.create_publisher(Twist, "/cmd_vel_requested", 10)
        self.timer = self.create_timer(1.0 / PUBLISH_RATE_HZ, self._tick)
        self.start_time = self.get_clock().now()
        self.cmd = Twist()
        self.cmd.linear.x = LINEAR_SPEED_MPS
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
        self.get_logger().info("move_forward complete; requested zero motion")


def main() -> None:
    rclpy.init()
    node = MoveForwardRequester()
    try:
        rclpy.spin_until_future_complete(node, future=_finished_future(node))
    finally:
        # Always send a final zero to /cmd_vel_requested.
        node._publish_zero_and_finish()
        node.destroy_node()
        rclpy.shutdown()


def _finished_future(node):
    from rclpy.task import Future
    fut = Future()
    def check():
        if node.finished:
            fut.set_result(True)
    timer = node.create_timer(0.1, check)
    return fut


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
- Distance is a *request*; the supervisor may clamp or reject.

## Diagnostics

- [info] `request_accepted`: distance specified in meters
- [info] `validation_passed`: generated code passed safety validation

## Authority statement

This snippet publishes only requested-motion or mission topics. The safety supervisor and motion arbitration remain authoritative; no copy-paste of this code grants actuator authority.
