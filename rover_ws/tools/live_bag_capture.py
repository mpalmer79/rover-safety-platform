#!/usr/bin/env python3
"""Live rosbag2 capture helper for the Phase 14 live-runtime pipeline.

This tool wraps ``ros2 bag record`` for a self-hosted Jazzy +
Gazebo Harmonic runner. It does NOT bring up the stack — that is the
caller's responsibility (typically the launch file referenced in the
scenario plan). The tool only:

* validates the supplied scenario plan,
* spawns ``ros2 bag record`` for the configured topics,
* waits for the configured duration,
* terminates the recorder cleanly,
* emits a ``bag-manifest.json`` next to the bag directory.

If ``ros2`` is not on PATH (e.g. the GitHub-hosted CI runner), the
tool exits with status 0 and writes a ``not_executed`` manifest so
the pipeline downstream stays honest. It never fabricates a bag.

Usage::

    rover_ws/tools/live_bag_capture.py \
        --scenario-plan live-runtime/scenario-plans/smoke-live-runtime.yaml \
        --output evidence/runtime/<run_id>/bag \
        --run-id <run_id> \
        [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from _probe_common import ensure_app_on_path  # noqa: E402

ensure_app_on_path()

from app.live_runtime.bag_manifest import (  # noqa: E402
    BagManifest,
    BagStatus,
    inspect_bag_directory,
)
from app.live_runtime.scenario_plan import (  # noqa: E402
    load_scenario_plan,
    validate_scenario_plan,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _not_executed_manifest(
    *,
    bag_dir: Path,
    reason: str,
    scenario_id: str | None,
    run_id: str | None,
) -> BagManifest:
    return BagManifest(
        bag_dir=str(bag_dir),
        status=BagStatus.NOT_EXECUTED,
        reason=reason,
        metadata_present=False,
        chunks=(),
        formats=(),
        scenario_id=scenario_id,
        run_id=run_id,
    )


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenario-plan",
        required=True,
        type=Path,
        help="Path to live scenario plan YAML",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Bag output directory (will be created)",
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help="Run id to record in the bag manifest",
    )
    parser.add_argument(
        "--bag-format",
        choices=("mcap", "db3"),
        default="mcap",
        help="rosbag2 storage format (must match runner profile)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate the scenario plan and emit a not_executed manifest",
    )
    parser.add_argument(
        "--manifest-only",
        type=Path,
        default=None,
        help="Path for the bag manifest JSON (default: alongside bag dir)",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON status to stdout")
    return parser.parse_args(argv)


def _write_manifest(manifest: BagManifest, manifest_path: Path) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest.as_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _record(
    *,
    plan_id: str,
    bag_dir: Path,
    topics: list[str],
    storage: str,
    duration: float,
) -> tuple[BagStatus, str]:
    """Run ``ros2 bag record`` and return (status, reason)."""

    if shutil.which("ros2") is None:
        return BagStatus.NOT_EXECUTED, "ros2 CLI not on PATH; live capture skipped"

    bag_dir.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ros2",
        "bag",
        "record",
        "-s",
        storage,
        "-o",
        str(bag_dir),
        *topics,
    ]
    proc = subprocess.Popen(  # noqa: S603 - command list is curated
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        time.sleep(max(duration, 0.0))
    finally:
        try:
            proc.send_signal(signal.SIGINT)
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
        except ProcessLookupError:
            pass

    if proc.returncode not in (0, -2):
        # rosbag2 returns 0 on clean SIGINT shutdown on most distros;
        # -2 is SIGINT on POSIX; anything else is a real failure.
        stderr = ""
        if proc.stderr is not None:
            stderr = proc.stderr.read().decode("utf-8", errors="replace")[:500]
        return (
            BagStatus.PARTIAL,
            f"ros2 bag record exited with {proc.returncode}: {stderr}",
        )

    if not bag_dir.exists():
        return BagStatus.PARTIAL, "ros2 bag record did not create the bag directory"

    return BagStatus.BAG_BACKED, "ros2 bag record completed and produced output"


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])

    plan = load_scenario_plan(args.scenario_plan)
    plan_errors = validate_scenario_plan(plan)
    if plan_errors:
        print("scenario plan validation failed:", file=sys.stderr)
        for err in plan_errors:
            print(f"  - {err}", file=sys.stderr)
        return 2

    bag_dir: Path = args.output
    manifest_path: Path = args.manifest_only or (
        bag_dir.parent / "bag-manifest.json"
    )

    if args.dry_run:
        manifest = _not_executed_manifest(
            bag_dir=bag_dir,
            reason="dry-run requested; ros2 bag record not invoked",
            scenario_id=plan.plan_id,
            run_id=args.run_id,
        )
        _write_manifest(manifest, manifest_path)
        if args.json:
            print(
                json.dumps(
                    {
                        "status": manifest.status.value,
                        "reason": manifest.reason,
                        "manifest": str(manifest_path),
                        "generated_at": _now_iso(),
                    },
                    indent=2,
                )
            )
        return 0

    status, reason = _record(
        plan_id=plan.plan_id,
        bag_dir=bag_dir,
        topics=list(plan.bag_topics),
        storage=args.bag_format,
        duration=plan.duration_seconds,
    )

    if status is BagStatus.NOT_EXECUTED:
        manifest = _not_executed_manifest(
            bag_dir=bag_dir,
            reason=reason,
            scenario_id=plan.plan_id,
            run_id=args.run_id,
        )
    else:
        # classify the on-disk result; this is the honesty chokepoint.
        manifest = inspect_bag_directory(
            bag_dir, scenario_id=plan.plan_id, run_id=args.run_id
        )
        # If the recorder reported a non-fatal anomaly, downgrade.
        if status is BagStatus.PARTIAL and manifest.is_bag_backed:
            manifest = BagManifest(
                bag_dir=manifest.bag_dir,
                status=BagStatus.PARTIAL,
                reason=reason,
                metadata_present=manifest.metadata_present,
                chunks=manifest.chunks,
                formats=manifest.formats,
                topic_inventory=manifest.topic_inventory,
                scenario_id=manifest.scenario_id,
                run_id=manifest.run_id,
                notes=manifest.notes,
            )

    _write_manifest(manifest, manifest_path)
    if args.json:
        print(
            json.dumps(
                {
                    "status": manifest.status.value,
                    "reason": manifest.reason,
                    "manifest": str(manifest_path),
                    "bag_dir": manifest.bag_dir,
                    "generated_at": _now_iso(),
                },
                indent=2,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
