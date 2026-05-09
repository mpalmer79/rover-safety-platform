"""Validate the ros_gz_bridge YAML.

The motion authority guarantee depends on this file: only
``/cmd_vel_authorized`` may be bridged ROS_TO_GZ on a motion topic.
A bridge entry forwarding ``/cmd_vel_requested`` (or generic
``/cmd_vel``) into Gazebo would make the supervisor bypassable.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml


REQUIRED_TOPICS = {
    "/clock",
    "/cmd_vel_authorized",
    "/odom",
    "/scan",
    "/imu",
    "/contact",
    "/joint_states",
    "/tf",
}


@pytest.fixture
def bridge(src_root) -> list[dict]:
    path = src_root / "rover_sim_gazebo" / "config" / "ros_gz_bridge.yaml"
    return yaml.safe_load(path.read_text())


def test_bridge_yaml_lists_required_topics(bridge: list[dict]) -> None:
    names = {entry["ros_topic_name"] for entry in bridge}
    missing = REQUIRED_TOPICS - names
    assert not missing, f"bridge missing topics: {missing}"


def test_authorized_topic_is_only_motion_topic_bridged(bridge: list[dict]) -> None:
    motion_entries = [
        e for e in bridge
        if "Twist" in e["ros_type_name"]
    ]
    assert len(motion_entries) == 1, "expected exactly one bridged motion topic"
    entry = motion_entries[0]
    assert entry["ros_topic_name"] == "/cmd_vel_authorized"
    assert entry["direction"] == "ROS_TO_GZ"


def test_no_requested_motion_bridged(bridge: list[dict]) -> None:
    for entry in bridge:
        assert entry["ros_topic_name"] != "/cmd_vel_requested", (
            "ros_gz_bridge must not forward /cmd_vel_requested"
        )
        assert entry["ros_topic_name"] != "/cmd_vel", (
            "ros_gz_bridge must not forward generic /cmd_vel"
        )


def test_bridge_directions_are_valid(bridge: list[dict]) -> None:
    allowed = {"GZ_TO_ROS", "ROS_TO_GZ", "BIDIRECTIONAL"}
    for entry in bridge:
        assert entry["direction"] in allowed, (
            f"unknown direction {entry['direction']!r} on {entry['ros_topic_name']}"
        )


def test_clock_is_bridged_in_one_direction_only(bridge: list[dict]) -> None:
    clock = [e for e in bridge if e["ros_topic_name"] == "/clock"]
    assert len(clock) == 1
    assert clock[0]["direction"] == "GZ_TO_ROS"
