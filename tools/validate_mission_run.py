#!/usr/bin/env python3
"""Validate the mission artefacts of a recorded run directory.

Usage:
    python tools/validate_mission_run.py runs/<run_id> [--json]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _common import emit, ensure_app_on_path

ensure_app_on_path()

from app.validation.mission_validator import validate_mission_run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path, help="path to runs/<run_id>")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args(argv)
    result = validate_mission_run(args.run_dir)
    return emit(result.as_dict(), as_json=args.json, ok=result.ok)


if __name__ == "__main__":
    sys.exit(main())
