# LLM skill candidate audit: fixture_valid_stop_immediately

_This LLM skill candidate is a development aid only. It does not represent autonomous execution, safety certification, or regulatory approval._

- **Provider mode:** `fixture`
- **Provider name:** `fixture-provider`
- **Provider status:** `proposed`
- **Final status:** `accepted`
- **Generated (UTC):** 2026-05-13T00:00:00+00:00

## Request

```text
Stop the robot immediately
```

## Candidate (untrusted)

- skill_type: `stop_immediately`
- language: `python_ros2`
- confidence: `high`
- declared topics: `/cmd_vel_requested`

Candidate explanation:

> Publish five zero Twists to /cmd_vel_requested. This is an *immediate stop request*; the safety supervisor remains authoritative for actual deceleration. Never publish to /cmd_vel directly.

## Sanitizer

- status: `accepted`
- accepted: True

## Validator bridge

- invoked: True
- accepted: True
- safety status: `safe_after_validation`

## Accepted code

```python
# Stop immediately by publishing zero Twist to /cmd_vel_requested.
# Safety supervisor authorises actual deceleration. Not safety-certified.
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

PUBLISH_COUNT = 5
PUBLISH_RATE_HZ = 10.0

class Stop(Node):
    def __init__(self):
        super().__init__('stop_immediately_llm_candidate')
        self.publisher = self.create_publisher(Twist, '/cmd_vel_requested', 10)
        self.zero = Twist()
        self.remaining = PUBLISH_COUNT
        self.timer = self.create_timer(1.0 / PUBLISH_RATE_HZ, self._tick)

    def _tick(self):
        if self.remaining <= 0:
            self.timer.cancel()
            return
        self.publisher.publish(self.zero)
        self.remaining -= 1

def main():
    rclpy.init()
    node = Stop()
    while rclpy.ok() and node.remaining > 0:
        rclpy.spin_once(node, timeout_sec=0.1)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

## Safety review

- safety_status: `safe_after_validation`
- risk_band: `low`
- allowed_topics: `/cmd_vel_requested`
- forbidden_topics: `/cmd_vel`
- reason_codes: `validation_passed`
- human_review_required: `False`
- notes:
  - Validated against Phase 15A REQUIRED_CODE_TOKENS for skill_type='stop_immediately'.
  - Safety supervisor remains authoritative for actual motion.
  - This generated skill is an engineering development aid. It does not represent autonomous execution, safety certification, or regulatory approval.

## Authority statement

The deterministic skill validator and the runtime safety supervisor remain authoritative. This audit does not authorise actuator motion, regardless of the final status.
