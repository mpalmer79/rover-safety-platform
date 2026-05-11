#!/usr/bin/env python3
"""One-command live runtime pipeline.

Drives the Phase 14 live evidence path end-to-end:

* validate the runner profile,
* validate the scenario plan,
* (optional) qualify the host via ``qualify_ros_host.py``,
* (optional) capture a rosbag2 bag via ``live_bag_capture.py``,
* construct the canonical :class:`LiveRuntimeEvidence` record,
* run the live evidence validator,
* (optional) promote the maturity baseline.

The pipeline is the single entry point a self-hosted runner uses to
go from "Jazzy host with built workspace" to "evidence/runtime/<run_id>
populated with honest artefacts." It also supports ``--dry-run`` and
``--static-check-only`` for the GitHub-hosted CI lane, where it
produces ``not_executed`` artefacts without touching ROS.

Usage::

    rover_ws/tools/run_live_runtime_pipeline.py \
        --scenario-plan live-runtime/scenario-plans/smoke-live-runtime.yaml \
        --runner-profile live-runtime/runner-profile.local.json \
        --output evidence/runtime/<run_id>
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from _probe_common import ensure_app_on_path  # noqa: E402

ensure_app_on_path()

from app.live_runtime.evidence_processor import (  # noqa: E402
    EvidenceMode,
    process_evidence,
    write_evidence,
)
from app.live_runtime.maturity_baseline import (  # noqa: E402
    load_maturity_baseline,
    new_not_established_baseline,
    promote_baseline,
)
from app.live_runtime.runner_profile import (  # noqa: E402
    load_runner_profile,
    validate_runner_profile,
)
from app.live_runtime.scenario_plan import (  # noqa: E402
    load_scenario_plan,
    validate_scenario_plan,
)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--scenario-plan",
        type=Path,
        default=Path("live-runtime/scenario-plans/smoke-live-runtime.yaml"),
    )
    p.add_argument(
        "--runner-profile",
        type=Path,
        default=Path("live-runtime/runner-profile.local.json"),
        help="Self-hosted runner profile (gitignored). Falls back to template.",
    )
    p.add_argument(
        "--runner-profile-template",
        type=Path,
        default=Path("live-runtime/runner-profile.template.json"),
        help="Honest template profile to use when --runner-profile is absent",
    )
    p.add_argument("--bag-dir", type=Path, default=None)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--run-id", default=None)
    p.add_argument(
        "--maturity-baseline",
        type=Path,
        default=Path("live-runtime/baselines/maturity-baseline.json"),
    )
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--static-check-only", action="store_true")
    p.add_argument(
        "--capture-bag",
        action="store_true",
        help="Invoke live_bag_capture inline (live mode only)",
    )
    p.add_argument(
        "--promote-baseline",
        action="store_true",
        help="Update the maturity baseline if the run is bag-backed",
    )
    p.add_argument("--json", action="store_true")
    return p.parse_args(argv)


def _resolve_run_id(explicit: str | None, output: Path) -> str:
    if explicit:
        return explicit
    if output.name and output.name not in (".", ""):
        return output.name
    return "live-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _load_runner(args: argparse.Namespace):
    if args.runner_profile.is_file():
        return load_runner_profile(args.runner_profile), str(args.runner_profile)
    if args.runner_profile_template.is_file():
        return (
            load_runner_profile(args.runner_profile_template),
            str(args.runner_profile_template),
        )
    return None, None


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])

    plan = load_scenario_plan(args.scenario_plan)
    plan_errors = validate_scenario_plan(plan)
    if plan_errors:
        print("scenario plan validation failed:", file=sys.stderr)
        for err in plan_errors:
            print(f"  - {err}", file=sys.stderr)
        return 2

    runner, runner_path = _load_runner(args)
    if runner is not None:
        runner_errors = validate_runner_profile(runner)
        if runner_errors:
            print("runner profile validation failed:", file=sys.stderr)
            for err in runner_errors:
                print(f"  - {err}", file=sys.stderr)
            return 2

    run_id = _resolve_run_id(args.run_id, args.output)
    args.output.mkdir(parents=True, exist_ok=True)

    captured_bag_dir: Path | None = args.bag_dir
    capture_status = "skipped"
    if args.capture_bag and not (args.dry_run or args.static_check_only):
        from live_bag_capture import main as capture_main  # type: ignore

        bag_dir = args.output / "bag"
        capture_argv = [
            "--scenario-plan",
            str(args.scenario_plan),
            "--output",
            str(bag_dir),
            "--run-id",
            run_id,
            "--manifest-only",
            str(args.output / "bag-manifest.json"),
        ]
        if runner is not None and runner.bag_format:
            capture_argv += ["--bag-format", runner.bag_format]
        rc = capture_main(capture_argv)
        capture_status = "ok" if rc == 0 else f"failed(rc={rc})"
        captured_bag_dir = bag_dir

    evidence = process_evidence(
        run_id=run_id,
        runner_profile=runner,
        scenario_plan=plan,
        bag_dir=captured_bag_dir,
        dry_run=args.dry_run,
        static_only=args.static_check_only,
    )
    paths = write_evidence(evidence, args.output)

    baseline_msg = "skipped"
    if args.promote_baseline:
        if args.maturity_baseline.is_file():
            previous = load_maturity_baseline(args.maturity_baseline)
        else:
            previous = new_not_established_baseline()
        if evidence.mode is EvidenceMode.BAG_BACKED:
            new_baseline = promote_baseline(
                previous,
                run_id=evidence.run_id,
                bag_dir=evidence.bag_manifest.bag_dir,
                runner_id=runner.runner_id if runner else None,
                scenario_plan_id=evidence.scenario_plan_id,
                captured_at=evidence.generated_at,
            )
            args.maturity_baseline.parent.mkdir(parents=True, exist_ok=True)
            args.maturity_baseline.write_text(
                json.dumps(new_baseline.as_dict(), indent=2, sort_keys=True)
                + "\n",
                encoding="utf-8",
            )
            baseline_msg = "promoted"
        else:
            args.maturity_baseline.parent.mkdir(parents=True, exist_ok=True)
            args.maturity_baseline.write_text(
                json.dumps(previous.as_dict(), indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            baseline_msg = (
                f"left unchanged: evidence mode is '{evidence.mode.value}'"
            )

    summary = {
        "run_id": evidence.run_id,
        "mode": evidence.mode.value,
        "status": evidence.status.value,
        "reason": evidence.reason,
        "scenario_plan": str(args.scenario_plan),
        "scenario_plan_id": plan.plan_id,
        "runner_profile": runner_path,
        "bag_dir": str(captured_bag_dir) if captured_bag_dir else None,
        "capture_status": capture_status,
        "baseline": baseline_msg,
        "evidence_paths": paths,
        "is_bag_backed": evidence.is_bag_backed,
    }
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"run_id: {summary['run_id']}")
        print(f"mode: {summary['mode']}")
        print(f"status: {summary['status']}")
        print(f"reason: {summary['reason']}")
        print(f"capture: {summary['capture_status']}")
        print(f"baseline: {summary['baseline']}")
        for label, p in paths.items():
            print(f"  wrote {label}: {p}")

    if evidence.status.value == "failed":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
