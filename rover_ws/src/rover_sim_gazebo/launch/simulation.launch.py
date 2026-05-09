"""Launch Gazebo Harmonic with the validation world and the bridge.

Composable: callers (typically rover_bringup) layer rover_spawn,
robot_state_publisher, and the safety runtime on top of this launch.
"""

from __future__ import annotations

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:
    world = LaunchConfiguration("world")
    headless = LaunchConfiguration("headless")
    verbose = LaunchConfiguration("verbose")
    bridge_config = LaunchConfiguration("bridge_config")

    default_world = PathJoinSubstitution(
        [FindPackageShare("rover_sim_gazebo"), "worlds", "validation_world.sdf"]
    )
    default_bridge = PathJoinSubstitution(
        [FindPackageShare("rover_sim_gazebo"), "config", "ros_gz_bridge.yaml"]
    )

    gz_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("ros_gz_sim"), "launch", "gz_sim.launch.py"]
            )
        ),
        launch_arguments={
            "gz_args": [
                "-r ",
                world,
                " --headless-rendering ",
                headless,
                " --verbose ",
                verbose,
            ],
        }.items(),
    )

    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="ros_gz_bridge",
        parameters=[{"config_file": bridge_config, "use_sim_time": True}],
        output="screen",
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "world",
                default_value=default_world,
                description="Path to the SDF world to load.",
            ),
            DeclareLaunchArgument(
                "headless",
                default_value="false",
                description="Run Gazebo without rendering.",
            ),
            DeclareLaunchArgument(
                "verbose",
                default_value="2",
                description="Gazebo verbosity level.",
            ),
            DeclareLaunchArgument(
                "bridge_config",
                default_value=default_bridge,
                description="Path to the ros_gz_bridge YAML.",
            ),
            gz_launch,
            bridge,
        ]
    )
