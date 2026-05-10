#!/usr/bin/env python3
"""Live bag-capture orchestrator (Phase 13).

Drives a live ROS 2 / Gazebo qualification run on a self-hosted
Jazzy host, captures rosbag2 artefacts, and writes an
``evidence/runtime/<run_id>/`` bundle. On hosts where Jazzy or
Gazebo is unavailable (or the user passed ``--dry-run``), the tool
emits a coherent ``not_executed`` evidence bundle with an honest
reason — it never fabricates bags.

The platform is **not safety-certified**.

Usage:
    rover_ws/tools/live_bag_capture.py
        --plan live-runtime/scenario-plans/core-live-qualification.yaml
        --evidence-root evidence/runtime
        --run-id <id>
        --runner-profile <path>
        [--scenario <id> ...]
        [--dry-run]
        [--started-at <iso8601>]
        [--finished-at <iso8601>]
        [--reason <text>]
        [--json]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from _probe_common import ensure_app_on_path  # noqa: E402

ensure_app_on_path()

from app.live_runtime import (  # noqa: E402
    BAG_STATUS_NOT_EXECUTED,
    LIVE_RUN_STATUS_NOT_EXECUTED,
    LiveRunSummary,
    build_not_executed_bundle,
    detect_environment_block_reason,
    init_run_directory,
    load_runner_profile,
    load_scenario_plan,
    runner_supports_live_execution,
    validate_runner_profile,
    validate_scenario_plan,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, default=Path("evidence/runtime"))
    parser.add_argument("--run-id", type=str, required=True)
    parser.add_argument("--runner-profile", type=Path, default=None)
    parser.add_argument("--scenario", type=str, action="append", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--started-at", type=str, default=None)
    parser.add_argument("--finished-at", type=str, default=None)
    parser.add_argument("--reason", type=str, default="")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def _select_scenarios(plan, requested: list[str] | None) -> tuple[str, ...]:
    available = tuple(e.scenario_id for e in plan.entries)
    if not requested:
        return available
    keep = tuple(s for s in available if s in set(requested))
    return keep or available


def _classify(reason_blockers: list[str], dry_run: bool, plan_warnings: tuple[str, ...]) -> tuple[str, str]:
    """Return (overall_status, reason_text)."""

    if dry_run:
        return LIVE_RUN_STATUS_NOT_EXECUTED, "dry-run requested"
    if reason_blockers:
        return LIVE_RUN_STATUS_NOT_EXECUTED, "; ".join(reason_blockers)
    if plan_warnings:
        return LIVE_RUN_STATUS_NOT_EXECUTED, f"scenario plan invalid: {'; '.join(plan_warnings)}"
    return LIVE_RUN_STATUS_NOT_EXECUTED, (
        "live execution path not yet wired; this build only emits "
        "not_executed bundles. See docs/LIVE_BAG_CAPTURE_RUNBOOK.md."
    )


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(list(argv) if argv is not None else sys.argv[1:])

    plan = load_scenario_plan(args.plan)
    plan_warnings = validate_scenario_plan(plan)

    runner_profile = (
        load_runner_profile(args.runner_profile) if args.runner_profile else None
    )
    runner_warnings = validate_runner_profile(runner_profile)

    blockers: list[str] = []
    if args.reason:
        blockers.append(args.reason)
    env_reason = detect_environment_block_reason()
    if env_reason:
        blockers.append(env_reason)
    if runner_warnings:
        blockers.append("; ".join(runner_warnings))
    if not runner_supports_live_execution(runner_profile):
        blockers.append(
            "runner profile does not support live execution "
            "(needs supports_gazebo + supports_rosbag2)"
        )

    status, reason = _classify(blockers, args.dry_run, plan_warnings)

    started_at = args.started_at or _now_iso()
    finished_at = args.finished_at or started_at

    bundle_dir = init_run_directory(args.evidence_root, args.run_id)
    scenario_ids = _select_scenarios(plan, args.scenario) if plan else tuple(args.scenario or ())
    if status == LIVE_RUN_STATUS_NOT_EXECUTED:
        build_not_executed_bundle(
            bundle_dir=bundle_dir,
            run_id=args.run_id,
            plan_id=(plan.plan_id if plan else ""),
            runner_id=(runner_profile.runner_id if runner_profile else ""),
            runner_profile=runner_profile,
            scenario_ids=scenario_ids,
            reason=reason,
            started_at=started_at,
            finished_at=finished_at,
        )

    payload = {
        "run_id": args.run_id,
        "evidence_root": str(args.evidence_root),
        "bundle_dir": str(bundle_dir),
        "plan_id": plan.plan_id if plan else "",
        "scenarios": list(scenario_ids),
        "status": status,
        "bag_status": BAG_STATUS_NOT_EXECUTED if status == LIVE_RUN_STATUS_NOT_EXECUTED else "unknown",
        "reason": reason,
        "runner_warnings": list(runner_warnings),
        "plan_warnings": list(plan_warnings),
    }

    if args.json:
        json.dump(payload, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print(f"[{status}] run_id={args.run_id}")
        print(f"  bundle: {bundle_dir}")
        if reason:
            print(f"  reason: {reason}")
        for w in runner_warnings:
            print(f"  runner warning: {w}")
        for w in plan_warnings:
            print(f"  plan warning: {w}")

    # Return 0 for not_executed (honest fall-back); non-zero only for hard failures.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
