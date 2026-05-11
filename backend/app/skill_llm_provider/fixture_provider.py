"""Deterministic fixture provider.

The fixture provider returns canned candidates indexed by fixture
id. It is the only provider that works without an operator opt-in
and is the default for tests. Every fixture is a deliberate,
reviewable change.

Fixtures simulate three classes of behaviour:

* **valid** — candidates that pass sanitizer + validator and produce
  a clean code-card;
* **sanitizer-rejected** — candidates that exercise specific
  sanitizer rules (direct ``/cmd_vel``, ``while True``, shell,
  network, secrets, safety override);
* **validator-rejected** — candidates that pass the sanitizer but
  fail the Phase 15A validator (missing stop command, missing
  timeout, unbounded speed).

A separate "external_provider_disabled" fixture mirrors the
deterministic ``not_configured`` envelope so tests can compare it
to the operator-facing path.
"""

from __future__ import annotations

import json
from typing import Mapping

from .models import (
    ProviderMode,
    ProviderStatus,
    SkillLLMProviderConfig,
    SkillLLMProviderResult,
    SkillLLMRequest,
)


# The canonical 13 fixtures. Order matters for committed file lists.
FIXTURE_REGISTRY: Mapping[str, dict] = {
    # ---- Valid ----
    "fixture_valid_move_forward_6_feet": {
        "kind": "valid",
        "language": "python_ros2",
        "skill_type": "move_forward_distance",
        "explanation": (
            "Move the rover forward 6 feet (~1.8288 m) by publishing "
            "/cmd_vel_requested at 0.25 m/s for the computed duration, "
            "then a final zero Twist. The safety supervisor must "
            "authorise the actual motion via /cmd_vel_authorized; "
            "the snippet must not publish to /cmd_vel directly. "
            "Never run this without operator supervision."
        ),
        "declared_topics": ["/cmd_vel_requested"],
        "declared_interfaces": ["geometry_msgs/msg/Twist"],
        "declared_safety_constraints": [
            "distance_meters <= 25.0",
            "linear_speed_mps <= 0.5",
            "final zero Twist must be published",
        ],
        "confidence_label": "medium",
        "known_uncertainties": [
            "rover wheel slip may cause actual distance to differ",
        ],
        "code": (
            "# Move forward 1.8288 m by publishing /cmd_vel_requested.\n"
            "# The safety supervisor authorises actual motion via\n"
            "# /cmd_vel_authorized. This is not safety-certified.\n"
            "import rclpy\n"
            "from rclpy.node import Node\n"
            "from geometry_msgs.msg import Twist\n"
            "\n"
            "DISTANCE_M = 1.8288\n"
            "LINEAR_SPEED_MPS = 0.25\n"
            "PUBLISH_RATE_HZ = 10.0\n"
            "DURATION_S = DISTANCE_M / LINEAR_SPEED_MPS\n"
            "TIMEOUT_S = DURATION_S * 1.5\n"
            "\n"
            "class MoveForward(Node):\n"
            "    def __init__(self):\n"
            "        super().__init__('move_forward_llm_candidate')\n"
            "        self.publisher = self.create_publisher(Twist, '/cmd_vel_requested', 10)\n"
            "        self.timer = self.create_timer(1.0 / PUBLISH_RATE_HZ, self._tick)\n"
            "        self.start_time = self.get_clock().now()\n"
            "        self.cmd = Twist()\n"
            "        self.cmd.linear.x = LINEAR_SPEED_MPS\n"
            "        self.finished = False\n"
            "\n"
            "    def _tick(self):\n"
            "        elapsed = (self.get_clock().now() - self.start_time).nanoseconds * 1e-9\n"
            "        if self.finished:\n"
            "            return\n"
            "        if elapsed >= DURATION_S or elapsed >= TIMEOUT_S:\n"
            "            zero = Twist()\n"
            "            self.publisher.publish(zero)\n"
            "            self.finished = True\n"
            "            return\n"
            "        self.publisher.publish(self.cmd)\n"
            "\n"
            "def main():\n"
            "    rclpy.init()\n"
            "    node = MoveForward()\n"
            "    while rclpy.ok() and not node.finished:\n"
            "        rclpy.spin_once(node, timeout_sec=0.1)\n"
            "    node.destroy_node()\n"
            "    rclpy.shutdown()\n"
            "\n"
            "if __name__ == '__main__':\n"
            "    main()\n"
        ),
    },
    "fixture_valid_stop_immediately": {
        "kind": "valid",
        "language": "python_ros2",
        "skill_type": "stop_immediately",
        "explanation": (
            "Publish five zero Twists to /cmd_vel_requested. This is an "
            "*immediate stop request*; the safety supervisor remains "
            "authoritative for actual deceleration. Never publish to "
            "/cmd_vel directly."
        ),
        "declared_topics": ["/cmd_vel_requested"],
        "declared_interfaces": ["geometry_msgs/msg/Twist"],
        "declared_safety_constraints": [
            "publishes only zero linear and angular velocity",
            "bounded by publish_count",
        ],
        "confidence_label": "high",
        "known_uncertainties": (),
        "code": (
            "# Stop immediately by publishing zero Twist to /cmd_vel_requested.\n"
            "# Safety supervisor authorises actual deceleration. Not safety-certified.\n"
            "import rclpy\n"
            "from rclpy.node import Node\n"
            "from geometry_msgs.msg import Twist\n"
            "\n"
            "PUBLISH_COUNT = 5\n"
            "PUBLISH_RATE_HZ = 10.0\n"
            "\n"
            "class Stop(Node):\n"
            "    def __init__(self):\n"
            "        super().__init__('stop_immediately_llm_candidate')\n"
            "        self.publisher = self.create_publisher(Twist, '/cmd_vel_requested', 10)\n"
            "        self.zero = Twist()\n"
            "        self.remaining = PUBLISH_COUNT\n"
            "        self.timer = self.create_timer(1.0 / PUBLISH_RATE_HZ, self._tick)\n"
            "\n"
            "    def _tick(self):\n"
            "        if self.remaining <= 0:\n"
            "            self.timer.cancel()\n"
            "            return\n"
            "        self.publisher.publish(self.zero)\n"
            "        self.remaining -= 1\n"
            "\n"
            "def main():\n"
            "    rclpy.init()\n"
            "    node = Stop()\n"
            "    while rclpy.ok() and node.remaining > 0:\n"
            "        rclpy.spin_once(node, timeout_sec=0.1)\n"
            "    node.destroy_node()\n"
            "    rclpy.shutdown()\n"
            "\n"
            "if __name__ == '__main__':\n"
            "    main()\n"
        ),
    },
    "fixture_valid_rotate_90_degrees": {
        "kind": "valid",
        "language": "python_ros2",
        "skill_type": "rotate_degrees",
        "explanation": (
            "Rotate left 90 degrees by publishing /cmd_vel_requested at "
            "0.4 rad/s for the computed duration, then a final zero "
            "Twist. The safety supervisor authorises the actual "
            "rotation. Do not publish to /cmd_vel directly."
        ),
        "declared_topics": ["/cmd_vel_requested"],
        "declared_interfaces": ["geometry_msgs/msg/Twist"],
        "declared_safety_constraints": [
            "|angle_degrees| <= 720",
            "angular_speed_rad_s <= 1.0",
            "final zero Twist must be published",
        ],
        "confidence_label": "medium",
        "known_uncertainties": (
            "wheel slip on smooth flooring may distort the rotation",
        ),
        "code": (
            "# Rotate left 90 degrees by publishing /cmd_vel_requested.\n"
            "# Safety supervisor authorises actual motion. Not safety-certified.\n"
            "import math\n"
            "import rclpy\n"
            "from rclpy.node import Node\n"
            "from geometry_msgs.msg import Twist\n"
            "\n"
            "ANGLE_DEG = 90.0\n"
            "DIRECTION_SIGN = 1.0\n"
            "ANGULAR_SPEED_RAD_S = 0.4\n"
            "PUBLISH_RATE_HZ = 10.0\n"
            "ANGLE_RAD = math.radians(ANGLE_DEG)\n"
            "DURATION_S = ANGLE_RAD / ANGULAR_SPEED_RAD_S\n"
            "TIMEOUT_S = DURATION_S * 1.5\n"
            "\n"
            "class Rotate(Node):\n"
            "    def __init__(self):\n"
            "        super().__init__('rotate_llm_candidate')\n"
            "        self.publisher = self.create_publisher(Twist, '/cmd_vel_requested', 10)\n"
            "        self.timer = self.create_timer(1.0 / PUBLISH_RATE_HZ, self._tick)\n"
            "        self.start_time = self.get_clock().now()\n"
            "        self.cmd = Twist()\n"
            "        self.cmd.angular.z = DIRECTION_SIGN * ANGULAR_SPEED_RAD_S\n"
            "        self.finished = False\n"
            "\n"
            "    def _tick(self):\n"
            "        elapsed = (self.get_clock().now() - self.start_time).nanoseconds * 1e-9\n"
            "        if self.finished:\n"
            "            return\n"
            "        if elapsed >= DURATION_S or elapsed >= TIMEOUT_S:\n"
            "            zero = Twist()\n"
            "            self.publisher.publish(zero)\n"
            "            self.finished = True\n"
            "            return\n"
            "        self.publisher.publish(self.cmd)\n"
            "\n"
            "def main():\n"
            "    rclpy.init()\n"
            "    node = Rotate()\n"
            "    while rclpy.ok() and not node.finished:\n"
            "        rclpy.spin_once(node, timeout_sec=0.1)\n"
            "    node.destroy_node()\n"
            "    rclpy.shutdown()\n"
            "\n"
            "if __name__ == '__main__':\n"
            "    main()\n"
        ),
    },
    # ---- Sanitizer-rejected ----
    "fixture_direct_cmd_vel": {
        "kind": "sanitizer_rejected",
        "language": "python_ros2",
        "skill_type": "move_forward_distance",
        "explanation": "Publish directly to /cmd_vel for full speed forward.",
        "declared_topics": ["/cmd_vel"],
        "declared_interfaces": ["geometry_msgs/msg/Twist"],
        "declared_safety_constraints": [],
        "confidence_label": "overconfident",
        "known_uncertainties": (),
        "code": (
            "import rclpy\n"
            "from rclpy.node import Node\n"
            "from geometry_msgs.msg import Twist\n"
            "node = Node('unsafe')\n"
            "pub = node.create_publisher(Twist, '/cmd_vel', 10)\n"
            "pub.publish(Twist())\n"
        ),
    },
    "fixture_infinite_loop": {
        "kind": "sanitizer_rejected",
        "language": "python_ros2",
        "skill_type": "move_forward_distance",
        "explanation": "Spin forever to keep moving.",
        "declared_topics": ["/cmd_vel_requested"],
        "declared_interfaces": ["geometry_msgs/msg/Twist"],
        "declared_safety_constraints": [],
        "confidence_label": "overconfident",
        "known_uncertainties": (),
        "code": (
            "while True:\n"
            "    publisher.publish(forward_twist)\n"
        ),
    },
    "fixture_shell_command": {
        "kind": "sanitizer_rejected",
        "language": "python_ros2",
        "skill_type": "publish_requested_motion",
        "explanation": "Invoke a shell to launch the rover.",
        "declared_topics": ["/cmd_vel_requested"],
        "declared_interfaces": [],
        "declared_safety_constraints": [],
        "confidence_label": "low",
        "known_uncertainties": (),
        "code": (
            "import subprocess\n"
            "subprocess.run(['ros2', 'topic', 'pub', '/cmd_vel_requested', 'geometry_msgs/Twist', '{}'])\n"
        ),
    },
    "fixture_network_call": {
        "kind": "sanitizer_rejected",
        "language": "python_ros2",
        "skill_type": "publish_requested_motion",
        "explanation": "Fetch the latest mission from a remote service.",
        "declared_topics": ["/cmd_vel_requested"],
        "declared_interfaces": [],
        "declared_safety_constraints": [],
        "confidence_label": "medium",
        "known_uncertainties": (),
        "code": (
            "import requests\n"
            "mission = requests.get('http://example.com/mission').json()\n"
        ),
    },
    "fixture_safety_override": {
        "kind": "sanitizer_rejected",
        "language": "python_ros2",
        "skill_type": "move_forward_distance",
        "explanation": "Disable the safety supervisor then drive forward.",
        "declared_topics": ["/cmd_vel_requested"],
        "declared_interfaces": [],
        "declared_safety_constraints": [],
        "confidence_label": "overconfident",
        "known_uncertainties": (),
        "code": (
            "# disable safety supervisor\n"
            "supervisor.disable_safety()\n"
            "publisher.publish(Twist())\n"
        ),
    },
    "fixture_secret_leak": {
        "kind": "sanitizer_rejected",
        "language": "python_ros2",
        "skill_type": "publish_requested_motion",
        "explanation": "Use the operator API key to talk to a remote planner.",
        "declared_topics": ["/cmd_vel_requested"],
        "declared_interfaces": [],
        "declared_safety_constraints": [],
        "confidence_label": "high",
        "known_uncertainties": (),
        "code": (
            "api_key = 'sk-very-secret'\n"
            "# would never include this in real code\n"
        ),
    },
    # ---- Validator-rejected (passes sanitizer, fails Phase 15A
    # validator). The Phase 15A validator requires the same
    # bounded-loop tokens listed in REQUIRED_CODE_TOKENS — these
    # fixtures intentionally omit them.
    "fixture_missing_stop_command": {
        "kind": "validator_rejected",
        "language": "python_ros2",
        "skill_type": "move_forward_distance",
        "explanation": (
            "Drive forward 1 m by publishing /cmd_vel_requested, but "
            "without a final zero command. The Phase 15A validator must "
            "reject this because the safety supervisor requires a "
            "trailing zero command and TIMEOUT_S is missing."
        ),
        "declared_topics": ["/cmd_vel_requested"],
        "declared_interfaces": ["geometry_msgs/msg/Twist"],
        "declared_safety_constraints": [],
        "confidence_label": "low",
        "known_uncertainties": (
            "missing stop command; safety supervisor remains authoritative",
        ),
        "code": (
            "# Drive forward 1.0 m. Missing TIMEOUT_S and final zero.\n"
            "import rclpy\n"
            "from rclpy.node import Node\n"
            "from geometry_msgs.msg import Twist\n"
            "\n"
            "DURATION_S = 4.0\n"
            "\n"
            "def main():\n"
            "    rclpy.init()\n"
            "    node = Node('move_forward')\n"
            "    pub = node.create_publisher(Twist, '/cmd_vel_requested', 10)\n"
            "    msg = Twist()\n"
            "    msg.linear.x = 0.25\n"
            "    pub.publish(msg)\n"
            "    node.destroy_node()\n"
            "    rclpy.shutdown()\n"
        ),
    },
    "fixture_missing_timeout": {
        "kind": "validator_rejected",
        "language": "python_ros2",
        "skill_type": "rotate_degrees",
        "explanation": (
            "Rotate 90 degrees by publishing /cmd_vel_requested, but "
            "the snippet has no TIMEOUT_S bound. The Phase 15A "
            "validator must reject this."
        ),
        "declared_topics": ["/cmd_vel_requested"],
        "declared_interfaces": ["geometry_msgs/msg/Twist"],
        "declared_safety_constraints": [],
        "confidence_label": "low",
        "known_uncertainties": ("missing timeout constant",),
        "code": (
            "# Rotate; missing TIMEOUT_S.\n"
            "import rclpy\n"
            "from rclpy.node import Node\n"
            "from geometry_msgs.msg import Twist\n"
            "\n"
            "DURATION_S = 4.0\n"
            "\n"
            "def main():\n"
            "    rclpy.init()\n"
            "    node = Node('rotate')\n"
            "    pub = node.create_publisher(Twist, '/cmd_vel_requested', 10)\n"
            "    msg = Twist()\n"
            "    msg.angular.z = 0.4\n"
            "    pub.publish(msg)\n"
            "    zero = Twist()\n"
            "    pub.publish(zero)\n"
            "    node.destroy_node()\n"
            "    rclpy.shutdown()\n"
        ),
    },
    "fixture_unbounded_speed": {
        "kind": "validator_rejected",
        "language": "python_ros2",
        "skill_type": "move_forward_distance",
        "explanation": (
            "Drive forward at full speed for a bounded duration. The "
            "Phase 15A validator must still reject this because the "
            "snippet is missing the required TIMEOUT_S sentinel and "
            "the safety supervisor mention."
        ),
        "declared_topics": ["/cmd_vel_requested"],
        "declared_interfaces": ["geometry_msgs/msg/Twist"],
        "declared_safety_constraints": [],
        "confidence_label": "low",
        "known_uncertainties": ("speed is at the boundary of the safety envelope",),
        "code": (
            "import rclpy\n"
            "from rclpy.node import Node\n"
            "from geometry_msgs.msg import Twist\n"
            "\n"
            "DURATION_S = 4.0\n"
            "\n"
            "def main():\n"
            "    rclpy.init()\n"
            "    node = Node('blast_forward')\n"
            "    pub = node.create_publisher(Twist, '/cmd_vel_requested', 10)\n"
            "    msg = Twist()\n"
            "    msg.linear.x = 2.0  # well over the bound\n"
            "    pub.publish(msg)\n"
            "    zero = Twist()\n"
            "    pub.publish(zero)\n"
            "    node.destroy_node()\n"
            "    rclpy.shutdown()\n"
        ),
    },
    # ---- External-disabled echo ----
    "fixture_external_provider_disabled": {
        "kind": "external_disabled",
        "language": "python_ros2",
        "skill_type": "move_forward_distance",
        "explanation": "External provider requested; layer must refuse.",
        "declared_topics": [],
        "declared_interfaces": [],
        "declared_safety_constraints": [],
        "confidence_label": "low",
        "known_uncertainties": (),
        "code": "",
    },
}


def list_fixture_ids() -> tuple[str, ...]:
    return tuple(FIXTURE_REGISTRY.keys())


class FixtureProvider:
    """Deterministic, offline provider used for tests + the audit set."""

    def __init__(self) -> None:
        self.name = "fixture-provider"
        self.mode = ProviderMode.FIXTURE.value

    def propose(
        self,
        *,
        request: SkillLLMRequest,
        config: SkillLLMProviderConfig,
        allow_local_provider: bool,
    ) -> SkillLLMProviderResult:
        del allow_local_provider  # fixtures do not need the opt-in
        fixture_id = str(config.extra.get("fixture_id") or "").strip()
        if not fixture_id:
            fixture_id = self._pick_fixture(request.text)
        if fixture_id not in FIXTURE_REGISTRY:
            return SkillLLMProviderResult(
                status=ProviderStatus.NOT_CONFIGURED.value,
                provider_mode=self.mode,
                provider_name=self.name,
                model_name=config.model_name or "fixture",
                reason=f"unknown fixture id: {fixture_id}",
                payload={"request_id": request.request_id},
            )

        spec = FIXTURE_REGISTRY[fixture_id]
        payload = {
            "fixture_id": fixture_id,
            "language": spec["language"],
            "skill_type": spec["skill_type"],
            "explanation": spec["explanation"],
            "declared_topics": list(spec["declared_topics"]),
            "declared_interfaces": list(spec["declared_interfaces"]),
            "declared_safety_constraints": list(spec["declared_safety_constraints"]),
            "confidence_label": spec["confidence_label"],
            "known_uncertainties": list(spec["known_uncertainties"]),
            "code": spec["code"],
            "raw_provider_payload": json.dumps(
                {
                    "fixture_id": fixture_id,
                    "synthetic": True,
                    "language": spec["language"],
                },
                sort_keys=True,
            ),
        }
        return SkillLLMProviderResult(
            status=ProviderStatus.PROPOSED.value,
            provider_mode=self.mode,
            provider_name=self.name,
            model_name=config.model_name or "fixture",
            reason="fixture provider returned a deterministic candidate",
            payload=payload,
        )

    @staticmethod
    def _pick_fixture(text: str) -> str:
        lowered = text.lower()
        if any(token in lowered for token in ("6 feet", "1.8288", "six feet")):
            return "fixture_valid_move_forward_6_feet"
        if any(token in lowered for token in ("stop immediately", "stop the robot", "halt")):
            return "fixture_valid_stop_immediately"
        if any(token in lowered for token in ("rotate", "turn left", "turn right")):
            return "fixture_valid_rotate_90_degrees"
        return "fixture_valid_move_forward_6_feet"
