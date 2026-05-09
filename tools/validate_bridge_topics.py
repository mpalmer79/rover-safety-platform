#!/usr/bin/env python3
"""Validate a ros_gz_bridge YAML.

Usage:
    python tools/validate_bridge_topics.py rover_ws/src/rover_sim_gazebo/config/ros_gz_bridge.yaml [--json]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _common import emit, ensure_app_on_path

ensure_app_on_path()

from app.validation.bridge_validator import validate_bridge_yaml


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bridge_yaml", type=Path, help="path to ros_gz_bridge YAML")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args(argv)
    result = validate_bridge_yaml(args.bridge_yaml)
    return emit(result.as_dict(), as_json=args.json, ok=result.ok)


if __name__ == "__main__":
    sys.exit(main())
