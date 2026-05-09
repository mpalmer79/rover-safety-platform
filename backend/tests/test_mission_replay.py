"""Replay-integrity tests for the new mission artefacts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.domain.identifiers import RunId, SequentialIdGenerator
from app.domain.scenarios import ScenarioDefinition
from app.domain.time import ManualClock
from app.simulation.engine import SimulationEngine
from app.validation.mission_validator import validate_mission_run
from app.validation.replay_validator import validate_run_directory


_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCENARIOS = _REPO_ROOT / "backend" / "scenarios"


def _run(scenario_file: str, tmp_path: Path) -> Path:
    sc = ScenarioDefinition.from_json_file(_SCENARIOS / scenario_file)
    eng = SimulationEngine(
        scenario=sc,
        runs_root=tmp_path,
        run_id=RunId(f"run-{sc.scenario_id}"),
        clock=ManualClock(),
        id_generator=SequentialIdGenerator(),
    )
    eng.run()
    return eng.recorder.run_dir


def test_mission_run_directory_has_phase2_artefacts(tmp_path: Path) -> None:
    run_dir = _run("nominal_waypoint_patrol.json", tmp_path)
    for required in (
        "mission_state_transitions.jsonl",
        "waypoint_events.jsonl",
        "recovery_events.jsonl",
        "world_model_snapshots.jsonl",
    ):
        assert (run_dir / required).exists(), f"missing {required}"
    base = validate_run_directory(run_dir)
    assert base.ok, base.errors


def test_validate_mission_run_passes_for_nominal(tmp_path: Path) -> None:
    run_dir = _run("nominal_waypoint_patrol.json", tmp_path)
    result = validate_mission_run(run_dir)
    assert result.ok, result.errors
    assert result.final_mission_state == "MISSION_COMPLETE"
    assert result.mission_state_count >= 2  # IDLE→ACTIVE→COMPLETE
    assert result.world_model_snapshot_count > 0


def test_validate_mission_run_rejects_invalid_state_value(tmp_path: Path) -> None:
    run_dir = _run("nominal_waypoint_patrol.json", tmp_path)
    transitions_path = run_dir / "mission_state_transitions.jsonl"
    rows = transitions_path.read_text(encoding="utf-8").splitlines()
    # Corrupt one row by replacing to_state with a non-vocabulary value.
    if rows:
        bad = json.loads(rows[0])
        bad["to_state"] = "NOT_A_REAL_STATE"
        rows[0] = json.dumps(bad)
        transitions_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    result = validate_mission_run(run_dir)
    assert not result.ok
    assert any("NOT_A_REAL_STATE" in e for e in result.errors)


def test_world_model_snapshots_have_required_keys(tmp_path: Path) -> None:
    run_dir = _run("keepout_zone_violation.json", tmp_path)
    path = run_dir / "world_model_snapshots.jsonl"
    found_keepout_violation = False
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            for key in (
                "sim_time_ns",
                "pose_x",
                "pose_y",
                "heading_rad",
                "inside_keepout",
                "near_keepout",
                "inside_restricted",
            ):
                assert key in payload, f"missing {key}"
            if payload["inside_keepout"]:
                found_keepout_violation = True
    assert found_keepout_violation


def test_waypoint_events_present_for_completed_mission(tmp_path: Path) -> None:
    run_dir = _run("nominal_waypoint_patrol.json", tmp_path)
    path = run_dir / "waypoint_events.jsonl"
    completed_ids: list[str] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            if payload["event_type"] == "mission_waypoint.completed":
                completed_ids.append(payload["waypoint_id"])
    assert completed_ids == ["w1", "w2", "w3"]


def test_recovery_events_recorded_when_mission_aborts(tmp_path: Path) -> None:
    run_dir = _run("waypoint_timeout_recovery.json", tmp_path)
    path = run_dir / "recovery_events.jsonl"
    behaviors: set[str] = set()
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            if payload.get("recovery_behavior"):
                behaviors.add(payload["recovery_behavior"])
    assert "backup_and_retry" in behaviors
    assert "mission_abort" in behaviors
