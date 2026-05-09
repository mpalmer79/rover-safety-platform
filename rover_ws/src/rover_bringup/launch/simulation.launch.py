"""Top-level alias for rover_sim_gazebo/simulation.launch.py + spawn.

Useful when bringing up Gazebo + the rover without engaging the
safety runtime (for example, when iterating on the URDF or world).
"""

from __future__ import annotations

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def _include(package: str, launch_file: str) -> IncludeLaunchDescription:
    return IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare(package), "launch", launch_file])
        )
    )


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            _include("rover_sim_gazebo", "simulation.launch.py"),
            TimerAction(
                period=3.0,
                actions=[_include("rover_sim_gazebo", "rover_spawn.launch.py")],
            ),
        ]
    )
