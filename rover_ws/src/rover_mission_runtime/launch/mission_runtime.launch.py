"""Launch the mission orchestrator node."""

from __future__ import annotations

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    run_id = LaunchConfiguration("run_id")
    scenario_id = LaunchConfiguration("scenario_id")
    plan_path = LaunchConfiguration("mission_plan_path")
    period = LaunchConfiguration("evaluation_period_ms")
    return LaunchDescription(
        [
            DeclareLaunchArgument("run_id", default_value="unknown"),
            DeclareLaunchArgument("scenario_id", default_value="unknown"),
            DeclareLaunchArgument(
                "mission_plan_path",
                description="Path to a JSON file containing a mission_plan",
            ),
            DeclareLaunchArgument("evaluation_period_ms", default_value="100"),
            Node(
                package="rover_mission_runtime",
                executable="mission_node",
                name="rover_mission_runtime",
                output="screen",
                parameters=[
                    {
                        "run_id": run_id,
                        "scenario_id": scenario_id,
                        "mission_plan_path": plan_path,
                        "evaluation_period_ms": period,
                        "use_sim_time": True,
                    }
                ],
            ),
        ]
    )
