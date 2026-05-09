"""Simulation endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from app.domain.scenarios import ScenarioDefinition
from app.simulation.scenario_runner import ScenarioRunner

router = APIRouter(prefix="/simulation", tags=["simulation"])


@router.post("/run")
def run_scenario(payload: dict[str, Any], request: Request) -> dict[str, Any]:
    """Run a scenario described by the JSON payload.

    The payload must conform to :class:`ScenarioDefinition.from_dict`.
    Returns the run id and final safety state.
    """

    try:
        scenario = ScenarioDefinition.from_dict(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    runs_root: Path = request.app.state.runs_root
    runner = ScenarioRunner(runs_root=runs_root)
    result = runner.run(scenario)
    return {
        "run_id": str(result.run_id),
        "scenario_id": str(result.scenario_id),
        "final_safety_state": result.final_safety_state.value,
        "duration_ms": result.duration_ms,
        "transitions": result.transitions,
        "fired_faults": list(result.fired_faults),
        "event_count": result.event_count,
        "run_dir": str(result.run_dir),
    }
