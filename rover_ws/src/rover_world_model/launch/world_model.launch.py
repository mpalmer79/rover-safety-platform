"""Launch the world model node."""

from __future__ import annotations

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            DeclareLaunchArgument("run_id", default_value="unknown"),
            DeclareLaunchArgument("scenario_id", default_value="unknown"),
            DeclareLaunchArgument(
                "zones_path",
                default_value="",
                description="Path to a JSON file declaring keepout/restricted/boundary zones.",
            ),
            DeclareLaunchArgument("evaluation_period_ms", default_value="200"),
            Node(
                package="rover_world_model",
                executable="world_model_node",
                name="rover_world_model",
                output="screen",
                parameters=[
                    {
                        "run_id": LaunchConfiguration("run_id"),
                        "scenario_id": LaunchConfiguration("scenario_id"),
                        "zones_path": LaunchConfiguration("zones_path"),
                        "evaluation_period_ms": LaunchConfiguration("evaluation_period_ms"),
                        "use_sim_time": True,
                    }
                ],
            ),
        ]
    )
