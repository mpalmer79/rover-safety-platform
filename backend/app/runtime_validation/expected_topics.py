"""Declared expectations for the live ROS topic graph.

The list mirrors the topics documented in:

* ``docs/REPLAY_SYSTEM.md`` section 7,
* ``rover_ws/src/rover_sim_gazebo/config/ros_gz_bridge.yaml``,
* the publisher / subscriber declarations in the safety bridge,
  mission node, world model, and diagnostics packages.

Each :class:`TopicExpectation` captures:

* the canonical topic name,
* the ROS message type (used by the topic probe to assert
  ``ros2 topic info`` matches),
* the direction (where the topic comes from in the live graph),
* an expected freshness window in milliseconds (``-1`` if liveness is
  not asserted, e.g. for event topics),
* whether the topic is required (``required=False`` topics are
  reported but their absence does not fail the check).

The module does not perform any I/O. The probe consumes this list at
runtime; static-only mode also consumes it to assert presence of
topic declarations across the workspace artefacts.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TopicDirection(str, Enum):
    """Where a topic enters the ROS graph from."""

    GAZEBO_BRIDGE = "gazebo_bridge"
    SAFETY_BRIDGE = "safety_bridge"
    MISSION_RUNTIME = "mission_runtime"
    WORLD_MODEL = "world_model"
    DIAGNOSTICS = "diagnostics"
    OBSERVABILITY = "observability"
    OPERATOR = "operator"
    ANY = "any"


@dataclass(frozen=True)
class TopicExpectation:
    name: str
    msg_type: str
    direction: TopicDirection
    expected_period_ms: int
    """Expected publish period; only used to derive a probe timeout."""

    freshness_window_ms: int
    """Maximum age in ms beyond which the topic is reported stale.

    ``-1`` disables the freshness check (used for event topics that
    may legitimately stay quiet for long periods).
    """

    required: bool = True


EXPECTED_TOPICS: tuple[TopicExpectation, ...] = (
    TopicExpectation(
        name="/clock",
        msg_type="rosgraph_msgs/msg/Clock",
        direction=TopicDirection.GAZEBO_BRIDGE,
        expected_period_ms=10,
        freshness_window_ms=200,
    ),
    TopicExpectation(
        name="/scan",
        msg_type="sensor_msgs/msg/LaserScan",
        direction=TopicDirection.GAZEBO_BRIDGE,
        expected_period_ms=100,
        freshness_window_ms=500,
    ),
    TopicExpectation(
        name="/imu",
        msg_type="sensor_msgs/msg/Imu",
        direction=TopicDirection.GAZEBO_BRIDGE,
        expected_period_ms=20,
        freshness_window_ms=300,
    ),
    TopicExpectation(
        name="/odom",
        msg_type="nav_msgs/msg/Odometry",
        direction=TopicDirection.GAZEBO_BRIDGE,
        expected_period_ms=20,
        freshness_window_ms=300,
    ),
    TopicExpectation(
        name="/tf",
        msg_type="tf2_msgs/msg/TFMessage",
        direction=TopicDirection.GAZEBO_BRIDGE,
        expected_period_ms=20,
        freshness_window_ms=500,
    ),
    TopicExpectation(
        name="/tf_static",
        msg_type="tf2_msgs/msg/TFMessage",
        direction=TopicDirection.GAZEBO_BRIDGE,
        expected_period_ms=10000,
        freshness_window_ms=-1,
    ),
    TopicExpectation(
        name="/cmd_vel_requested",
        msg_type="geometry_msgs/msg/Twist",
        direction=TopicDirection.MISSION_RUNTIME,
        expected_period_ms=100,
        freshness_window_ms=-1,
        required=False,
    ),
    TopicExpectation(
        name="/cmd_vel_authorized",
        msg_type="geometry_msgs/msg/Twist",
        direction=TopicDirection.SAFETY_BRIDGE,
        expected_period_ms=50,
        freshness_window_ms=300,
    ),
    TopicExpectation(
        name="/safety/state",
        msg_type="rover_msgs/msg/SafetyState",
        direction=TopicDirection.SAFETY_BRIDGE,
        expected_period_ms=100,
        freshness_window_ms=500,
    ),
    TopicExpectation(
        name="/safety/events",
        msg_type="std_msgs/msg/String",
        direction=TopicDirection.SAFETY_BRIDGE,
        expected_period_ms=1000,
        freshness_window_ms=-1,
    ),
    TopicExpectation(
        name="/system/health",
        msg_type="rover_msgs/msg/SystemHealth",
        direction=TopicDirection.DIAGNOSTICS,
        expected_period_ms=1000,
        freshness_window_ms=2500,
    ),
    TopicExpectation(
        name="/diagnostics/runtime_summary",
        msg_type="std_msgs/msg/String",
        direction=TopicDirection.DIAGNOSTICS,
        expected_period_ms=1000,
        freshness_window_ms=2500,
    ),
    TopicExpectation(
        name="/mission/state",
        msg_type="rover_msgs/msg/MissionState",
        direction=TopicDirection.MISSION_RUNTIME,
        expected_period_ms=100,
        freshness_window_ms=500,
        required=False,
    ),
    TopicExpectation(
        name="/mission/events",
        msg_type="std_msgs/msg/String",
        direction=TopicDirection.MISSION_RUNTIME,
        expected_period_ms=1000,
        freshness_window_ms=-1,
        required=False,
    ),
    TopicExpectation(
        name="/mission/progress",
        msg_type="rover_msgs/msg/WaypointStatus",
        direction=TopicDirection.MISSION_RUNTIME,
        expected_period_ms=100,
        freshness_window_ms=500,
        required=False,
    ),
    TopicExpectation(
        name="/world_model/state",
        msg_type="rover_msgs/msg/WorldModelState",
        direction=TopicDirection.WORLD_MODEL,
        expected_period_ms=200,
        freshness_window_ms=1000,
        required=False,
    ),
    TopicExpectation(
        name="/replay/markers",
        msg_type="rover_msgs/msg/ReplayMarker",
        direction=TopicDirection.OBSERVABILITY,
        expected_period_ms=5000,
        freshness_window_ms=-1,
    ),
)


def get_required_topics() -> tuple[TopicExpectation, ...]:
    return tuple(t for t in EXPECTED_TOPICS if t.required)


def find_topic(name: str) -> TopicExpectation | None:
    for t in EXPECTED_TOPICS:
        if t.name == name:
            return t
    return None
