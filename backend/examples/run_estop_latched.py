"""Run the E-stop scenario; verify the latch holds.

Usage:
    PYTHONPATH=. python examples/run_estop_latched.py
"""

from __future__ import annotations

from pathlib import Path

from app.domain.identifiers import SequentialIdGenerator
from app.domain.scenarios import ScenarioDefinition
from app.domain.time import ManualClock
from app.simulation.scenario_runner import ScenarioRunner


SCENARIO_PATH = (
    Path(__file__).resolve().parent.parent
    / "scenarios"
    / "estop_latched_manual_reset_required.json"
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
    assert result.final_safety_state.value == "E_STOP_LATCHED", "expected E_STOP_LATCHED"
    print("E_STOP_LATCHED latched as expected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
