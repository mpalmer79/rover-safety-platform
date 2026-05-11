# Skill report: skill-waypoint_alpha_request

_This generated skill is an engineering development aid. It does not represent autonomous execution, safety certification, or regulatory approval._

- **Skill type:** `waypoint_request`
- **Language:** `python_ros2`
- **Title:** Request waypoint 'alpha'
- **Subtitle:** Publishes a mission request to /mission/waypoint_request.
- **Risk band:** `low`
- **Safety status:** `safe_template`
- **Generated (UTC):** 2026-05-13T00:00:00+00:00

## Request

```text
Go to waypoint alpha
```

## Parameters

- `waypoint_id` = `alpha` (unitless)

## Generated code

```python
# This snippet only publishes /cmd_vel_requested.
# The rover safety supervisor authorises actual motion via
# /cmd_vel_authorized. This code is not safety-certified.
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

MISSION_TOPIC = "/mission/waypoint_request"
WAYPOINT_ID = "alpha"


def main() -> None:
    rclpy.init()
    node = Node("waypoint_requester")
    # NOTE: publishes a mission request, not an actuator command.
    publisher = node.create_publisher(String, MISSION_TOPIC, 10)
    msg = String()
    msg.data = WAYPOINT_ID
    publisher.publish(msg)
    node.get_logger().info(f"requested waypoint {WAYPOINT_ID}")
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
```

## Safety review

- allowed topics: /mission/waypoint_request
- forbidden topics: /cmd_vel, /cmd_vel_requested
- human review required: False
- reason codes: validation_passed

Notes:
- Uses /cmd_vel_requested instead of /cmd_vel.
- No motion is published.
- Safety supervisor remains authoritative for actual motion.
- Mission runtime decides whether to act; safety supervisor authorises motion.

## Diagnostics

- [info] `request_accepted`: waypoint 'alpha' request
- [info] `validation_passed`: generated code passed safety validation

## Authority statement

This snippet publishes only requested-motion or mission topics. The safety supervisor and motion arbitration remain authoritative; no copy-paste of this code grants actuator authority.
