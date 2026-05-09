"""Launch all four sensor adapter nodes."""

from __future__ import annotations

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _adapter(executable: str, run_id, scenario_id) -> Node:
    return Node(
        package="rover_sensor_adapters",
        executable=executable,
        name=executable,
        output="screen",
        parameters=[
            {
                "run_id": run_id,
                "scenario_id": scenario_id,
                "use_sim_time": True,
            }
        ],
    )


def generate_launch_description() -> LaunchDescription:
    run_id = LaunchConfiguration("run_id")
    scenario_id = LaunchConfiguration("scenario_id")

    return LaunchDescription(
        [
            DeclareLaunchArgument("run_id", default_value="unknown"),
            DeclareLaunchArgument("scenario_id", default_value="unknown"),
            _adapter("lidar_adapter", run_id, scenario_id),
            _adapter("imu_adapter", run_id, scenario_id),
            _adapter("odometry_adapter", run_id, scenario_id),
            _adapter("contact_adapter", run_id, scenario_id),
        ]
    )
