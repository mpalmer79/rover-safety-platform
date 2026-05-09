"""Top-level launch: simulation + spawn + adapters + safety + observability.

Composes the smaller launches in deterministic order:

1. Gazebo + ros_gz_bridge (rover_sim_gazebo/simulation.launch.py)
2. Robot description and rover spawn (rover_sim_gazebo/rover_spawn.launch.py)
3. Sensor adapters (rover_sensor_adapters/sensor_adapters.launch.py)
4. Safety bridge (rover_safety_bridge/safety_bridge.launch.py)
5. Observability (rover_observability/observability.launch.py)
"""

from __future__ import annotations

import os

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def _include(package: str, launch_file: str, **launch_args) -> IncludeLaunchDescription:
    return IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare(package), "launch", launch_file])
        ),
        launch_arguments=launch_args.items(),
    )


def generate_launch_description() -> LaunchDescription:
    run_id = LaunchConfiguration("run_id")
    scenario_id = LaunchConfiguration("scenario_id")
    runs_root = LaunchConfiguration("runs_root")
    record_bag = LaunchConfiguration("record_bag")
    headless = LaunchConfiguration("headless")

    sim = _include(
        "rover_sim_gazebo", "simulation.launch.py", headless=headless,
    )

    spawn = TimerAction(
        period=3.0,
        actions=[
            _include("rover_sim_gazebo", "rover_spawn.launch.py"),
        ],
    )

    adapters = TimerAction(
        period=4.5,
        actions=[
            _include(
                "rover_sensor_adapters",
                "sensor_adapters.launch.py",
                run_id=run_id,
                scenario_id=scenario_id,
            ),
        ],
    )

    safety = TimerAction(
        period=5.0,
        actions=[
            _include(
                "rover_safety_bridge",
                "safety_bridge.launch.py",
                run_id=run_id,
                scenario_id=scenario_id,
            ),
        ],
    )

    observability = TimerAction(
        period=2.0,
        actions=[
            _include(
                "rover_observability",
                "observability.launch.py",
                run_id=run_id,
                scenario_id=scenario_id,
                runs_root=runs_root,
                record_bag=record_bag,
            ),
        ],
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "run_id",
                default_value="",
                description="Run identifier; empty -> rover_run_manager allocates one.",
            ),
            DeclareLaunchArgument("scenario_id", default_value="full_system_default"),
            DeclareLaunchArgument(
                "runs_root", default_value=os.path.join(os.getcwd(), "runs")
            ),
            DeclareLaunchArgument("record_bag", default_value="true"),
            DeclareLaunchArgument("headless", default_value="false"),
            observability,
            sim,
            spawn,
            adapters,
            safety,
        ]
    )
