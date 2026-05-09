"""Publish robot_description from rover.urdf.xacro and start
robot_state_publisher.

This launch is composed by the higher-level launches in rover_bringup.
It does not depend on Gazebo; it only computes the URDF and starts the
state publisher.
"""

from __future__ import annotations

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import (
    Command,
    FindExecutable,
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    use_sim_time = LaunchConfiguration("use_sim_time")
    xacro_file = PathJoinSubstitution(
        [FindPackageShare("rover_description"), "urdf", "rover.urdf.xacro"]
    )
    robot_description = Command([FindExecutable(name="xacro"), " ", xacro_file])

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "use_sim_time",
                default_value="true",
                description="Drive nodes from /clock published by Gazebo.",
            ),
            Node(
                package="robot_state_publisher",
                executable="robot_state_publisher",
                name="robot_state_publisher",
                output="screen",
                parameters=[
                    {
                        "robot_description": robot_description,
                        "use_sim_time": use_sim_time,
                    }
                ],
            ),
        ]
    )
