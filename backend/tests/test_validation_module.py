"""Tests for the runtime validation module.

Covers:

* :func:`validate_run_directory` against deterministic engine output,
* :func:`validate_events_file` against an events.jsonl,
* :func:`validate_bridge_yaml` against the workspace YAML,
* :func:`validate_urdf_tf_tree` against the workspace URDF,
* :func:`validate_safety_pipeline` (drives the engine through six checks).

The tests run the deterministic engine to produce real artefacts and
then validate them. This is the only place in the suite that
exercises the full pipeline + validators together.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.domain.identifiers import RunId, ScenarioId, SequentialIdGenerator
from app.domain.scenarios import (
    RequestedMotionPlan,
    ScenarioDefinition,
    ScenarioInitialState,
)
from app.domain.time import ManualClock
from app.simulation.engine import SimulationEngine
from app.validation.bridge_validator import validate_bridge_yaml
from app.validation.event_validator import (
    EventValidationResult,
    validate_events_file,
    validate_events_iter,
)
from app.validation.replay_validator import validate_run_directory
from app.validation.safety_pipeline_validator import validate_safety_pipeline
from app.validation.tf_validator import validate_urdf_tf_tree


_REPO_ROOT = Path(__file__).resolve().parents[2]
_WORKSPACE_BRIDGE = _REPO_ROOT / "rover_ws" / "src" / "rover_sim_gazebo" / "config" / "ros_gz_bridge.yaml"
_WORKSPACE_URDF = _REPO_ROOT / "rover_ws" / "src" / "rover_description" / "urdf" / "rover.urdf.xacro"


def _run_a_nominal_scenario(tmp_path: Path) -> Path:
    sc = ScenarioDefinition(
        scenario_id=ScenarioId("validation-test"),
        duration_seconds=2.0,
        time_step_ms=100,
        initial_state=ScenarioInitialState(operator_activate_at_ms=200),
        requested_motion=RequestedMotionPlan(linear_velocity=0.4, angular_velocity=0.0),
    )
    eng = SimulationEngine(
        scenario=sc,
        runs_root=tmp_path,
        run_id=RunId("run-validation-test"),
        clock=ManualClock(),
        id_generator=SequentialIdGenerator(),
    )
    eng.run()
    return eng.recorder.run_dir


def test_validate_run_directory_on_real_run(tmp_path: Path) -> None:
    run_dir = _run_a_nominal_scenario(tmp_path)
    result = validate_run_directory(run_dir)
    assert result.ok, result.errors
    assert result.event_count > 0
    assert result.state_count > 0
    assert result.command_count > 0
    assert result.sensor_frame_count > 0
    assert result.transition_count >= 1


def test_validate_run_directory_detects_missing_artefacts(tmp_path: Path) -> None:
    result = validate_run_directory(tmp_path / "does_not_exist")
    assert not result.ok
    assert any("does not exist" in e for e in result.errors)


def test_validate_events_file_on_real_run(tmp_path: Path) -> None:
    run_dir = _run_a_nominal_scenario(tmp_path)
    events = run_dir / "events.jsonl"
    result = validate_events_file(events)
    assert result.ok
    assert result.line_count > 0
    assert result.line_count == result.valid_count


def test_validate_events_iter_rejects_invalid_severity() -> None:
    bad = {
        "timestamp": "2026-01-01T00:00:00Z",
        "run_id": "r",
        "scenario_id": "s",
        "event_id": "e",
        "event_type": "system_lifecycle.boot",
        "severity": "PANIC",
        "subsystem": "x",
        "node": "/x",
        "lifecycle_state": "active",
        "safety_state": "BOOT",
        "source_topic": None,
        "confidence_score": None,
        "requested_motion": None,
        "final_motion": None,
        "reason_code": "boot",
        "message": "m",
    }
    result = validate_events_iter([bad])
    assert not result.ok
    assert result.line_count == 1
    assert result.valid_count == 0


def test_validate_bridge_yaml_against_workspace() -> None:
    assert _WORKSPACE_BRIDGE.exists(), f"bridge YAML missing: {_WORKSPACE_BRIDGE}"
    result = validate_bridge_yaml(_WORKSPACE_BRIDGE)
    assert result.ok, result.errors
    assert "/cmd_vel_authorized" in result.bridged_topics
    assert "/cmd_vel_requested" not in result.bridged_topics
    assert "/cmd_vel" not in result.bridged_topics


def test_validate_bridge_yaml_rejects_forbidden_topic(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        "- ros_topic_name: /cmd_vel_requested\n"
        "  gz_topic_name: /cmd_vel_requested\n"
        "  ros_type_name: geometry_msgs/msg/Twist\n"
        "  gz_type_name: gz.msgs.Twist\n"
        "  direction: ROS_TO_GZ\n"
    )
    result = validate_bridge_yaml(bad)
    assert not result.ok
    assert any("/cmd_vel_requested" in e for e in result.errors)


def test_validate_urdf_tf_tree_against_workspace() -> None:
    assert _WORKSPACE_URDF.exists(), f"URDF missing: {_WORKSPACE_URDF}"
    result = validate_urdf_tf_tree(_WORKSPACE_URDF)
    assert result.ok, result.errors
    for required in (
        "base_link",
        "base_footprint",
        "lidar_link",
        "imu_link",
        "contact_link",
        "left_wheel_link",
        "right_wheel_link",
        "caster_link",
    ):
        assert required in result.links


def test_validate_urdf_rejects_orphan_link(tmp_path: Path) -> None:
    bad = tmp_path / "orphan.urdf"
    bad.write_text(
        '<robot xmlns:xacro="http://www.ros.org/wiki/xacro" name="orphan">\n'
        '  <link name="base_footprint"/>\n'
        '  <link name="base_link"/>\n'
        '  <link name="lidar_link"/>\n'
        '  <link name="imu_link"/>\n'
        '  <link name="contact_link"/>\n'
        '  <link name="left_wheel_link"/>\n'
        '  <link name="right_wheel_link"/>\n'
        '  <link name="caster_link"/>\n'
        '  <link name="orphan_link"/>\n'
        '  <joint name="b_joint" type="fixed">\n'
        '    <parent link="base_footprint"/><child link="base_link"/>\n'
        '  </joint>\n'
        '</robot>\n'
    )
    result = validate_urdf_tf_tree(bad)
    assert not result.ok
    assert any("not reachable" in e for e in result.errors)


def test_validate_safety_pipeline() -> None:
    result = validate_safety_pipeline()
    assert result.ok, result.errors
    # Six checks ran and produced detail keys.
    for key in (
        "authorized_source_checked",
        "safe_stop_zero_motion_checked",
        "estop_latch_checked",
        "clamp_event_checked",
        "fault_no_direct_transition_checked",
        "arbiter_only_construction_checked",
    ):
        assert result.detail.get(key) is True
