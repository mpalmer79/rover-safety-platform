"""Top-level alias for rover_observability/observability.launch.py.

Provides a single namespace (``rover_bringup``) for all top-level
launches users typically run.
"""

from __future__ import annotations

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution(
                        [
                            FindPackageShare("rover_observability"),
                            "launch",
                            "observability.launch.py",
                        ]
                    )
                ),
            )
        ]
    )
