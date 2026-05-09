"""Run manager + event recorder + rosbag2 recording.

Composable. Defaults:
* ``runs_root``: ``./runs`` relative to the launch cwd.
* ``record_bag``: ``true``. Set to ``false`` to disable bag recording.
* ``run_id``: empty string -> the run manager allocates a UUID.
* ``scenario_id``: ``unknown``.

The bag is written to ``runs/<run_id>/bags/`` when recording is on.
"""

from __future__ import annotations

import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node


_RECORD_TOPICS: tuple[str, ...] = (
    "/clock",
    "/scan",
    "/odom",
    "/imu",
    "/contact",
    "/joint_states",
    "/tf",
    "/tf_static",
    "/cmd_vel_requested",
    "/cmd_vel_authorized",
    "/safety/state",
    "/safety/events",
    "/safety/motion_authorization",
    "/system/health",
    "/replay/markers",
    "/sensors/lidar/health",
    "/sensors/imu/health",
    "/sensors/wheel_encoder/health",
    "/sensors/contact/health",
)


def generate_launch_description() -> LaunchDescription:
    run_id = LaunchConfiguration("run_id")
    scenario_id = LaunchConfiguration("scenario_id")
    runs_root = LaunchConfiguration("runs_root")
    record_bag = LaunchConfiguration("record_bag")

    run_manager = Node(
        package="rover_observability",
        executable="run_manager",
        name="rover_run_manager",
        output="screen",
        parameters=[
            {
                "run_id": run_id,
                "scenario_id": scenario_id,
                "runs_root": runs_root,
                "use_sim_time": True,
            }
        ],
    )

    event_recorder = Node(
        package="rover_observability",
        executable="event_recorder",
        name="rover_event_recorder",
        output="screen",
        parameters=[
            {
                "run_id": run_id,
                "runs_root": runs_root,
                "events_topic": "/safety/events",
                "use_sim_time": True,
            }
        ],
    )

    # rosbag2 record. We invoke ros2 bag through ExecuteProcess to keep
    # the launch dependency-light; this matches the recommended Jazzy
    # idiom for recording from launch files.
    bag_proc = ExecuteProcess(
        cmd=[
            "ros2", "bag", "record",
            "-s", "mcap",
            "-o", [runs_root, "/", run_id, "/bags"],
            *list(_RECORD_TOPICS),
        ],
        output="screen",
        condition=IfCondition(record_bag),
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("run_id", default_value=""),
            DeclareLaunchArgument("scenario_id", default_value="unknown"),
            DeclareLaunchArgument(
                "runs_root", default_value=os.path.join(os.getcwd(), "runs")
            ),
            DeclareLaunchArgument("record_bag", default_value="true"),
            run_manager,
            event_recorder,
            bag_proc,
        ]
    )
