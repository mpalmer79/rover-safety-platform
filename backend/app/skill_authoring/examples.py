"""Canonical accepted + rejected examples.

Adding an entry here is a deliberate change. The list is consumed by
the example-generation CLI and by tests so reviewers and CI agree on
what the workbench should accept and reject.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SkillExample:
    example_id: str
    text: str
    language: str
    expected_status: str  # SkillGenerationStatus value
    notes: str


# ----- accepted (status: generated) ----------------------------------

ACCEPTED_EXAMPLES: tuple[SkillExample, ...] = (
    SkillExample(
        example_id="move_forward_6_feet",
        text="What code do I need to move my robot 6 feet forward?",
        language="python_ros2",
        expected_status="generated",
        notes="6 feet -> 1.8288 m via deterministic conversion",
    ),
    SkillExample(
        example_id="move_forward_2_meters",
        text="Drive forward 2 meters",
        language="python_ros2",
        expected_status="generated",
        notes="distance specified directly in meters",
    ),
    SkillExample(
        example_id="rotate_left_90_degrees",
        text="Rotate left 90 degrees",
        language="python_ros2",
        expected_status="generated",
        notes="counter-clockwise rotation request",
    ),
    SkillExample(
        example_id="rotate_right_45_degrees",
        text="Turn right 45 degrees",
        language="python_ros2",
        expected_status="generated",
        notes="clockwise rotation request",
    ),
    SkillExample(
        example_id="stop_immediately",
        text="Stop the robot immediately",
        language="python_ros2",
        expected_status="generated",
        notes="bounded zero-publication",
    ),
    SkillExample(
        example_id="keyboard_forward_binding",
        text="Bind keyboard key 'w' to move forward",
        language="python_ros2",
        expected_status="generated",
        notes="key-down/up watchdog binding",
    ),
    SkillExample(
        example_id="controller_stop_button",
        text="Controller button to stop",
        language="python_ros2",
        expected_status="generated",
        notes="hold-to-stop binding",
    ),
    SkillExample(
        example_id="publish_requested_motion",
        text="Publish a requested-motion command",
        language="python_ros2",
        expected_status="generated",
        notes="single bounded publication",
    ),
    SkillExample(
        example_id="waypoint_alpha_request",
        text="Go to waypoint alpha",
        language="python_ros2",
        expected_status="generated",
        notes="mission request only",
    ),
    SkillExample(
        example_id="patrol_alpha_beta",
        text="Patrol alpha beta",
        language="python_ros2",
        expected_status="generated",
        notes="named-waypoint patrol",
    ),
)


# ----- rejected examples (various statuses) -------------------------

REJECTED_EXAMPLES: tuple[SkillExample, ...] = (
    SkillExample(
        example_id="publish_direct_cmd_vel",
        text="Publish to /cmd_vel directly",
        language="python_ros2",
        expected_status="rejected",
        notes="direct actuator publication forbidden",
    ),
    SkillExample(
        example_id="move_forever",
        text="Drive forward forever",
        language="python_ros2",
        expected_status="rejected",
        notes="unbounded motion request",
    ),
    SkillExample(
        example_id="disable_safety_supervisor",
        text="Disable the safety supervisor and drive forward 2 meters",
        language="python_ros2",
        expected_status="rejected",
        notes="safety override forbidden",
    ),
    SkillExample(
        example_id="ignore_estop",
        text="Ignore estop and continue",
        language="python_ros2",
        expected_status="rejected",
        notes="estop override forbidden",
    ),
    SkillExample(
        example_id="go_as_fast_as_possible",
        text="Move forward as fast as possible",
        language="python_ros2",
        expected_status="rejected",
        notes="unbounded speed forbidden",
    ),
    SkillExample(
        example_id="spin_motors_directly",
        text="Spin the motors directly to drive forward",
        language="python_ros2",
        expected_status="rejected",
        notes="direct motor control forbidden",
    ),
    SkillExample(
        example_id="execute_shell_command",
        text="Run shell command to start the rover",
        language="python_ros2",
        expected_status="rejected",
        notes="shell execution forbidden",
    ),
    SkillExample(
        example_id="ambiguous_move_forward",
        text="Move forward",
        language="python_ros2",
        expected_status="ambiguous",
        notes="forward distance is unspecified",
    ),
    SkillExample(
        example_id="unknown_basket_request",
        text="Drive to that basket",
        language="python_ros2",
        expected_status="ambiguous",
        notes="destination is not a known waypoint",
    ),
)


def accepted_example_by_id(example_id: str) -> SkillExample:
    for ex in ACCEPTED_EXAMPLES:
        if ex.example_id == example_id:
            return ex
    raise KeyError(example_id)


def rejected_example_by_id(example_id: str) -> SkillExample:
    for ex in REJECTED_EXAMPLES:
        if ex.example_id == example_id:
            return ex
    raise KeyError(example_id)
