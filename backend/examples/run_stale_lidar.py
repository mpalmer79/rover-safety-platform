"""Run the stale-LiDAR scenario.

Usage:
    PYTHONPATH=. python examples/run_stale_lidar.py
"""

from __future__ import annotations

from pathlib import Path

from app.domain.identifiers import SequentialIdGenerator
from app.domain.scenarios import ScenarioDefinition
from app.domain.time import ManualClock
from app.simulation.scenario_runner import ScenarioRunner


SCENARIO_PATH = (
    Path(__file__).resolve().parent.parent / "scenarios" / "stale_lidar_restricted_mode.json"
)
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
    print("final state:", result.final_safety_state.value)
    print("fired faults:", result.fired_faults)
    print("transitions:", result.transitions)
    print("run_dir   :", result.run_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
