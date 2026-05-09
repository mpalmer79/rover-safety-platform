"""End-to-end test for the Phase 1C scenario validation suite.

Runs every required scenario through the deterministic engine and
asserts the documented outcome. This is the most important behavioural
test in this repo: it is the gate for "scenario validation suite
executes correctly" in the Phase 1C acceptance criteria.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.validation.scenario_suite import (
    builtin_scenarios,
    run_scenario_suite,
)


def test_builtin_scenarios_count() -> None:
    cases = builtin_scenarios()
    # Phase 1C explicitly requires seven scenarios.
    assert len(cases) == 7


def test_each_builtin_scenario_has_a_file_on_disk(tmp_path: Path) -> None:
    from app.validation.scenario_suite import SCENARIOS_DIR

    for case in builtin_scenarios():
        assert (SCENARIOS_DIR / case.scenario_file).exists()


def test_full_suite_passes(tmp_path: Path) -> None:
    result = run_scenario_suite(runs_root=tmp_path / "runs")
    assert result.ok, [
        f"{o.case.scenario_file}: {o.errors}" for o in result.outcomes if not o.ok
    ]
    assert result.failure_count == 0
    # Every scenario produced a run directory and its replay validation
    # passed.
    for outcome in result.outcomes:
        assert outcome.run_dir is not None
        assert outcome.run_dir.exists()
        assert outcome.replay.ok, outcome.replay.errors


def test_each_scenario_produces_required_artefacts(tmp_path: Path) -> None:
    result = run_scenario_suite(runs_root=tmp_path / "runs")
    for outcome in result.outcomes:
        for required in (
            "metadata.json",
            "events.jsonl",
            "states.jsonl",
            "commands.jsonl",
            "sensor_readings.jsonl",
            "incident-summary.md",
        ):
            assert (outcome.run_dir / required).exists(), (
                f"{outcome.case.scenario_file} run dir missing {required}"
            )


def test_e_stop_scenario_records_critical_severity(tmp_path: Path) -> None:
    """The E-stop scenario must record a CRITICAL severity event."""

    import json

    result = run_scenario_suite(runs_root=tmp_path / "runs")
    estop = next(
        o for o in result.outcomes
        if o.case.scenario_file == "estop_latched_manual_reset_required.json"
    )
    events_path = estop.run_dir / "events.jsonl"
    has_critical = False
    has_estop_transition = False
    with events_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            payload = json.loads(line)
            if payload.get("severity") == "CRITICAL":
                has_critical = True
            if (
                payload.get("event_type") == "safety_transition.entered"
                and payload.get("safety_state") == "E_STOP_LATCHED"
            ):
                has_estop_transition = True
    assert has_critical, "expected at least one CRITICAL event in the E-stop scenario"
    assert has_estop_transition, "expected safety_transition.entered E_STOP_LATCHED"
