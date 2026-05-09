#!/usr/bin/env python3
"""Validate the rover URDF / Xacro TF graph.

Usage:
    python tools/validate_tf_tree.py rover_ws/src/rover_description/urdf/rover.urdf.xacro [--json]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _common import emit, ensure_app_on_path

ensure_app_on_path()

from app.validation.tf_validator import validate_urdf_tf_tree


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("urdf", type=Path, help="path to rover.urdf.xacro")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args(argv)
    result = validate_urdf_tf_tree(args.urdf)
    return emit(result.as_dict(), as_json=args.json, ok=result.ok)


if __name__ == "__main__":
    sys.exit(main())
