"""Launch the Nav2 velocity-clamp boundary node."""

from __future__ import annotations

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            DeclareLaunchArgument("input_topic", default_value="/cmd_vel_nav2"),
            DeclareLaunchArgument("output_topic", default_value="/cmd_vel_requested"),
            DeclareLaunchArgument("max_linear_velocity", default_value="0.5"),
            DeclareLaunchArgument("max_angular_velocity", default_value="0.8"),
            Node(
                package="rover_mission_runtime",
                executable="nav2_velocity_clamp",
                name="rover_nav2_velocity_clamp",
                output="screen",
                parameters=[
                    {
                        "input_topic": LaunchConfiguration("input_topic"),
                        "output_topic": LaunchConfiguration("output_topic"),
                        "max_linear_velocity": LaunchConfiguration(
                            "max_linear_velocity"
                        ),
                        "max_angular_velocity": LaunchConfiguration(
                            "max_angular_velocity"
                        ),
                        "use_sim_time": True,
                    }
                ],
            ),
        ]
    )
