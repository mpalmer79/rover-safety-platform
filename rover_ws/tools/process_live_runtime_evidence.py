#!/usr/bin/env python3
"""Feed a single live-runtime evidence bundle into downstream pipelines.

Consumes ``evidence/runtime/<run_id>`` and reports what each
downstream pipeline (incident reconstruction, replay review,
analytics, programme review, reviewer export) would do with it. By
default the tool runs in **dry-run** mode: it never re-runs the
underlying generators, it simply reports which integration steps
the bundle qualifies for and preserves the bundle's ``bag_status``
verbatim.

Use ``--apply`` to actually invoke the integration commands. In
dry-run mode (the default), the script is safe to run anywhere and
its output is deterministic.

The platform is **not safety-certified**.

Usage:
    rover_ws/tools/process_live_runtime_evidence.py
        --bundle evidence/runtime/<run_id>
        [--apply]
        [--json]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from _probe_common import ensure_app_on_path  # noqa: E402

ensure_app_on_path()

from app.live_runtime import (  # noqa: E402
    BAG_STATUS_BAG_BACKED,
    BAG_STATUS_NOT_EXECUTED,
    bag_manifest_is_bag_backed,
    load_bag_manifest,
)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def plan_actions(bundle_dir: Path) -> dict:
    bundle_dir = Path(bundle_dir)
    manifest = load_bag_manifest(bundle_dir / "bag-manifest.json")
    bag_status = manifest.bag_status if manifest else BAG_STATUS_NOT_EXECUTED
    qualifies_for_bag_backed = bag_manifest_is_bag_backed(manifest)

    actions: list[dict] = []

    # Incident reconstruction is appropriate when there is at least an
    # events.jsonl - even static-only.
    events_present = (bundle_dir / "events.jsonl").exists()
    actions.append(
        {
            "step": "incident_reconstruction",
            "qualifies": events_present,
            "command": [
                "python",
                "rover_ws/tools/reconstruct_incident.py",
                "--evidence",
                str(bundle_dir),
            ],
            "reason": (
                "events.jsonl present"
                if events_present
                else "events.jsonl missing; reconstruction skipped"
            ),
        }
    )

    actions.append(
        {
            "step": "replay_review_bundle",
            "qualifies": qualifies_for_bag_backed,
            "command": [
                "python",
                "rover_ws/tools/build_replay_review_bundle.py",
                "--bag",
                str(bundle_dir / "bags"),
            ],
            "reason": (
                "bag_backed manifest with real artefacts"
                if qualifies_for_bag_backed
                else f"bag_status={bag_status} does not qualify for bag-backed review"
            ),
        }
    )

    actions.append(
        {
            "step": "replay_analytics",
            "qualifies": qualifies_for_bag_backed,
            "command": ["python", "rover_ws/tools/generate_replay_analytics.py"],
            "reason": (
                "bag-backed evidence available"
                if qualifies_for_bag_backed
                else "no bag-backed evidence; analytics skipped"
            ),
        }
    )

    actions.append(
        {
            "step": "programme_review",
            "qualifies": True,
            "command": ["python", "rover_ws/tools/generate_programme_review.py"],
            "reason": "programme review always re-runs over on-disk evidence",
        }
    )

    actions.append(
        {
            "step": "reviewer_export",
            "qualifies": True,
            "command": ["python", "rover_ws/tools/generate_reviewer_export.py"],
            "reason": "reviewer export always re-runs over on-disk evidence",
        }
    )

    return {
        "bundle_dir": str(bundle_dir),
        "bag_status": bag_status,
        "preserved_bag_status": bag_status,  # explicit: never mutated downstream
        "qualifies_for_bag_backed": qualifies_for_bag_backed,
        "actions": actions,
    }


def apply_actions(plan: dict) -> dict:
    results: list[dict] = []
    for action in plan["actions"]:
        if not action["qualifies"]:
            results.append({**action, "executed": False, "exit_code": None})
            continue
        try:
            outcome = subprocess.run(
                action["command"],
                check=False,
                capture_output=True,
                text=True,
            )
            results.append(
                {
                    **action,
                    "executed": True,
                    "exit_code": outcome.returncode,
                    "stdout_tail": outcome.stdout[-2000:],
                    "stderr_tail": outcome.stderr[-2000:],
                }
            )
        except FileNotFoundError as exc:
            results.append(
                {**action, "executed": False, "error": f"command not found: {exc}"}
            )
    return {**plan, "actions": results}


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(list(argv) if argv is not None else sys.argv[1:])
    plan = plan_actions(args.bundle)
    if args.apply:
        plan = apply_actions(plan)
    if args.json:
        json.dump(plan, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print(f"bundle: {plan['bundle_dir']}")
        print(f"bag_status: {plan['bag_status']} (preserved: {plan['preserved_bag_status']})")
        for a in plan["actions"]:
            mark = "+" if a["qualifies"] else "-"
            ran = " (executed)" if a.get("executed") else ""
            print(f"  [{mark}] {a['step']}{ran}: {a['reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
