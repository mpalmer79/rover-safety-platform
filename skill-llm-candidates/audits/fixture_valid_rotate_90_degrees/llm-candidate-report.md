# LLM skill candidate audit: fixture_valid_rotate_90_degrees

_This LLM skill candidate is a development aid only. It does not represent autonomous execution, safety certification, or regulatory approval._

- **Provider mode:** `fixture`
- **Provider name:** `fixture-provider`
- **Provider status:** `proposed`
- **Final status:** `accepted`
- **Generated (UTC):** 2026-05-13T00:00:00+00:00

## Request

```text
Rotate left 90 degrees
```

## Candidate (untrusted)

- skill_type: `rotate_degrees`
- language: `python_ros2`
- confidence: `medium`
- declared topics: `/cmd_vel_requested`
- known uncertainties:
  - wheel slip on smooth flooring may distort the rotation

Candidate explanation:

> Rotate left 90 degrees by publishing /cmd_vel_requested at 0.4 rad/s for the computed duration, then a final zero Twist. The safety supervisor authorises the actual rotation. Do not publish to /cmd_vel directly.

## Sanitizer

- status: `accepted`
- accepted: True

## Validator bridge

- invoked: True
- accepted: True
- safety status: `safe_after_validation`

## Accepted code

```python
# Rotate left 90 degrees by publishing /cmd_vel_requested.
# Safety supervisor authorises actual motion. Not safety-certified.
import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

ANGLE_DEG = 90.0
DIRECTION_SIGN = 1.0
ANGULAR_SPEED_RAD_S = 0.4
PUBLISH_RATE_HZ = 10.0
ANGLE_RAD = math.radians(ANGLE_DEG)
DURATION_S = ANGLE_RAD / ANGULAR_SPEED_RAD_S
TIMEOUT_S = DURATION_S * 1.5

class Rotate(Node):
    def __init__(self):
        super().__init__('rotate_llm_candidate')
        self.publisher = self.create_publisher(Twist, '/cmd_vel_requested', 10)
        self.timer = self.create_timer(1.0 / PUBLISH_RATE_HZ, self._tick)
        self.start_time = self.get_clock().now()
        self.cmd = Twist()
        self.cmd.angular.z = DIRECTION_SIGN * ANGULAR_SPEED_RAD_S
        self.finished = False

    def _tick(self):
        elapsed = (self.get_clock().now() - self.start_time).nanoseconds * 1e-9
        if self.finished:
            return
        if elapsed >= DURATION_S or elapsed >= TIMEOUT_S:
            zero = Twist()
            self.publisher.publish(zero)
            self.finished = True
            return
        self.publisher.publish(self.cmd)

def main():
    rclpy.init()
    node = Rotate()
    while rclpy.ok() and not node.finished:
        rclpy.spin_once(node, timeout_sec=0.1)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

## Safety review

- safety_status: `safe_after_validation`
- risk_band: `guarded`
- allowed_topics: `/cmd_vel_requested`
- forbidden_topics: `/cmd_vel`
- reason_codes: `validation_passed`
- human_review_required: `False`
- notes:
  - Validated against Phase 15A REQUIRED_CODE_TOKENS for skill_type='rotate_degrees'.
  - Safety supervisor remains authoritative for actual motion.
  - This generated skill is an engineering development aid. It does not represent autonomous execution, safety certification, or regulatory approval.

## Authority statement

The deterministic skill validator and the runtime safety supervisor remain authoritative. This audit does not authorise actuator motion, regardless of the final status.
