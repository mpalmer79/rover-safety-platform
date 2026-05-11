"""Code templates for each supported skill.

Templates are pure-Python string builders. They never invoke any
runtime; they emit copyable text. Each builder receives validated
parameters and returns (code_text, title, subtitle).

Every generated motion snippet:

* publishes to ``/cmd_vel_requested`` (never directly to
  ``/cmd_vel``);
* uses a bounded loop driven by a duration or count;
* sends a final zero ``Twist`` before exiting;
* mentions the safety supervisor in a comment header.
"""

from __future__ import annotations

from typing import Mapping, Sequence

from .models import (
    SkillLanguage,
    SkillParameter,
    SkillType,
)


_NON_AUTHORITY_HEADER = (
    "# This snippet only publishes /cmd_vel_requested.\n"
    "# The rover safety supervisor authorises actual motion via\n"
    "# /cmd_vel_authorized. This code is not safety-certified."
)


def _param_dict(params: Sequence[SkillParameter]) -> dict:
    return {p.name: p.value for p in params}


def _move_forward_python(params: Sequence[SkillParameter], defaults: Mapping[str, object]) -> tuple[str, str, str]:
    p = _param_dict(params)
    distance = float(p["distance_meters"])  # type: ignore[arg-type]
    linear_speed = float(defaults.get("linear_speed_mps", 0.25))
    publish_rate = float(defaults.get("publish_rate_hz", 10.0))
    margin = float(defaults.get("timeout_safety_margin", 1.5))
    duration = distance / linear_speed
    timeout = duration * margin
    title = f"Move forward {distance:.4f} m"
    subtitle = (
        f"Publishes /cmd_vel_requested at {linear_speed:.2f} m/s for "
        f"{duration:.2f} s, then zero."
    )

    code = f"""{_NON_AUTHORITY_HEADER}
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

# --- bounded parameters -----------------------------------------------
DISTANCE_M = {distance:.4f}           # requested distance
LINEAR_SPEED_MPS = {linear_speed:.2f}        # conservative speed
PUBLISH_RATE_HZ = {publish_rate:.1f}       # Twist publish rate
DURATION_S = DISTANCE_M / LINEAR_SPEED_MPS
TIMEOUT_S = DURATION_S * {margin:.2f}        # hard timeout guard


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
"""
    return code, title, subtitle


def _rotate_python(params: Sequence[SkillParameter], defaults: Mapping[str, object]) -> tuple[str, str, str]:
    p = _param_dict(params)
    angle_deg = float(p["angle_degrees"])  # type: ignore[arg-type]
    direction = str(p["direction"])
    angular_speed = float(defaults.get("angular_speed_rad_s", 0.4))
    publish_rate = float(defaults.get("publish_rate_hz", 10.0))
    margin = float(defaults.get("timeout_safety_margin", 1.5))
    angle_rad = abs(angle_deg) * 3.141592653589793 / 180.0
    duration = angle_rad / angular_speed
    timeout = duration * margin
    sign = 1.0 if direction == "left" else -1.0
    title = f"Rotate {direction} {angle_deg:.2f} deg"
    subtitle = (
        f"Publishes /cmd_vel_requested at {angular_speed:.2f} rad/s for "
        f"{duration:.2f} s, then zero."
    )

    code = f"""{_NON_AUTHORITY_HEADER}
import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

# --- bounded parameters -----------------------------------------------
ANGLE_DEG = {abs(angle_deg):.2f}            # requested angle magnitude
DIRECTION_SIGN = {sign:.1f}        # +1.0 = left, -1.0 = right
ANGULAR_SPEED_RAD_S = {angular_speed:.2f}
PUBLISH_RATE_HZ = {publish_rate:.1f}
ANGLE_RAD = math.radians(ANGLE_DEG)
DURATION_S = ANGLE_RAD / ANGULAR_SPEED_RAD_S
TIMEOUT_S = DURATION_S * {margin:.2f}


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
"""
    return code, title, subtitle


def _stop_python(params: Sequence[SkillParameter], defaults: Mapping[str, object]) -> tuple[str, str, str]:
    publish_count = int(defaults.get("publish_count", 5))
    publish_rate = float(defaults.get("publish_rate_hz", 10.0))
    title = "Stop immediately"
    subtitle = f"Publishes {publish_count} zero Twists to /cmd_vel_requested."

    code = f"""{_NON_AUTHORITY_HEADER}
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

PUBLISH_COUNT = {publish_count}
PUBLISH_RATE_HZ = {publish_rate:.1f}


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
"""
    return code, title, subtitle


def _publish_requested_motion_python(params: Sequence[SkillParameter], defaults: Mapping[str, object]) -> tuple[str, str, str]:
    p = _param_dict(params)
    linear_x = float(p.get("linear_x_mps", 0.2))
    angular_z = float(p.get("angular_z_rad_s", 0.0))
    title = "Publish a single requested-motion command"
    subtitle = f"Publishes one Twist (lin={linear_x:.2f}, ang={angular_z:.2f}) to /cmd_vel_requested."

    code = f"""{_NON_AUTHORITY_HEADER}
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


def main() -> None:
    rclpy.init()
    node = Node("requested_motion_publisher")
    # NOTE: /cmd_vel_requested, not /cmd_vel.
    publisher = node.create_publisher(Twist, "/cmd_vel_requested", 10)
    msg = Twist()
    msg.linear.x = {linear_x:.2f}
    msg.angular.z = {angular_z:.2f}
    publisher.publish(msg)
    node.get_logger().info("requested-motion command published")
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
"""
    return code, title, subtitle


def _keyboard_python(params: Sequence[SkillParameter], defaults: Mapping[str, object]) -> tuple[str, str, str]:
    p = _param_dict(params)
    key = str(p["key"])
    linear_speed = float(defaults.get("linear_speed_mps", 0.2))
    publish_rate = float(defaults.get("publish_rate_hz", 10.0))
    watchdog = float(defaults.get("watchdog_seconds", 0.5))
    title = f"Bind keyboard key '{key}' to forward motion"
    subtitle = "Publishes /cmd_vel_requested while held; zeroes on release."

    code = f"""{_NON_AUTHORITY_HEADER}
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

KEY = "{key}"
LINEAR_SPEED_MPS = {linear_speed:.2f}
PUBLISH_RATE_HZ = {publish_rate:.1f}
WATCHDOG_SECONDS = {watchdog:.2f}


class KeyboardForwardBinding(Node):
    def __init__(self) -> None:
        super().__init__("keyboard_forward_binding")
        # NOTE: /cmd_vel_requested, not /cmd_vel.
        self.publisher = self.create_publisher(Twist, "/cmd_vel_requested", 10)
        self.timer = self.create_timer(1.0 / PUBLISH_RATE_HZ, self._tick)
        self.last_key_event = self.get_clock().now()
        self.key_held = False

    def on_key_down(self, key: str) -> None:
        if key == KEY:
            self.key_held = True
            self.last_key_event = self.get_clock().now()

    def on_key_up(self, key: str) -> None:
        if key == KEY:
            self.key_held = False

    def _tick(self) -> None:
        elapsed_since_event = (
            self.get_clock().now() - self.last_key_event
        ).nanoseconds * 1e-9
        if not self.key_held or elapsed_since_event > WATCHDOG_SECONDS:
            # Watchdog timeout: zero motion to /cmd_vel_requested.
            zero = Twist()
            self.publisher.publish(zero)
            return
        cmd = Twist()
        cmd.linear.x = LINEAR_SPEED_MPS
        self.publisher.publish(cmd)


def main() -> None:
    rclpy.init()
    node = KeyboardForwardBinding()
    try:
        rclpy.spin(node)
    finally:
        # Always send a final zero before exit.
        zero = Twist()
        node.publisher.publish(zero)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
"""
    return code, title, subtitle


def _controller_python(params: Sequence[SkillParameter], defaults: Mapping[str, object]) -> tuple[str, str, str]:
    p = _param_dict(params)
    button = str(p["button"])
    verb = str(p.get("verb", "move"))
    linear_speed = float(defaults.get("linear_speed_mps", 0.2))
    publish_rate = float(defaults.get("publish_rate_hz", 10.0))
    watchdog = float(defaults.get("watchdog_seconds", 0.5))
    title = f"Bind controller button '{button}' to {verb}"
    subtitle = "Publishes /cmd_vel_requested while held; zeroes on release."
    linear_when_pressed = 0.0 if verb == "stop" else linear_speed

    code = f"""{_NON_AUTHORITY_HEADER}
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

BUTTON = "{button}"
VERB = "{verb}"
LINEAR_SPEED_MPS = {linear_when_pressed:.2f}
PUBLISH_RATE_HZ = {publish_rate:.1f}
WATCHDOG_SECONDS = {watchdog:.2f}


class ControllerButtonBinding(Node):
    def __init__(self) -> None:
        super().__init__("controller_button_binding")
        # NOTE: /cmd_vel_requested, not /cmd_vel.
        self.publisher = self.create_publisher(Twist, "/cmd_vel_requested", 10)
        self.timer = self.create_timer(1.0 / PUBLISH_RATE_HZ, self._tick)
        self.last_button_event = self.get_clock().now()
        self.button_held = False

    def on_button_event(self, button: str, pressed: bool) -> None:
        if button == BUTTON:
            self.button_held = pressed
            self.last_button_event = self.get_clock().now()

    def _tick(self) -> None:
        elapsed_since_event = (
            self.get_clock().now() - self.last_button_event
        ).nanoseconds * 1e-9
        cmd = Twist()
        if (
            not self.button_held
            or elapsed_since_event > WATCHDOG_SECONDS
        ):
            self.publisher.publish(cmd)  # zero
            return
        cmd.linear.x = LINEAR_SPEED_MPS
        self.publisher.publish(cmd)


def main() -> None:
    rclpy.init()
    node = ControllerButtonBinding()
    try:
        rclpy.spin(node)
    finally:
        zero = Twist()
        node.publisher.publish(zero)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
"""
    return code, title, subtitle


def _waypoint_python(params: Sequence[SkillParameter], defaults: Mapping[str, object]) -> tuple[str, str, str]:
    p = _param_dict(params)
    waypoint_id = str(p["waypoint_id"])
    mission_topic = str(defaults.get("mission_topic", "/mission/waypoint_request"))
    title = f"Request waypoint '{waypoint_id}'"
    subtitle = f"Publishes a mission request to {mission_topic}."

    code = f"""{_NON_AUTHORITY_HEADER}
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

MISSION_TOPIC = "{mission_topic}"
WAYPOINT_ID = "{waypoint_id}"


def main() -> None:
    rclpy.init()
    node = Node("waypoint_requester")
    # NOTE: publishes a mission request, not an actuator command.
    publisher = node.create_publisher(String, MISSION_TOPIC, 10)
    msg = String()
    msg.data = WAYPOINT_ID
    publisher.publish(msg)
    node.get_logger().info(f"requested waypoint {{WAYPOINT_ID}}")
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
"""
    return code, title, subtitle


def _patrol_python(params: Sequence[SkillParameter], defaults: Mapping[str, object]) -> tuple[str, str, str]:
    p = _param_dict(params)
    waypoints = tuple(p["waypoints"])  # type: ignore[arg-type]
    mission_topic = str(defaults.get("mission_topic", "/mission/patrol_request"))
    title = f"Request patrol of {len(waypoints)} named waypoints"
    subtitle = f"Publishes a patrol mission request to {mission_topic}."

    body_list = ",".join(f'"{w}"' for w in waypoints)
    code = f"""{_NON_AUTHORITY_HEADER}
import json
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

MISSION_TOPIC = "{mission_topic}"
WAYPOINTS = [{body_list}]


def main() -> None:
    rclpy.init()
    node = Node("patrol_requester")
    # NOTE: publishes a mission request, not an actuator command.
    publisher = node.create_publisher(String, MISSION_TOPIC, 10)
    msg = String()
    msg.data = json.dumps({{"waypoints": WAYPOINTS}})
    publisher.publish(msg)
    node.get_logger().info("requested patrol route")
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
"""
    return code, title, subtitle


def _safe_stop_wrapper_python(params: Sequence[SkillParameter], defaults: Mapping[str, object]) -> tuple[str, str, str]:
    publish_count = int(defaults.get("publish_count", 3))
    publish_rate = float(defaults.get("publish_rate_hz", 10.0))
    title = "Safe-stop wrapper for /cmd_vel_requested"
    subtitle = "Context manager that zeroes motion on exit, exception, or KeyboardInterrupt."

    code = f"""{_NON_AUTHORITY_HEADER}
from contextlib import contextmanager
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

PUBLISH_COUNT = {publish_count}
PUBLISH_RATE_HZ = {publish_rate:.1f}


@contextmanager
def safe_stop(node: Node):
    # NOTE: publishes only zero Twists to /cmd_vel_requested.
    publisher = node.create_publisher(Twist, "/cmd_vel_requested", 10)
    try:
        yield publisher
    finally:
        zero = Twist()
        for _ in range(PUBLISH_COUNT):
            publisher.publish(zero)
        node.get_logger().info("safe_stop: requested zero motion on exit")


def main() -> None:
    rclpy.init()
    node = Node("safe_stop_wrapper_demo")
    try:
        with safe_stop(node) as publisher:
            # The developer's bounded motion request would go here.
            # The wrapper guarantees a final zero, even on exception.
            pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
"""
    return code, title, subtitle


_BUILDERS: dict[tuple[str, str], object] = {
    (SkillType.MOVE_FORWARD_DISTANCE.value, SkillLanguage.PYTHON_ROS2.value): _move_forward_python,
    (SkillType.ROTATE_DEGREES.value, SkillLanguage.PYTHON_ROS2.value): _rotate_python,
    (SkillType.STOP_IMMEDIATELY.value, SkillLanguage.PYTHON_ROS2.value): _stop_python,
    (SkillType.PUBLISH_REQUESTED_MOTION.value, SkillLanguage.PYTHON_ROS2.value): _publish_requested_motion_python,
    (SkillType.KEYBOARD_FORWARD_BINDING.value, SkillLanguage.PYTHON_ROS2.value): _keyboard_python,
    (SkillType.CONTROLLER_BUTTON_BINDING.value, SkillLanguage.PYTHON_ROS2.value): _controller_python,
    (SkillType.WAYPOINT_REQUEST.value, SkillLanguage.PYTHON_ROS2.value): _waypoint_python,
    (SkillType.PATROL_ROUTE_TEMPLATE.value, SkillLanguage.PYTHON_ROS2.value): _patrol_python,
    (SkillType.SAFE_STOP_WRAPPER.value, SkillLanguage.PYTHON_ROS2.value): _safe_stop_wrapper_python,
}


def render_template(
    *,
    skill_type: str,
    language: str,
    params: Sequence[SkillParameter],
    defaults: Mapping[str, object],
) -> tuple[str, str, str]:
    """Render code for ``(skill_type, language)`` with the given parameters.

    Returns ``(code, title, subtitle)``. Raises ``KeyError`` if no
    builder exists for the requested combination.
    """

    key = (skill_type, language)
    builder = _BUILDERS.get(key)
    if builder is None:
        raise KeyError(f"no template for {key}")
    return builder(params, defaults)  # type: ignore[operator]


def supported_template_keys() -> tuple[tuple[str, str], ...]:
    return tuple(sorted(_BUILDERS.keys()))
