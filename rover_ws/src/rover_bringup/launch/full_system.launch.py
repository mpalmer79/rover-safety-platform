"""Top-level launch: simulation + spawn + adapters + safety + observability + diagnostics.

Composes the smaller launches in a deterministic, dependency-aware order:

1. ``observability`` (run_manager + event_recorder + bag) — earliest
   so the recorder captures every later event.
2. ``simulation`` (Gazebo + ros_gz_bridge).
3. ``rover_spawn`` (URDF publisher + spawn entity).
4. ``sensor_adapters`` (per-sensor freshness summaries).
5. ``safety_runtime`` (safety bridge — the only producer of
   ``/cmd_vel_authorized``).
6. ``runtime_diagnostics`` (Phase 1C live runtime monitors).

The ordering is enforced via :class:`TimerAction` delays. Each delay
is conservative (a few seconds) so the parent process can be a
``python3 -m`` invocation in CI without races.

Launch arguments are validated by ``OnLaunchedHandler``-style action
when reasonable (``record_bag`` and ``enable_diagnostics`` are bools;
``runs_root`` must be writable).
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
    package: str, launch_file: str, *, condition=None, **launch_args
) -> IncludeLaunchDescription:
    return IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare(package), "launch", launch_file])
        ),
        launch_arguments=launch_args.items(),
        condition=condition,
    )


def generate_launch_description() -> LaunchDescription:
    run_id = LaunchConfiguration("run_id")
    scenario_id = LaunchConfiguration("scenario_id")
    runs_root = LaunchConfiguration("runs_root")
    record_bag = LaunchConfiguration("record_bag")
    headless = LaunchConfiguration("headless")
    enable_diagnostics = LaunchConfiguration("enable_diagnostics")

    observability = TimerAction(
        period=0.5,
        actions=[
            LogInfo(msg="[full_system] starting observability"),
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

    sim = TimerAction(
        period=1.5,
        actions=[
            LogInfo(msg="[full_system] starting Gazebo and ros_gz_bridge"),
            _include("rover_sim_gazebo", "simulation.launch.py", headless=headless),
        ],
    )

    spawn = TimerAction(
        period=4.0,
        actions=[
            LogInfo(msg="[full_system] spawning rover and starting robot_state_publisher"),
            _include("rover_sim_gazebo", "rover_spawn.launch.py"),
        ],
    )

    adapters = TimerAction(
        period=5.5,
        actions=[
            LogInfo(msg="[full_system] starting sensor adapters"),
            _include(
                "rover_sensor_adapters",
                "sensor_adapters.launch.py",
                run_id=run_id,
                scenario_id=scenario_id,
            ),
        ],
    )

    safety = TimerAction(
        period=6.0,
        actions=[
            LogInfo(msg="[full_system] starting safety bridge"),
            _include(
                "rover_safety_bridge",
                "safety_bridge.launch.py",
                run_id=run_id,
                scenario_id=scenario_id,
            ),
        ],
    )

    diagnostics = TimerAction(
        period=8.0,
        actions=[
            LogInfo(msg="[full_system] starting runtime diagnostics"),
            _include(
                "rover_runtime_diagnostics",
                "runtime_diagnostics.launch.py",
                run_id=run_id,
                scenario_id=scenario_id,
                condition=IfCondition(enable_diagnostics),
            ),
        ],
    )

    enable_mission = LaunchConfiguration("enable_mission")
    mission_plan_path = LaunchConfiguration("mission_plan_path")
    mission = TimerAction(
        period=9.0,
        actions=[
            LogInfo(msg="[full_system] starting mission runtime + world model"),
            _include(
                "rover_world_model",
                "world_model.launch.py",
                run_id=run_id,
                scenario_id=scenario_id,
                zones_path=mission_plan_path,
                condition=IfCondition(enable_mission),
            ),
            _include(
                "rover_mission_runtime",
                "mission_runtime.launch.py",
                run_id=run_id,
                scenario_id=scenario_id,
                mission_plan_path=mission_plan_path,
                condition=IfCondition(enable_mission),
            ),
            _include(
                "rover_mission_diagnostics",
                "mission_diagnostics.launch.py",
                condition=IfCondition(enable_mission),
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
            DeclareLaunchArgument(
                "scenario_id",
                default_value="full_system_default",
                description="Scenario identifier; flows into events and the run directory metadata.",
            ),
            DeclareLaunchArgument(
                "runs_root",
                default_value=os.path.join(os.getcwd(), "runs"),
                description="Root directory under which run folders are created.",
            ),
            DeclareLaunchArgument(
                "record_bag",
                default_value="true",
                choices=["true", "false"],
                description="Whether to start an MCAP rosbag2 recording.",
            ),
            DeclareLaunchArgument(
                "headless",
                default_value="false",
                choices=["true", "false"],
                description="Run Gazebo without rendering.",
            ),
            DeclareLaunchArgument(
                "enable_diagnostics",
                default_value="true",
                choices=["true", "false"],
                description="Whether to launch the rover_runtime_diagnostics nodes.",
            ),
            DeclareLaunchArgument(
                "enable_mission",
                default_value="false",
                choices=["true", "false"],
                description=(
                    "Whether to launch the Phase 2 mission stack "
                    "(world model, mission orchestrator, mission diagnostics)."
                ),
            ),
            DeclareLaunchArgument(
                "mission_plan_path",
                default_value="",
                description=(
                    "Path to a JSON file containing a mission_plan. Required when "
                    "enable_mission is true."
                ),
            ),
            observability,
            sim,
            spawn,
            adapters,
            safety,
            diagnostics,
            mission,
        ]
    )
