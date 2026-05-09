"""Launch the safety bridge node."""

from __future__ import annotations

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    run_id = LaunchConfiguration("run_id")
    scenario_id = LaunchConfiguration("scenario_id")
    period = LaunchConfiguration("evaluation_period_ms")

    return LaunchDescription(
        [
            DeclareLaunchArgument("run_id", default_value="unknown"),
            DeclareLaunchArgument("scenario_id", default_value="unknown"),
            DeclareLaunchArgument("evaluation_period_ms", default_value="100"),
            Node(
                package="rover_safety_bridge",
                executable="safety_bridge_node",
                name="rover_safety_bridge",
                output="screen",
                parameters=[
                    {
                        "run_id": run_id,
                        "scenario_id": scenario_id,
                        "evaluation_period_ms": period,
                        "use_sim_time": True,
                    }
                ],
            ),
        ]
    )
