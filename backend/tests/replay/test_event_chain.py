"""End-to-end tests for the tamper-evident event chain (#13).

These tests record a run, then prove that the replay validator detects:
* a flipped byte mid-file,
* a truncated last line,
* a deleted middle event.
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
from app.telemetry.chain import CHAIN_FIELD, GENESIS_HASH, hash_canonical
from app.simulation.engine import SimulationEngine
from app.validation.replay_validator import validate_run_directory


def _record_run(tmp_path: Path) -> Path:
    scenario = ScenarioDefinition(
        scenario_id=ScenarioId("chain-test"),
        duration_seconds=1.0,
        time_step_ms=100,
        initial_state=ScenarioInitialState(operator_activate_at_ms=200),
        requested_motion=RequestedMotionPlan(linear_velocity=0.4, angular_velocity=0.0),
    )
    engine = SimulationEngine(
        scenario=scenario,
        runs_root=tmp_path,
        run_id=RunId("run-chain"),
        clock=ManualClock(),
        id_generator=SequentialIdGenerator(),
    )
    engine.run()
    return engine.recorder.run_dir


def _read_lines(p: Path) -> list[str]:
    return [ln for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]


def test_recorder_produces_validatable_chain(tmp_path: Path) -> None:
    run_dir = _record_run(tmp_path)
    result = validate_run_directory(run_dir)
    assert result.ok, result.errors
    # First event chains to genesis.
    lines = _read_lines(run_dir / "events.jsonl")
    first = json.loads(lines[0])
    assert first[CHAIN_FIELD] == GENESIS_HASH
    # Chain links: each event's prev_event_hash == hash of previous canonical bytes.
    prev = first
    for raw in lines[1:]:
        evt = json.loads(raw)
        assert evt[CHAIN_FIELD] == hash_canonical(prev)
        prev = evt


def test_flipping_one_field_breaks_chain(tmp_path: Path) -> None:
    run_dir = _record_run(tmp_path)
    events_path = run_dir / "events.jsonl"
    lines = _read_lines(events_path)
    mid_idx = len(lines) // 2
    mid = json.loads(lines[mid_idx])
    mid["reason_code"] = "tampered_reason_code"
    lines[mid_idx] = json.dumps(
        mid, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    events_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    result = validate_run_directory(run_dir)
    assert not result.ok
    assert any("chain_broken" in e for e in result.errors), result.errors


def test_truncating_last_line_breaks_tip(tmp_path: Path) -> None:
    run_dir = _record_run(tmp_path)
    events_path = run_dir / "events.jsonl"
    lines = _read_lines(events_path)
    events_path.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")

    result = validate_run_directory(run_dir)
    assert not result.ok
    # Either chain_broken on a missing line or events_count/tip mismatch — both
    # are emitted under the chain_broken family.
    assert any("chain_broken" in e for e in result.errors), result.errors


def test_deleting_middle_event_breaks_chain(tmp_path: Path) -> None:
    run_dir = _record_run(tmp_path)
    events_path = run_dir / "events.jsonl"
    lines = _read_lines(events_path)
    assert len(lines) >= 3
    del lines[len(lines) // 2]
    events_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    result = validate_run_directory(run_dir)
    assert not result.ok
    assert any("chain_broken" in e for e in result.errors), result.errors


def test_metadata_carries_tip_and_count(tmp_path: Path) -> None:
    run_dir = _record_run(tmp_path)
    metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
    assert isinstance(metadata.get("events_chain_tip"), str)
    assert len(metadata["events_chain_tip"]) == 64
    assert isinstance(metadata.get("events_count"), int)
    assert metadata["events_count"] > 0
