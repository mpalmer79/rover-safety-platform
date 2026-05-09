#!/usr/bin/env python3
"""Drive the deterministic engine through the safety-pipeline checks.

The tool validates:

* only the supervisor's arbiter constructs AuthorizedMotionCommand,
* SAFE_STOP forces zero motion,
* E_STOP_LATCHED does not self-clear,
* clamping emits motion_arbitration.clamped events,
* fault injection does not emit safety_transition.* events.

Usage:
    python tools/validate_safety_pipeline.py [--runs-root <dir>] [--json]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _common import emit, ensure_app_on_path

ensure_app_on_path()

from app.validation.safety_pipeline_validator import validate_safety_pipeline


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-root", type=Path, default=None)
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args(argv)
    result = validate_safety_pipeline(runs_root=args.runs_root)
    return emit(result.as_dict(), as_json=args.json, ok=result.ok)


if __name__ == "__main__":
    sys.exit(main())
