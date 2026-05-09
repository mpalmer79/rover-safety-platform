"""Spawn the rover in the running Gazebo simulation.

Computes the rover's URDF using xacro, publishes robot_description via
robot_state_publisher, and uses the ros_gz `create` service to spawn
the rover into the current Gazebo world. Caller must already have
Gazebo running (see simulation.launch.py).
"""

from __future__ import annotations

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    rover_name = LaunchConfiguration("rover_name")
    spawn_x = LaunchConfiguration("spawn_x")
    spawn_y = LaunchConfiguration("spawn_y")
    spawn_yaw = LaunchConfiguration("spawn_yaw")

    description_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [
                    FindPackageShare("rover_description"),
                    "launch",
                    "rover_description.launch.py",
                ]
            )
        ),
        launch_arguments={"use_sim_time": "true"}.items(),
    )

    spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        name="spawn_rover",
        output="screen",
        arguments=[
            "-name", rover_name,
            "-topic", "/robot_description",
            "-x", spawn_x,
            "-y", spawn_y,
            "-z", "0.05",
            "-Y", spawn_yaw,
        ],
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("rover_name", default_value="rover"),
            DeclareLaunchArgument("spawn_x", default_value="0.0"),
            DeclareLaunchArgument("spawn_y", default_value="0.0"),
            DeclareLaunchArgument("spawn_yaw", default_value="0.0"),
            description_launch,
            spawn_entity,
        ]
    )
