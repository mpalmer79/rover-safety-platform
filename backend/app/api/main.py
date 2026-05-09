"""FastAPI gateway entry point.

The gateway is optional. Installing the ``api`` extra
(``pip install -e .[api]``) is the supported way to get FastAPI and
uvicorn. Tests do not depend on this module.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    from fastapi import FastAPI
except ImportError as exc:  # pragma: no cover - import-time guard
    raise RuntimeError(
        "FastAPI is required to import app.api.main. "
        "Install with: pip install '.[api]'"
    ) from exc

from app.api.routes import health as health_routes
from app.api.routes import runs as runs_routes
from app.api.routes import simulation as simulation_routes


def create_app(*, runs_root: Path | str = "runs") -> "FastAPI":
    """Construct the FastAPI application.

    The application is instantiated per-call so multiple test apps can
    coexist with their own ``runs_root`` directories.
    """

    app = FastAPI(
        title="Rover Safety Platform Backend",
        version="0.1.0",
        description="Deterministic simulation core for the Autonomous Safety Validation Rover Platform.",
    )
    app.state.runs_root = Path(runs_root)
    app.include_router(health_routes.router)
    app.include_router(simulation_routes.router)
    app.include_router(runs_routes.router)
    return app


def get_default_app() -> "FastAPI":  # pragma: no cover - convenience hook
    return create_app()
