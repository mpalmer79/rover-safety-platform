"""Tests for the run recorder and replay loader."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.domain.enums import ReplayStatus, SafetyState
from app.domain.identifiers import RunId, ScenarioId, SequentialIdGenerator
from app.domain.scenarios import (
    RequestedMotionPlan,
    ScenarioDefinition,
    ScenarioInitialState,
)
from app.domain.time import ManualClock
from app.replay.loader import RunLoader, load_metadata
from app.simulation.engine import SimulationEngine


def _run(tmp_path: Path) -> Path:
    sc = ScenarioDefinition(
        scenario_id=ScenarioId("replay-test"),
        duration_seconds=2.0,
        time_step_ms=100,
        initial_state=ScenarioInitialState(operator_activate_at_ms=200),
        requested_motion=RequestedMotionPlan(linear_velocity=0.3, angular_velocity=0.0),
    )
    eng = SimulationEngine(
        scenario=sc,
        runs_root=tmp_path,
        run_id=RunId("run-replay-0001"),
        clock=ManualClock(),
        id_generator=SequentialIdGenerator(),
    )
    eng.run()
    return eng.recorder.run_dir


def test_run_directory_layout(tmp_path: Path) -> None:
    run_dir = _run(tmp_path)
    assert (run_dir / "metadata.json").exists()
    assert (run_dir / "events.jsonl").exists()
    assert (run_dir / "states.jsonl").exists()
    assert (run_dir / "commands.jsonl").exists()
    assert (run_dir / "sensor_readings.jsonl").exists()
    assert (run_dir / "incident-summary.md").exists()
    assert (run_dir / "bags").is_dir()
    assert (run_dir / "traces").is_dir()


def test_metadata_finalized(tmp_path: Path) -> None:
    run_dir = _run(tmp_path)
    metadata = load_metadata(run_dir)
    assert metadata.status == ReplayStatus.FINALIZED
    assert metadata.ended_sim_ns is not None
    assert metadata.ended_wall is not None


def test_events_jsonl_well_formed(tmp_path: Path) -> None:
    run_dir = _run(tmp_path)
    raw = (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
    assert raw, "expected at least one event"
    for line in raw:
        evt = json.loads(line)
        assert "event_id" in evt
        assert "event_type" in evt
        assert "safety_state" in evt
        assert "run_id" in evt


def test_loader_filters_by_safety_state(tmp_path: Path) -> None:
    run_dir = _run(tmp_path)
    loader = RunLoader(run_dir)
    evt = loader.find_first_safety_state(SafetyState.ACTIVE_NORMAL)
    assert evt is not None
    assert evt["safety_state"] == "ACTIVE_NORMAL"


def test_loader_iterates_all_streams(tmp_path: Path) -> None:
    run_dir = _run(tmp_path)
    loader = RunLoader(run_dir)
    events = list(loader.events())
    states = list(loader.states())
    commands = list(loader.commands())
    sensors = list(loader.sensor_frames())
    assert events
    assert states
    assert commands
    assert sensors


def test_incident_summary_lists_transitions(tmp_path: Path) -> None:
    run_dir = _run(tmp_path)
    summary_md = (run_dir / "incident-summary.md").read_text(encoding="utf-8")
    assert "ACTIVE_NORMAL" in summary_md or "INACTIVE" in summary_md
    assert "Incident Summary" in summary_md
