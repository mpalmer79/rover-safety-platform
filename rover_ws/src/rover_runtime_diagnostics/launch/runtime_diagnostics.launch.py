"""Launch the runtime diagnostics nodes.

Composable: callers (rover_bringup) include this after the safety
runtime is up so the diagnostics node have something to monitor.
"""

from __future__ import annotations

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import (
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    run_id = LaunchConfiguration("run_id")
    scenario_id = LaunchConfiguration("scenario_id")
    urdf = PathJoinSubstitution(
        [FindPackageShare("rover_description"), "urdf", "rover.urdf.xacro"]
    )

    common_params = [{"use_sim_time": True}]

    return LaunchDescription(
        [
            DeclareLaunchArgument("run_id", default_value="unknown"),
            DeclareLaunchArgument("scenario_id", default_value="unknown"),
            Node(
                package="rover_runtime_diagnostics",
                executable="topic_freshness_node",
                name="rover_topic_freshness_diagnostics",
                output="screen",
                parameters=common_params,
            ),
            Node(
                package="rover_runtime_diagnostics",
                executable="bridge_health_node",
                name="rover_bridge_health_diagnostics",
                output="screen",
                parameters=common_params,
            ),
            Node(
                package="rover_runtime_diagnostics",
                executable="tf_validator_node",
                name="rover_tf_validator",
                output="screen",
                parameters=[
                    {"use_sim_time": True, "urdf_path": urdf},
                ],
            ),
            Node(
                package="rover_runtime_diagnostics",
                executable="runtime_summary_node",
                name="rover_runtime_summary",
                output="screen",
                parameters=[
                    {
                        "use_sim_time": True,
                        "run_id": run_id,
                        "scenario_id": scenario_id,
                    }
                ],
            ),
        ]
    )
