"""FastAPI gateway entry point.

The gateway is optional. Installing the ``api`` extra
(``pip install -e .[api]``) is the supported way to get FastAPI and
uvicorn. Tests do not depend on this module.

This server has **no authentication**. It is intended for local
development against a deterministic in-process simulation. The
``__main__`` entry point below defaults to binding ``127.0.0.1``;
binding ``0.0.0.0`` requires the explicit ``--allow-remote`` flag.
"""

from __future__ import annotations

import argparse
import logging
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


_log = logging.getLogger(__name__)


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


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m app.api.main",
        description="Run the rover-safety-platform FastAPI gateway (local dev).",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Bind address (default 127.0.0.1).")
    parser.add_argument("--port", type=int, default=8000, help="TCP port (default 8000).")
    parser.add_argument("--runs-root", default="runs", help="Filesystem root for recorded runs.")
    parser.add_argument(
        "--allow-remote",
        action="store_true",
        help=(
            "Permit binding to 0.0.0.0 (or another non-loopback host). "
            "Required if --host is not 127.0.0.1/localhost/::1."
        ),
    )
    return parser


def _is_loopback(host: str) -> bool:
    return host in {"127.0.0.1", "localhost", "::1"}


if __name__ == "__main__":  # pragma: no cover - manual entry point
    import uvicorn

    args = _build_arg_parser().parse_args()
    if not _is_loopback(args.host) and not args.allow_remote:
        raise SystemExit(
            f"refusing to bind non-loopback host {args.host!r} without --allow-remote. "
            "The API has no authentication; pass --allow-remote only on a trusted network."
        )
    logging.basicConfig(level=logging.INFO)
    _log.warning(
        "API trusts its caller; no authentication enabled. "
        "Use --allow-remote only on a trusted network."
    )
    uvicorn.run(
        create_app(runs_root=args.runs_root),
        host=args.host,
        port=args.port,
        log_level="info",
    )
