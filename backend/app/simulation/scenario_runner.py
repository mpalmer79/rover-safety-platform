"""High-level scenario runner.

Wraps :class:`SimulationEngine` so callers can run a scenario from a
file path or a definition object with one call.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from app.domain.identifiers import IdGenerator, RunId
from app.domain.scenarios import ScenarioDefinition
from app.domain.time import ManualClock
from app.simulation.engine import SimulationEngine, SimulationResult


class ScenarioRunner:
    def __init__(
        self,
        *,
        runs_root: str | Path,
        clock: Optional[ManualClock] = None,
        id_generator: Optional[IdGenerator] = None,
    ) -> None:
        self._runs_root = Path(runs_root)
        self._clock = clock
        self._id_generator = id_generator

    def run(
        self,
        scenario: ScenarioDefinition,
        *,
        run_id: Optional[RunId] = None,
        contact_assertions: tuple[int, ...] = (),
    ) -> SimulationResult:
        engine = SimulationEngine(
            scenario=scenario,
            runs_root=self._runs_root,
            run_id=run_id,
            clock=self._clock,
            id_generator=self._id_generator,
            contact_assertions=contact_assertions,
        )
        return engine.run()

    def run_from_file(self, path: str | Path) -> SimulationResult:
        scenario = ScenarioDefinition.from_json_file(path)
        return self.run(scenario)
