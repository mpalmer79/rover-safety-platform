"""Run inspection endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request

from app.replay.loader import RunLoader, load_metadata

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("")
def list_runs(request: Request) -> list[dict[str, Any]]:
    runs_root: Path = request.app.state.runs_root
    if not runs_root.exists():
        return []
    runs: list[dict[str, Any]] = []
    for entry in sorted(runs_root.iterdir()):
        if not entry.is_dir():
            continue
        try:
            metadata = load_metadata(entry)
        except FileNotFoundError:
            continue
        runs.append(
            {
                "run_id": str(metadata.run_id),
                "scenario_id": str(metadata.scenario_id),
                "started_wall": metadata.started_wall,
                "status": metadata.status.value,
            }
        )
    return runs


def _loader_for(request: Request, run_id: str) -> RunLoader:
    runs_root: Path = request.app.state.runs_root
    run_dir = runs_root / run_id
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail=f"unknown run_id: {run_id}")
    return RunLoader(run_dir)


@router.get("/{run_id}")
def get_run(run_id: str, request: Request) -> dict[str, Any]:
    loader = _loader_for(request, run_id)
    manifest = loader.manifest()
    return manifest.to_dict()


@router.get("/{run_id}/events")
def get_run_events(
    run_id: str,
    request: Request,
    event_type: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=10_000),
) -> list[dict[str, Any]]:
    loader = _loader_for(request, run_id)
    out: list[dict[str, Any]] = []
    for evt in loader.events():
        if event_type is not None and evt.get("event_type") != event_type:
            continue
        out.append(evt)
        if len(out) >= limit:
            break
    return out


@router.get("/{run_id}/summary")
def get_run_summary(run_id: str, request: Request) -> dict[str, Any]:
    loader = _loader_for(request, run_id)
    summary_path = loader.run_dir / "incident-summary.md"
    if not summary_path.exists():
        raise HTTPException(status_code=404, detail="incident-summary.md not present")
    return {
        "run_id": run_id,
        "summary_md": summary_path.read_text(encoding="utf-8"),
        "metadata": loader.manifest().metadata.to_dict(),
    }
