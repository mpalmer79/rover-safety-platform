"""Parse the .msg files and assert their fields match the docs.

These tests do not require ``rosidl_*`` — they perform a small
hand-rolled parse and validate the field set, which is enough to catch
regressions like a renamed ``run_id`` or a removed ``reason_code``.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


_FIELD_RE = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_/]*(?:\[[^\]]*\])?)\s+([A-Za-z_][A-Za-z0-9_]*)\s*"
)


def _parse_msg(path: Path) -> dict[str, str]:
    fields: dict[str, str] = {}
    for raw in path.read_text().splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        match = _FIELD_RE.match(line)
        if not match:
            continue
        type_, name = match.group(1), match.group(2)
        fields[name] = type_
    return fields


@pytest.fixture
def msg_dir(src_root):
    return src_root / "rover_msgs" / "msg"


def test_safety_state_message(msg_dir):
    fields = _parse_msg(msg_dir / "SafetyState.msg")
    for required in (
        "stamp",
        "run_id",
        "scenario_id",
        "state",
        "reason_code",
        "confidence_score",
        "estop_latched",
        "lifecycle_state",
    ):
        assert required in fields, f"missing field {required}"
    assert fields["stamp"] == "builtin_interfaces/Time"
    assert fields["state"] == "string"
    assert fields["estop_latched"] == "bool"


def test_motion_authorization_message(msg_dir):
    fields = _parse_msg(msg_dir / "MotionAuthorization.msg")
    for required in (
        "decision",
        "reason_code",
        "safety_state",
        "requested",
        "authorized",
        "was_clamped",
        "confidence_score",
    ):
        assert required in fields
    assert fields["requested"] == "geometry_msgs/Twist"
    assert fields["authorized"] == "geometry_msgs/Twist"
    assert fields["was_clamped"] == "bool"


def test_sensor_health_message(msg_dir):
    fields = _parse_msg(msg_dir / "SensorHealth.msg")
    for required in (
        "sensor_type",
        "sensor_id",
        "status",
        "reason_code",
        "age_ms",
        "confidence_score",
        "sequence_number",
    ):
        assert required in fields
    assert fields["age_ms"] == "int32"
    assert fields["sequence_number"] == "uint64"


def test_fault_event_message(msg_dir):
    fields = _parse_msg(msg_dir / "FaultEvent.msg")
    for required in (
        "fault_id",
        "fault_type",
        "phase",
        "target",
        "reason_code",
        "attributes_json",
    ):
        assert required in fields


def test_replay_marker_message(msg_dir):
    fields = _parse_msg(msg_dir / "ReplayMarker.msg")
    for required in ("kind", "label", "reason_code", "payload_json"):
        assert required in fields


def test_mission_state_message(msg_dir):
    fields = _parse_msg(msg_dir / "MissionState.msg")
    for required in (
        "mission_id",
        "state",
        "reason_code",
        "safety_state",
        "mission_progress",
    ):
        assert required in fields
    assert fields["state"] == "string"
    assert fields["mission_progress"] == "float32"


def test_waypoint_status_message(msg_dir):
    fields = _parse_msg(msg_dir / "WaypointStatus.msg")
    for required in (
        "waypoint_id",
        "status",
        "distance_to_goal_m",
        "elapsed_ms",
        "timeout_ms",
        "waypoint_index",
        "waypoint_total",
    ):
        assert required in fields


def test_waypoint_event_message(msg_dir):
    fields = _parse_msg(msg_dir / "WaypointEvent.msg")
    for required in ("phase", "reason_code", "waypoint_id", "waypoint_index"):
        assert required in fields


def test_recovery_event_message(msg_dir):
    fields = _parse_msg(msg_dir / "RecoveryEvent.msg")
    for required in ("phase", "reason_code", "recovery_behavior", "attempt_count"):
        assert required in fields


def test_world_model_state_message(msg_dir):
    fields = _parse_msg(msg_dir / "WorldModelState.msg")
    for required in (
        "pose_x",
        "forward_clearance_m",
        "forward_sector_clear",
        "inside_keepout",
        "speed_limit_linear",
        "speed_limit_angular",
    ):
        assert required in fields
    assert fields["forward_sector_clear"] == "bool"


def test_hazard_report_message(msg_dir):
    fields = _parse_msg(msg_dir / "HazardReport.msg")
    for required in ("kind", "reason_code", "severity", "summary", "zone_id"):
        assert required in fields
