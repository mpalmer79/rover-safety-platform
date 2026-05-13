"""Waypoint-coordinate bounds tests for mission_validator (#21).

The validator now numerically bounds pose_x / pose_y from
world_model_snapshots.jsonl against the scenario's declared
operational extents. When no extents are declared it falls back to a
sanity range of +/-10_000 m and emits a warning.
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
from app.validation.mission_validator import (
    WaypointBounds,
    validate_mission_run,
)


def _snapshot(sim_time_ns: int, *, pose_x: float = 0.0, pose_y: float = 0.0) -> dict:
    return {
        "sim_time_ns": sim_time_ns,
        "pose_x": pose_x,
        "pose_y": pose_y,
        "heading_rad": 0.0,
        "occupancy_min_range_m": 1.0,
        "occupancy_mean_range_m": 5.0,
        "forward_sector_clear": True,
        "forward_clearance_m": 5.0,
        "inside_keepout": False,
        "near_keepout": False,
        "inside_restricted": False,
        "boundary_violations": [],
    }


def _record_run(tmp_path: Path, *, snapshots: list[dict] | None = None) -> Path:
    scenario = ScenarioDefinition(
        scenario_id=ScenarioId("bounds-test"),
        duration_seconds=0.5,
        time_step_ms=100,
        initial_state=ScenarioInitialState(operator_activate_at_ms=200),
        requested_motion=RequestedMotionPlan(linear_velocity=0.4, angular_velocity=0.0),
    )
    engine = SimulationEngine(
        scenario=scenario,
        runs_root=tmp_path,
        run_id=RunId("run-bounds"),
        clock=ManualClock(),
        id_generator=SequentialIdGenerator(),
    )
    engine.run()
    run_dir = engine.recorder.run_dir
    snap_path = run_dir / "world_model_snapshots.jsonl"
    snaps = snapshots if snapshots is not None else [
        _snapshot(i * 100_000_000, pose_x=float(i), pose_y=float(i)) for i in range(3)
    ]
    snap_path.write_text(
        "\n".join(json.dumps(s, separators=(",", ":")) for s in snaps) + "\n",
        encoding="utf-8",
    )
    return run_dir


def test_default_extents_emit_a_warning(tmp_path: Path) -> None:
    run_dir = _record_run(tmp_path)
    result = validate_mission_run(run_dir)  # bounds defaults
    assert any(
        "did not declare operational extents" in w for w in result.warnings
    ), result.warnings


def test_explicit_extents_skip_warning(tmp_path: Path) -> None:
    run_dir = _record_run(tmp_path)
    result = validate_mission_run(
        run_dir,
        bounds=WaypointBounds(
            min_pose_x=-100.0, max_pose_x=100.0,
            min_pose_y=-100.0, max_pose_y=100.0,
            explicit=True,
        ),
    )
    assert not any(
        "did not declare operational extents" in w for w in result.warnings
    )


def test_oversized_pose_is_rejected(tmp_path: Path) -> None:
    run_dir = _record_run(
        tmp_path,
        snapshots=[_snapshot(0, pose_x=1_000_000.0)],
    )
    result = validate_mission_run(run_dir)
    assert any(
        "outside operational extents" in e for e in result.errors
    ), result.errors


def test_nan_pose_is_rejected(tmp_path: Path) -> None:
    run_dir = _record_run(
        tmp_path,
        snapshots=[_snapshot(0, pose_x=float("nan"))],
    )
    result = validate_mission_run(run_dir)
    # Non-finite must be caught as a structured failure (not silently accepted).
    assert not result.ok, result.errors


def test_scenario_definition_rejects_non_finite_extents() -> None:
    with pytest.raises(ValueError):
        ScenarioDefinition(
            scenario_id=ScenarioId("bad"),
            duration_seconds=1.0,
            min_pose_x=float("nan"),
        )


def test_scenario_definition_rejects_inverted_extents() -> None:
    with pytest.raises(ValueError):
        ScenarioDefinition(
            scenario_id=ScenarioId("bad"),
            duration_seconds=1.0,
            min_pose_x=10.0,
            max_pose_x=-10.0,
        )
