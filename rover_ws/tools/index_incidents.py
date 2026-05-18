#!/usr/bin/env python3
"""Scan ``incidents/`` and write the incident index.

Outputs ``incidents/index.json`` and ``docs/INCIDENT_INDEX.md``.

Usage:
    rover_ws/tools/index_incidents.py
        [--incidents-root incidents]
        [--json-out incidents/index.json]
        [--md-out docs/INCIDENT_INDEX.md]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _probe_common import ensure_app_on_path  # noqa: E402

ensure_app_on_path()

from app.incident_analysis.index import (  # noqa: E402
    build_incident_index,
    write_incident_index,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--incidents-root",
        type=Path,
        default=Path("incidents"),
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=Path("incidents/index.json"),
    )
    parser.add_argument(
        "--md-out",
        type=Path,
        default=Path("docs/INCIDENT_INDEX.md"),
    )
    args = parser.parse_args(argv)

    index = build_incident_index(incidents_root=args.incidents_root)
    write_incident_index(index, json_path=args.json_out, markdown_path=args.md_out)
    print(
        f"incident-index: rows={len(index.rows)} json={args.json_out} md={args.md_out}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
