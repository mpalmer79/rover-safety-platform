# Skill report: skill-stop_immediately

_This generated skill is an engineering development aid. It does not represent autonomous execution, safety certification, or regulatory approval._

- **Skill type:** `stop_immediately`
- **Language:** `python_ros2`
- **Title:** Stop immediately
- **Subtitle:** Publishes 5 zero Twists to /cmd_vel_requested.
- **Risk band:** `low`
- **Safety status:** `safe_template`
- **Generated (UTC):** 2026-05-13T00:00:00+00:00

## Request

```text
Stop the robot immediately
```

## Parameters

_(none)_

## Generated code

```python
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
- An immediate stop request still flows through the safety supervisor.

## Diagnostics

- [info] `request_accepted`: stop request recognised
- [info] `validation_passed`: generated code passed safety validation

## Authority statement

This snippet publishes only requested-motion or mission topics. The safety supervisor and motion arbitration remain authoritative; no copy-paste of this code grants actuator authority.
