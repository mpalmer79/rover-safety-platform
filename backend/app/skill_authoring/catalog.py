"""Bounded catalog of supported robotics skills.

Adding a new entry here is a deliberate, reviewable change. The
intent parser only emits skill candidates that match one of these
entries. Templates live in :mod:`templates`; this module records the
metadata (required parameters, safety constraints, allowed topics).
"""

from __future__ import annotations

from .models import (
    SkillLanguage,
    SkillRiskBand,
    SkillTemplate,
    SkillType,
)


_REQUESTED_MOTION_TOPIC: str = "/cmd_vel_requested"
_FORBIDDEN_ACTUATOR_TOPIC: str = "/cmd_vel"


SKILL_CATALOG: tuple[SkillTemplate, ...] = (
    SkillTemplate(
        skill_type=SkillType.MOVE_FORWARD_DISTANCE.value,
        language=SkillLanguage.PYTHON_ROS2.value,
        title="Move forward a bounded distance",
        subtitle="Publishes /cmd_vel_requested at a conservative speed, then a final zero command.",
        required_parameters=("distance_meters",),
        default_parameters={
            "linear_speed_mps": 0.25,
            "publish_rate_hz": 10.0,
            "timeout_safety_margin": 1.5,
        },
        safety_constraints=(
            "distance_meters must be > 0 and <= 25.0",
            "linear_speed_mps must be > 0 and <= 0.5",
            "publish loop must terminate via duration timeout",
            "final zero Twist must be published",
        ),
        generated_topics=(_REQUESTED_MOTION_TOPIC,),
        forbidden_topics=(_FORBIDDEN_ACTUATOR_TOPIC,),
        timeout_required=True,
        stop_command_required=True,
        risk_band=SkillRiskBand.GUARDED.value,
        review_notes=(
            "Safety supervisor authorises actual motion via /cmd_vel_authorized.",
            "Distance is a *request*; the supervisor may clamp or reject.",
        ),
    ),
    SkillTemplate(
        skill_type=SkillType.ROTATE_DEGREES.value,
        language=SkillLanguage.PYTHON_ROS2.value,
        title="Rotate by a bounded angle",
        subtitle="Publishes /cmd_vel_requested with bounded angular velocity, then a zero command.",
        required_parameters=("angle_degrees", "direction"),
        default_parameters={
            "angular_speed_rad_s": 0.4,
            "publish_rate_hz": 10.0,
            "timeout_safety_margin": 1.5,
        },
        safety_constraints=(
            "|angle_degrees| must be > 0 and <= 720",
            "angular_speed_rad_s must be > 0 and <= 1.0",
            "publish loop must terminate via duration timeout",
            "final zero Twist must be published",
        ),
        generated_topics=(_REQUESTED_MOTION_TOPIC,),
        forbidden_topics=(_FORBIDDEN_ACTUATOR_TOPIC,),
        timeout_required=True,
        stop_command_required=True,
        risk_band=SkillRiskBand.GUARDED.value,
        review_notes=(
            "Safety supervisor authorises actual motion via /cmd_vel_authorized.",
            "Angle is a *request*; the supervisor may clamp or reject.",
        ),
    ),
    SkillTemplate(
        skill_type=SkillType.STOP_IMMEDIATELY.value,
        language=SkillLanguage.PYTHON_ROS2.value,
        title="Stop immediately",
        subtitle="Publishes a single zero Twist to /cmd_vel_requested.",
        required_parameters=(),
        default_parameters={"publish_count": 5, "publish_rate_hz": 10.0},
        safety_constraints=(
            "publishes only zero linear and angular velocity",
            "no loop unless bounded by publish_count",
        ),
        generated_topics=(_REQUESTED_MOTION_TOPIC,),
        forbidden_topics=(_FORBIDDEN_ACTUATOR_TOPIC,),
        timeout_required=False,
        stop_command_required=True,
        risk_band=SkillRiskBand.LOW.value,
        review_notes=(
            "An immediate stop request still flows through the safety supervisor.",
        ),
    ),
    SkillTemplate(
        skill_type=SkillType.PUBLISH_REQUESTED_MOTION.value,
        language=SkillLanguage.PYTHON_ROS2.value,
        title="Publish a single requested-motion command",
        subtitle="Publishes one Twist to /cmd_vel_requested with operator-supplied values.",
        required_parameters=("linear_x_mps", "angular_z_rad_s"),
        default_parameters={},
        safety_constraints=(
            "|linear_x_mps| <= 0.5",
            "|angular_z_rad_s| <= 1.0",
        ),
        generated_topics=(_REQUESTED_MOTION_TOPIC,),
        forbidden_topics=(_FORBIDDEN_ACTUATOR_TOPIC,),
        timeout_required=False,
        stop_command_required=False,
        risk_band=SkillRiskBand.GUARDED.value,
        review_notes=(
            "Single publication; caller decides cadence and timeout.",
            "Safety supervisor remains authoritative.",
        ),
    ),
    SkillTemplate(
        skill_type=SkillType.KEYBOARD_FORWARD_BINDING.value,
        language=SkillLanguage.PYTHON_ROS2.value,
        title="Bind a keyboard key to a requested-motion command",
        subtitle="Publishes /cmd_vel_requested while a key is held; zeroes on release.",
        required_parameters=("key",),
        default_parameters={
            "linear_speed_mps": 0.2,
            "publish_rate_hz": 10.0,
            "watchdog_seconds": 0.5,
        },
        safety_constraints=(
            "linear_speed_mps must be > 0 and <= 0.5",
            "watchdog must zero motion if key is released",
        ),
        generated_topics=(_REQUESTED_MOTION_TOPIC,),
        forbidden_topics=(_FORBIDDEN_ACTUATOR_TOPIC,),
        timeout_required=True,
        stop_command_required=True,
        risk_band=SkillRiskBand.GUARDED.value,
        review_notes=(
            "Generated snippet uses a polled loop; integrate with your input library.",
            "Safety supervisor remains authoritative for actual motion.",
        ),
    ),
    SkillTemplate(
        skill_type=SkillType.CONTROLLER_BUTTON_BINDING.value,
        language=SkillLanguage.PYTHON_ROS2.value,
        title="Bind a controller button to a requested-motion command",
        subtitle="Publishes /cmd_vel_requested while a button is held; zeroes on release.",
        required_parameters=("button",),
        default_parameters={
            "linear_speed_mps": 0.2,
            "publish_rate_hz": 10.0,
            "watchdog_seconds": 0.5,
        },
        safety_constraints=(
            "linear_speed_mps must be > 0 and <= 0.5",
            "watchdog must zero motion if button is released",
        ),
        generated_topics=(_REQUESTED_MOTION_TOPIC,),
        forbidden_topics=(_FORBIDDEN_ACTUATOR_TOPIC,),
        timeout_required=True,
        stop_command_required=True,
        risk_band=SkillRiskBand.GUARDED.value,
        review_notes=(
            "Generated snippet expects a Joy / sensor_msgs subscriber.",
            "Safety supervisor remains authoritative for actual motion.",
        ),
    ),
    SkillTemplate(
        skill_type=SkillType.WAYPOINT_REQUEST.value,
        language=SkillLanguage.PYTHON_ROS2.value,
        title="Request a single waypoint",
        subtitle="Publishes a mission request, not a /cmd_vel_authorized command.",
        required_parameters=("waypoint_id",),
        default_parameters={"mission_topic": "/mission/waypoint_request"},
        safety_constraints=(
            "waypoint_id must be a known label, not a free coordinate",
            "publishes to mission_topic, not to actuator topics",
        ),
        generated_topics=("/mission/waypoint_request",),
        forbidden_topics=(_FORBIDDEN_ACTUATOR_TOPIC, _REQUESTED_MOTION_TOPIC),
        timeout_required=False,
        stop_command_required=False,
        risk_band=SkillRiskBand.LOW.value,
        review_notes=(
            "Mission runtime decides whether to act; safety supervisor authorises motion.",
        ),
    ),
    SkillTemplate(
        skill_type=SkillType.PATROL_ROUTE_TEMPLATE.value,
        language=SkillLanguage.PYTHON_ROS2.value,
        title="Request a bounded patrol route",
        subtitle="Publishes a patrol mission request listing named waypoints.",
        required_parameters=("waypoints",),
        default_parameters={
            "mission_topic": "/mission/patrol_request",
            "max_waypoints": 8,
        },
        safety_constraints=(
            "waypoints must be a list of named labels (length <= 8)",
            "publishes to mission_topic, not to actuator topics",
        ),
        generated_topics=("/mission/patrol_request",),
        forbidden_topics=(_FORBIDDEN_ACTUATOR_TOPIC, _REQUESTED_MOTION_TOPIC),
        timeout_required=False,
        stop_command_required=False,
        risk_band=SkillRiskBand.LOW.value,
        review_notes=(
            "Mission runtime sequences the waypoints; the snippet does not move the rover.",
        ),
    ),
    SkillTemplate(
        skill_type=SkillType.SAFE_STOP_WRAPPER.value,
        language=SkillLanguage.PYTHON_ROS2.value,
        title="Safe-stop wrapper for a /cmd_vel_requested publisher",
        subtitle="Decorator that zeroes motion on exception, KeyboardInterrupt, or context-exit.",
        required_parameters=(),
        default_parameters={"publish_count": 3, "publish_rate_hz": 10.0},
        safety_constraints=(
            "must always publish a zero Twist on exit",
        ),
        generated_topics=(_REQUESTED_MOTION_TOPIC,),
        forbidden_topics=(_FORBIDDEN_ACTUATOR_TOPIC,),
        timeout_required=False,
        stop_command_required=True,
        risk_band=SkillRiskBand.LOW.value,
        review_notes=(
            "Use this as a wrapper around developer-authored motion routines.",
            "Safety supervisor remains authoritative for actual motion.",
        ),
    ),
)


def find_template(
    skill_type: str, language: str = SkillLanguage.PYTHON_ROS2.value
) -> SkillTemplate | None:
    for template in SKILL_CATALOG:
        if template.skill_type == skill_type and template.language == language:
            return template
    return None


def list_supported_skills() -> tuple[str, ...]:
    return tuple(sorted({t.skill_type for t in SKILL_CATALOG}))
