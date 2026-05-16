"""Simulation endpoints."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from app.domain.scenarios import ScenarioDefinition
from app.simulation.scenario_runner import ScenarioRunner

router = APIRouter(prefix="/simulation", tags=["simulation"])

_log = logging.getLogger(__name__)


@router.post("/run")
def run_scenario(payload: dict[str, Any], request: Request) -> dict[str, Any]:
    """Run a scenario described by the JSON payload.

    The payload must conform to :class:`ScenarioDefinition.from_dict`.
    Returns the run id and final safety state. Server-side filesystem
    paths (e.g. the run directory) are deliberately NOT returned — the
    caller addresses runs by ``run_id``, not by absolute path.
    """

    try:
        scenario = ScenarioDefinition.from_dict(payload)
    except (ValueError, KeyError, TypeError) as exc:
        # Log the real reason server-side so operators can debug, but
        # return a generic detail so we do not leak internals or
        # reflect attacker-controlled strings.
        _log.warning("invalid scenario payload rejected: %s", exc)
        raise HTTPException(status_code=400, detail="invalid scenario payload") from exc

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
    }
