"""Tests for scenario loading and the high-level scenario runner."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.domain.enums import SafetyState
from app.domain.identifiers import RunId, SequentialIdGenerator
from app.domain.scenarios import ScenarioDefinition
from app.domain.time import ManualClock
from app.simulation.scenario_runner import ScenarioRunner


SCENARIOS_DIR = Path(__file__).resolve().parent.parent / "scenarios"


def test_all_bundled_scenarios_parse() -> None:
    files = sorted(SCENARIOS_DIR.glob("*.json"))
    assert files, "expected bundled scenario files"
    for path in files:
        scenario = ScenarioDefinition.from_json_file(path)
        assert scenario.duration_seconds > 0
        assert scenario.time_step_ms > 0


@pytest.mark.parametrize(
    "scenario_file,expected_state",
    [
        ("nominal_run.json", SafetyState.ACTIVE_NORMAL),
        ("stale_lidar_restricted_mode.json", SafetyState.SAFE_STOP),
        ("command_timeout_safe_stop.json", SafetyState.SAFE_STOP),
        ("estop_latched_manual_reset_required.json", SafetyState.E_STOP_LATCHED),
    ],
)
def test_bundled_scenario_runs(scenario_file: str, expected_state: SafetyState, tmp_path: Path) -> None:
    runner = ScenarioRunner(
        runs_root=tmp_path,
        clock=ManualClock(),
        id_generator=SequentialIdGenerator(),
    )
    result = runner.run_from_file(SCENARIOS_DIR / scenario_file)
    assert result.final_safety_state == expected_state
    assert result.run_dir.exists()


def test_runner_produces_unique_run_ids(tmp_path: Path) -> None:
    runner_a = ScenarioRunner(runs_root=tmp_path / "a", clock=ManualClock(), id_generator=SequentialIdGenerator())
    runner_b = ScenarioRunner(runs_root=tmp_path / "b", clock=ManualClock(), id_generator=SequentialIdGenerator())
    sa = ScenarioDefinition.from_json_file(SCENARIOS_DIR / "nominal_run.json")
    ra = runner_a.run(sa, run_id=RunId("run-fixed-1"))
    rb = runner_b.run(sa, run_id=RunId("run-fixed-2"))
    assert ra.run_id != rb.run_id
