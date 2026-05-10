#!/usr/bin/env python3
"""Build a replay review bundle for an incident.

Reads ``incident-report.json`` from the supplied incident directory,
inspects candidate bag locations (the incident dir, the optional
runtime evidence dir, and the gitignored ``runs/<run_id>/``), builds
a Foxglove session + manifest + markers + report, and writes them
back into the incident directory.

The CLI never opens a bag file. It produces metadata only. CI runs
without ROS / Gazebo / Foxglove are still expected to succeed; the
output simply records ``bag_status=missing_bag`` (or
``static_only`` when the underlying incident is static-only).

Usage:
    rover_ws/tools/build_replay_review_bundle.py
        --incident incidents/<incident_id>
        [--run evidence/runtime/<run_id>]
        [--runs-root runs/verify]
        [--foxglove-layout foxglove/layouts/incident-review-layout.json]
        [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _probe_common import ensure_app_on_path  # noqa: E402

ensure_app_on_path()

from app.replay_review import build_replay_review  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--incident",
        type=Path,
        required=True,
        help="path to incidents/<incident_id>/",
    )
    parser.add_argument(
        "--run",
        type=Path,
        default=None,
        help="path to evidence/runtime/<run_id>/ (optional)",
    )
    parser.add_argument(
        "--runs-root",
        type=Path,
        default=Path("runs/verify"),
        help="root of recorded runs (default: runs/verify)",
    )
    parser.add_argument(
        "--foxglove-layout",
        type=Path,
        default=Path("foxglove/layouts/incident-review-layout.json"),
        help="Foxglove layout file referenced from the session metadata",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if not (args.incident / "incident-report.json").exists():
        sys.stderr.write(
            f"incident-report.json not found under {args.incident}\n"
            "Run rover_ws/tools/reconstruct_incident.py first.\n"
        )
        return 2

    bundle = build_replay_review(
        incident_dir=args.incident,
        runtime_run_dir=args.run,
        runs_root=args.runs_root,
        foxglove_layout_path=str(args.foxglove_layout),
    )

    if args.json:
        json.dump(bundle.as_dict(), sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print(
            f"replay-review {bundle.incident_id}: "
            f"bag={bundle.manifest.bag_status.value} "
            f"replay={bundle.report.replay_execution_status.value} "
            f"origin={bundle.report.evidence_origin.value} "
            f"markers={len(bundle.markers)}"
        )
        print(f"  bundle: {bundle.bundle_dir}")
    return 0 if bundle.report.replay_execution_status.value not in {"failed"} else 1


if __name__ == "__main__":
    sys.exit(main())
