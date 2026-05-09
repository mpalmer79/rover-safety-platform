"""Run the nominal scenario and print a small summary.

Usage:
    PYTHONPATH=. python examples/run_nominal.py
"""

from __future__ import annotations

from pathlib import Path

from app.domain.identifiers import SequentialIdGenerator
from app.domain.time import ManualClock
from app.simulation.scenario_runner import ScenarioRunner
from app.domain.scenarios import ScenarioDefinition


SCENARIO_PATH = Path(__file__).resolve().parent.parent / "scenarios" / "nominal_run.json"
RUNS_ROOT = Path(__file__).resolve().parent.parent / "runs"


def main() -> int:
    RUNS_ROOT.mkdir(exist_ok=True)
    scenario = ScenarioDefinition.from_json_file(SCENARIO_PATH)
    runner = ScenarioRunner(
        runs_root=RUNS_ROOT,
        clock=ManualClock(),
        id_generator=SequentialIdGenerator(),
    )
    result = runner.run(scenario)
    print("scenario  :", result.scenario_id)
    print("run_id    :", result.run_id)
    print("final     :", result.final_safety_state.value)
    print("transitions:", result.transitions)
    print("events    :", result.event_count)
    print("run_dir   :", result.run_dir)
    print("summary   :", result.summary_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
