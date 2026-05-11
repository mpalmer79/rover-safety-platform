# LLM skill candidate audit: fixture_valid_move_forward_6_feet

_This LLM skill candidate is a development aid only. It does not represent autonomous execution, safety certification, or regulatory approval._

- **Provider mode:** `fixture`
- **Provider name:** `fixture-provider`
- **Provider status:** `proposed`
- **Final status:** `accepted`
- **Generated (UTC):** 2026-05-13T00:00:00+00:00

## Request

```text
Move my robot 6 feet forward
```

## Candidate (untrusted)

- skill_type: `move_forward_distance`
- language: `python_ros2`
- confidence: `medium`
- declared topics: `/cmd_vel_requested`
- known uncertainties:
  - rover wheel slip may cause actual distance to differ

Candidate explanation:

> Move the rover forward 6 feet (~1.8288 m) by publishing /cmd_vel_requested at 0.25 m/s for the computed duration, then a final zero Twist. The safety supervisor must authorise the actual motion via /cmd_vel_authorized; the snippet must not publish to /cmd_vel directly. Never run this without operator supervision.

## Sanitizer

- status: `accepted`
- accepted: True

## Validator bridge

- invoked: True
- accepted: True
- safety status: `safe_after_validation`

## Accepted code

```python
# Move forward 1.8288 m by publishing /cmd_vel_requested.
# The safety supervisor authorises actual motion via
# /cmd_vel_authorized. This is not safety-certified.
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

DISTANCE_M = 1.8288
LINEAR_SPEED_MPS = 0.25
PUBLISH_RATE_HZ = 10.0
DURATION_S = DISTANCE_M / LINEAR_SPEED_MPS
TIMEOUT_S = DURATION_S * 1.5

class MoveForward(Node):
    def __init__(self):
        super().__init__('move_forward_llm_candidate')
        self.publisher = self.create_publisher(Twist, '/cmd_vel_requested', 10)
        self.timer = self.create_timer(1.0 / PUBLISH_RATE_HZ, self._tick)
        self.start_time = self.get_clock().now()
        self.cmd = Twist()
        self.cmd.linear.x = LINEAR_SPEED_MPS
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
    node = MoveForward()
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
  - Validated against Phase 15A REQUIRED_CODE_TOKENS for skill_type='move_forward_distance'.
  - Safety supervisor remains authoritative for actual motion.
  - This generated skill is an engineering development aid. It does not represent autonomous execution, safety certification, or regulatory approval.

## Authority statement

The deterministic skill validator and the runtime safety supervisor remain authoritative. This audit does not authorise actuator motion, regardless of the final status.
