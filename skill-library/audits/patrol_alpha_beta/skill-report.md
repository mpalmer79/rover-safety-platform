# Skill report: skill-patrol_alpha_beta

_This generated skill is an engineering development aid. It does not represent autonomous execution, safety certification, or regulatory approval._

- **Skill type:** `patrol_route_template`
- **Language:** `python_ros2`
- **Title:** Request patrol of 2 named waypoints
- **Subtitle:** Publishes a patrol mission request to /mission/patrol_request.
- **Risk band:** `low`
- **Safety status:** `safe_template`
- **Generated (UTC):** 2026-05-13T00:00:00+00:00

## Request

```text
Patrol alpha beta
```

## Parameters

- `waypoints` = `('alpha', 'beta')` (unitless)

## Generated code

```python
# This snippet only publishes /cmd_vel_requested.
# The rover safety supervisor authorises actual motion via
# /cmd_vel_authorized. This code is not safety-certified.
import json
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

MISSION_TOPIC = "/mission/patrol_request"
WAYPOINTS = ["alpha","beta"]


def main() -> None:
    rclpy.init()
    node = Node("patrol_requester")
    # NOTE: publishes a mission request, not an actuator command.
    publisher = node.create_publisher(String, MISSION_TOPIC, 10)
    msg = String()
    msg.data = json.dumps({"waypoints": WAYPOINTS})
    publisher.publish(msg)
    node.get_logger().info("requested patrol route")
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
```

## Safety review

- allowed topics: /mission/patrol_request
- forbidden topics: /cmd_vel, /cmd_vel_requested
- human review required: False
- reason codes: validation_passed

Notes:
- Uses /cmd_vel_requested instead of /cmd_vel.
- No motion is published.
- Safety supervisor remains authoritative for actual motion.
- Mission runtime sequences the waypoints; the snippet does not move the rover.

## Diagnostics

- [info] `request_accepted`: patrol route with 2 named waypoints
- [info] `validation_passed`: generated code passed safety validation

## Authority statement

This snippet publishes only requested-motion or mission topics. The safety supervisor and motion arbitration remain authoritative; no copy-paste of this code grants actuator authority.
