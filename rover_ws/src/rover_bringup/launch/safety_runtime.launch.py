"""Launch the safety runtime (adapters + safety bridge + observability + diagnostics).

Useful when iterating on the safety pathway against a stubbed or
externally-launched simulation. Diagnostics are enabled by default
because the safety runtime is the most freshness-sensitive subsystem;
when iterating against a stub, the diagnostics tell you immediately
which inputs the stub has not provided.
"""

from __future__ import annotations

import os

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    LogInfo,
    TimerAction,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def _include(
    package: str, launch_file: str, *, condition=None, **kwargs
) -> IncludeLaunchDescription:
    return IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare(package), "launch", launch_file])
        ),
        launch_arguments=kwargs.items(),
        condition=condition,
    )


def generate_launch_description() -> LaunchDescription:
    run_id = LaunchConfiguration("run_id")
    scenario_id = LaunchConfiguration("scenario_id")
    runs_root = LaunchConfiguration("runs_root")
    record_bag = LaunchConfiguration("record_bag")
    enable_diagnostics = LaunchConfiguration("enable_diagnostics")
    return LaunchDescription(
        [
            DeclareLaunchArgument("run_id", default_value=""),
            DeclareLaunchArgument("scenario_id", default_value="safety_runtime_default"),
            DeclareLaunchArgument(
                "runs_root", default_value=os.path.join(os.getcwd(), "runs")
            ),
            DeclareLaunchArgument(
                "record_bag",
                default_value="false",
                choices=["true", "false"],
            ),
            DeclareLaunchArgument(
                "enable_diagnostics",
                default_value="true",
                choices=["true", "false"],
            ),
            _include(
                "rover_observability",
                "observability.launch.py",
                run_id=run_id,
                scenario_id=scenario_id,
                runs_root=runs_root,
                record_bag=record_bag,
            ),
            _include(
                "rover_sensor_adapters",
                "sensor_adapters.launch.py",
                run_id=run_id,
                scenario_id=scenario_id,
            ),
            _include(
                "rover_safety_bridge",
                "safety_bridge.launch.py",
                run_id=run_id,
                scenario_id=scenario_id,
            ),
            TimerAction(
                period=2.0,
                actions=[
                    LogInfo(msg="[safety_runtime] starting runtime diagnostics"),
                    _include(
                        "rover_runtime_diagnostics",
                        "runtime_diagnostics.launch.py",
                        run_id=run_id,
                        scenario_id=scenario_id,
                        condition=IfCondition(enable_diagnostics),
                    ),
                ],
            ),
        ]
    )
