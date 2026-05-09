#!/usr/bin/env python3
"""Validate an events.jsonl file against the canonical event envelope.

Usage:
    python tools/validate_event_integrity.py runs/<run_id>/events.jsonl [--json]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _common import emit, ensure_app_on_path

ensure_app_on_path()

from app.validation.event_validator import validate_events_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("events_file", type=Path, help="path to events.jsonl")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args(argv)
    result = validate_events_file(args.events_file)
    return emit(result.as_dict(), as_json=args.json, ok=result.ok)


if __name__ == "__main__":
    sys.exit(main())
