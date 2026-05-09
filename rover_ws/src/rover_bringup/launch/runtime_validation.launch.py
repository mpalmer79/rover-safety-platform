"""Launch the runtime diagnostics nodes against an already-running stack.

Useful for attaching diagnostics to a graph that was started without
``--enable_diagnostics``. Also useful when iterating on the
diagnostics package itself: rebuild the package, rerun this launch,
and the topic_freshness / bridge_health / runtime_summary nodes
restart without disturbing the simulation or safety runtime.
"""

from __future__ import annotations

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    run_id = LaunchConfiguration("run_id")
    scenario_id = LaunchConfiguration("scenario_id")
    return LaunchDescription(
        [
            DeclareLaunchArgument("run_id", default_value="unknown"),
            DeclareLaunchArgument("scenario_id", default_value="unknown"),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution(
                        [
                            FindPackageShare("rover_runtime_diagnostics"),
                            "launch",
                            "runtime_diagnostics.launch.py",
                        ]
                    )
                ),
                launch_arguments={
                    "run_id": run_id,
                    "scenario_id": scenario_id,
                }.items(),
            ),
        ]
    )
