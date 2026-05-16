"""Run inspection endpoints."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.replay.loader import RunLoader, load_metadata

router = APIRouter(prefix="/runs", tags=["runs"])


_RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,128}$")


def validated_run_id(run_id: str) -> str:
    """FastAPI dependency: reject run_ids that do not match the charset/length policy.

    The string is matched against ``^[A-Za-z0-9_-]{1,128}$``. The original input
    is never echoed back to the caller — error detail is a constant — so
    attempts at reflective injection (terminal escapes, HTML, URL-encoded
    traversal) cannot reach the client.
    """

    if not isinstance(run_id, str) or not _RUN_ID_PATTERN.fullmatch(run_id):
        raise HTTPException(status_code=400, detail="invalid run_id")
    return run_id


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
    runs_root_resolved = runs_root.resolve()
    run_dir = runs_root / run_id
    # Second layer: even though the charset is constrained, resolve and
    # confirm the joined path stays under runs_root. Cheap; closes the
    # door on filesystem-symlink shenanigans created out-of-band.
    try:
        run_dir_resolved = run_dir.resolve()
    except OSError as exc:
        raise HTTPException(status_code=400, detail="invalid run_id") from exc
    if not run_dir_resolved.is_relative_to(runs_root_resolved):
        raise HTTPException(status_code=400, detail="invalid run_id")
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="unknown run_id")
    return RunLoader(run_dir)


@router.get("/{run_id}")
def get_run(
    request: Request,
    run_id: str = Depends(validated_run_id),
) -> dict[str, Any]:
    loader = _loader_for(request, run_id)
    manifest = loader.manifest()
    return manifest.to_dict()


@router.get("/{run_id}/events")
def get_run_events(
    request: Request,
    run_id: str = Depends(validated_run_id),
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
def get_run_summary(
    request: Request,
    run_id: str = Depends(validated_run_id),
) -> dict[str, Any]:
    loader = _loader_for(request, run_id)
    summary_path = loader.run_dir / "incident-summary.md"
    if not summary_path.exists():
        raise HTTPException(status_code=404, detail="incident-summary.md not present")
    return {
        "run_id": run_id,
        "summary_md": summary_path.read_text(encoding="utf-8"),
        "metadata": loader.manifest().metadata.to_dict(),
    }
