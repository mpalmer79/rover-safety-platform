"""Launch the mission diagnostics node."""

from __future__ import annotations

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            DeclareLaunchArgument("evaluation_period_ms", default_value="500"),
            Node(
                package="rover_mission_diagnostics",
                executable="mission_diagnostics_node",
                name="rover_mission_diagnostics",
                output="screen",
                parameters=[
                    {
                        "evaluation_period_ms": LaunchConfiguration("evaluation_period_ms"),
                        "use_sim_time": True,
                    }
                ],
            ),
        ]
    )
