#!/usr/bin/env python3
"""Reconstruct an incident bundle from runtime + scenario evidence.

Loads the configured ``evidence/runtime/<run_id>/`` and / or
``evidence/scenarios/<scenario_id>/`` directories, normalises the
events, builds a timeline, runs the causality engine, classifies the
incident, and writes a bundle under ``incidents/<incident_id>/``.

Usage:
    rover_ws/tools/reconstruct_incident.py
        [--runtime-run evidence/runtime/<run_id>]
        [--scenario evidence/scenarios/<scenario_id>]
        [--runs-root runs/verify]
        [--incident-id <id>]
        [--output incidents/<incident_id>]
        [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from _probe_common import ensure_app_on_path  # noqa: E402

ensure_app_on_path()

from app.incident_analysis import (  # noqa: E402
    reconstruct_incident,
    write_default_foxglove_layout,
    write_incident_bundle,
)


def _default_incident_id(args: argparse.Namespace) -> str:
    parts: list[str] = []
    if args.scenario:
        parts.append(args.scenario.name)
    if args.runtime_run:
        parts.append(args.runtime_run.name)
    if not parts:
        parts.append("incident")
    parts.append(datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    return "-".join(parts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--runtime-run",
        type=Path,
        default=None,
        help="path to evidence/runtime/<run_id>/",
    )
    parser.add_argument(
        "--scenario",
        type=Path,
        default=None,
        help="path to evidence/scenarios/<scenario_id>/",
    )
    parser.add_argument(
        "--runs-root",
        type=Path,
        default=Path("runs/verify"),
        help="root of recorded runs (used when scenario evidence references a run dir)",
    )
    parser.add_argument(
        "--incident-id",
        type=str,
        default="",
        help="incident id; default derives one from the inputs and the current UTC stamp",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="bundle directory; default: incidents/<incident_id>/",
    )
    parser.add_argument(
        "--foxglove-layout",
        type=Path,
        default=Path("foxglove/layouts/incident-review-layout.json"),
        help="Foxglove layout file to reference in the hints (created if missing)",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if args.runtime_run is None and args.scenario is None:
        parser.error("at least one of --runtime-run or --scenario must be supplied")

    incident_id = args.incident_id or _default_incident_id(args)
    bundle_dir = args.output or Path("incidents") / incident_id

    write_default_foxglove_layout(args.foxglove_layout)

    incident = reconstruct_incident(
        incident_id=incident_id,
        runtime_run_dir=args.runtime_run,
        scenario_dir=args.scenario,
        runs_root=args.runs_root,
        foxglove_layout_path=str(args.foxglove_layout),
    )
    bundle = write_incident_bundle(incident, bundle_dir=bundle_dir)

    if args.json:
        json.dump(bundle.as_dict(), sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print(
            f"incident {incident.incident_id}: severity={incident.severity.value} "
            f"outcome={incident.outcome.value} evidence={incident.evidence_status.value}"
        )
        print(f"  bundle: {bundle.bundle_dir}")
        if incident.cause is not None:
            print(
                f"  cause:  {incident.cause.label} "
                f"({incident.cause.confidence.value})"
            )
        if incident.contradictions:
            print(f"  contradictions: {len(incident.contradictions)}")
        if incident.missing_evidence:
            print(f"  missing evidence: {len(incident.missing_evidence)}")
    return 0 if not incident.contradictions else 1


if __name__ == "__main__":
    sys.exit(main())
