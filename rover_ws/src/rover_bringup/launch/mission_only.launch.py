"""Mission-only bringup.

Layers the Phase 2 mission stack (world model, mission orchestrator,
mission diagnostics) on top of an already-running safety / simulation
graph. Useful for iterating on mission scenarios without restarting
Gazebo.

The full top-level launch (``full_system.launch.py``) includes this
stack via ``enable_mission``.
"""

from __future__ import annotations

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def _include(package: str, launch_file: str, **kwargs) -> IncludeLaunchDescription:
    return IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare(package), "launch", launch_file])
        ),
        launch_arguments=kwargs.items(),
    )


def generate_launch_description() -> LaunchDescription:
    run_id = LaunchConfiguration("run_id")
    scenario_id = LaunchConfiguration("scenario_id")
    plan_path = LaunchConfiguration("mission_plan_path")
    return LaunchDescription(
        [
            DeclareLaunchArgument("run_id", default_value="unknown"),
            DeclareLaunchArgument("scenario_id", default_value="unknown"),
            DeclareLaunchArgument(
                "mission_plan_path",
                description=(
                    "Path to a JSON file containing a mission_plan. The "
                    "world model also reads zone declarations from it."
                ),
            ),
            _include(
                "rover_world_model",
                "world_model.launch.py",
                run_id=run_id,
                scenario_id=scenario_id,
                zones_path=plan_path,
            ),
            _include(
                "rover_mission_runtime",
                "mission_runtime.launch.py",
                run_id=run_id,
                scenario_id=scenario_id,
                mission_plan_path=plan_path,
            ),
            _include("rover_mission_diagnostics", "mission_diagnostics.launch.py"),
        ]
    )
