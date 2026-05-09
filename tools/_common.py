"""Shared helpers for the tools/ CLIs."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def ensure_app_on_path() -> None:
    """Make :mod:`app` importable when the tools are run from the repo root."""

    backend = Path(__file__).resolve().parent.parent / "backend"
    if str(backend) not in sys.path:
        sys.path.insert(0, str(backend))


def emit(result_dict: dict, *, as_json: bool, ok: bool) -> int:
    if as_json:
        json.dump(result_dict, sys.stdout, indent=2, sort_keys=True, default=str)
        sys.stdout.write("\n")
        return 0 if ok else 1
    # Human-friendly fallback. Keep it boring; CI parses JSON.
    status = "OK" if ok else "FAILED"
    print(f"[{status}]")
    for key in ("source", "run_dir", "ok", "errors", "warnings"):
        if key in result_dict and result_dict[key] not in (None, [], {}):
            print(f"  {key}: {result_dict[key]}")
    return 0 if ok else 1
