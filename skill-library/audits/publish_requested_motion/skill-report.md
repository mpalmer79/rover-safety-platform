# Skill report: skill-publish_requested_motion

_This generated skill is an engineering development aid. It does not represent autonomous execution, safety certification, or regulatory approval._

- **Skill type:** `publish_requested_motion`
- **Language:** `python_ros2`
- **Title:** Publish a single requested-motion command
- **Subtitle:** Publishes one Twist (lin=0.20, ang=0.00) to /cmd_vel_requested.
- **Risk band:** `guarded`
- **Safety status:** `guarded`
- **Generated (UTC):** 2026-05-13T00:00:00+00:00

## Request

```text
Publish a requested-motion command
```

## Parameters

- `linear_x_mps` = `0.2` (m/s)
- `angular_z_rad_s` = `0.0` (rad/s)

## Generated code

```python
# This snippet only publishes /cmd_vel_requested.
# The rover safety supervisor authorises actual motion via
# /cmd_vel_authorized. This code is not safety-certified.
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


def main() -> None:
    rclpy.init()
    node = Node("requested_motion_publisher")
    # NOTE: /cmd_vel_requested, not /cmd_vel.
    publisher = node.create_publisher(Twist, "/cmd_vel_requested", 10)
    msg = Twist()
    msg.linear.x = 0.20
    msg.angular.z = 0.00
    publisher.publish(msg)
    node.get_logger().info("requested-motion command published")
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
- No motion is published.
- Safety supervisor remains authoritative for actual motion.
- Single publication; caller decides cadence and timeout.
- Safety supervisor remains authoritative.

## Diagnostics

- [info] `request_accepted`: single requested-motion publication
- [info] `validation_passed`: generated code passed safety validation

## Authority statement

This snippet publishes only requested-motion or mission topics. The safety supervisor and motion arbitration remain authoritative; no copy-paste of this code grants actuator authority.
