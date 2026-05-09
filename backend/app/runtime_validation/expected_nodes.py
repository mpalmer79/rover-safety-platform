"""Declared expectations for the live ROS node graph.

Each :class:`NodeExpectation` represents one ROS 2 node that must be
running after ``ros2 launch rover_bringup full_system.launch.py``
reaches steady state. The launch smoke test asserts these nodes are
present; static-only mode asserts the launch file mentions them.

Names match the ``name=`` argument passed to :class:`launch_ros.actions.Node`
in each launch file. If a launch is restructured the corresponding
expectation must move with it.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NodeExpectation:
    node_name: str
    package: str
    role: str
    """Free-text role for the report."""

    required: bool = True


EXPECTED_SIMULATION_NODES: tuple[NodeExpectation, ...] = (
    NodeExpectation(
        node_name="ros_gz_bridge",
        package="ros_gz_bridge",
        role="Bridges Gazebo simulator to ROS topics.",
    ),
    NodeExpectation(
        node_name="robot_state_publisher",
        package="robot_state_publisher",
        role="Publishes /tf_static from rover URDF.",
    ),
)


EXPECTED_SAFETY_NODES: tuple[NodeExpectation, ...] = (
    NodeExpectation(
        node_name="rover_safety_bridge",
        package="rover_safety_bridge",
        role="Hosts the deterministic safety supervisor; sole producer of /cmd_vel_authorized.",
    ),
    NodeExpectation(
        node_name="lidar_adapter",
        package="rover_sensor_adapters",
        role="Normalises /scan freshness; publishes SensorHealth.",
    ),
    NodeExpectation(
        node_name="imu_adapter",
        package="rover_sensor_adapters",
        role="Normalises /imu freshness; publishes SensorHealth.",
    ),
    NodeExpectation(
        node_name="odometry_adapter",
        package="rover_sensor_adapters",
        role="Normalises /odom freshness; publishes SensorHealth.",
    ),
    NodeExpectation(
        node_name="contact_adapter",
        package="rover_sensor_adapters",
        role="Normalises /contact freshness; publishes SensorHealth.",
    ),
)


EXPECTED_OBSERVABILITY_NODES: tuple[NodeExpectation, ...] = (
    NodeExpectation(
        node_name="rover_run_manager",
        package="rover_observability",
        role="Allocates run_id and writes runs/<run_id>/ metadata.",
    ),
    NodeExpectation(
        node_name="rover_event_recorder",
        package="rover_observability",
        role="Persists /safety/events to events.jsonl.",
    ),
    NodeExpectation(
        node_name="rover_topic_freshness_diagnostics",
        package="rover_runtime_diagnostics",
        role="Topic freshness monitor; publishes /diagnostics/topic_freshness.",
    ),
    NodeExpectation(
        node_name="rover_bridge_health_diagnostics",
        package="rover_runtime_diagnostics",
        role="ros_gz_bridge health monitor.",
    ),
    NodeExpectation(
        node_name="rover_runtime_summary",
        package="rover_runtime_diagnostics",
        role="Aggregates diagnostic summaries; publishes /diagnostics/runtime_summary and /system/health.",
    ),
)


EXPECTED_NODES: tuple[NodeExpectation, ...] = (
    EXPECTED_SIMULATION_NODES
    + EXPECTED_SAFETY_NODES
    + EXPECTED_OBSERVABILITY_NODES
)
