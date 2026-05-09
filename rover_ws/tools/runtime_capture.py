#!/usr/bin/env python3
"""Runtime fault-scenario capture probe.

Replays a short Phase-1C / Phase-2 scenario through the deterministic
engine (static-only) or against the live ROS 2 stack (live, when
``--ros-launch`` is supplied on a Jazzy host) and captures the
resulting transitions. The point of this probe is to prove that a
fault injection produces the documented safety-state response — not
to be a substitute for the full scenario verifier.

Modes:

* **static-only**: drives the scenario through
  :func:`app.verification.scenario_verifier.verify_scenario`, which
  uses the deterministic engine. Captures the resulting safety
  transitions and returns the canonical status.
* **live**: out of scope for this environment. Live capture requires
  driving the live ROS 2 stack with the fault-injection node and
  recording ``/safety/events`` and ``/safety/state`` for the duration
  of the scenario. The probe surfaces ``not_executed`` with a clear
  reason when invoked without ``--ros-launch`` on a Jazzy host.

Usage:
    rover_ws/tools/runtime_capture.py --scenario stale_lidar_restricted_mode \\
        [--static-only] [--evidence-root evidence/runtime] [--run-id <id>]
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from _probe_common import (  # noqa: E402  (sys.path mutated)
    ProbeOutcome,
    common_argparser,
    detect_rclpy,
    emit,
    ensure_app_on_path,
    write_json,
)

ensure_app_on_path()

from app.runtime_validation.evidence_layout import (  # noqa: E402
    EvidenceLayout,
    new_runtime_run_id,
)
from app.verification.scenario_verifier import (  # noqa: E402
    SCENARIO_EXPECTATIONS,
    verify_scenario,
)


_DEFAULT_SCENARIO = "stale_lidar_restricted_mode"


def _scenario_choices() -> list[str]:
    return [exp.scenario_id for exp in SCENARIO_EXPECTATIONS]


def run_static(*, scenario_id: str, runs_root: Path) -> dict:
    expectation = next(
        (e for e in SCENARIO_EXPECTATIONS if e.scenario_id == scenario_id),
        None,
    )
    if expectation is None:
        return {
            "scenario_id": scenario_id,
            "status": "failed",
            "detail": f"unknown scenario: {scenario_id}",
        }
    runs_root.mkdir(parents=True, exist_ok=True)
    verification = verify_scenario(expectation, runs_root=runs_root)
    return {
        "scenario_id": expectation.scenario_id,
        "status": verification.status.value,
        "expected_safety_state": expectation.expected_safety_state.value,
        "observed_safety_state": (
            verification.final_safety_state.value
            if verification.final_safety_state is not None
            else ""
        ),
        "expected_mission_state": expectation.expected_mission_state,
        "observed_mission_state": verification.final_mission_state,
        "fired_faults": list(verification.fired_faults),
        "recovery_engagement_count": verification.recovery_engagement_count,
        "checks": [c.as_dict() for c in verification.checks],
        "run_dir": str(verification.run_dir) if verification.run_dir else "",
        "not_executed_reason": verification.not_executed_reason,
    }


def main(argv: list[str] | None = None) -> int:
    parser = common_argparser(description=__doc__)
    parser.add_argument(
        "--scenario",
        default=_DEFAULT_SCENARIO,
        choices=_scenario_choices(),
        help="scenario id to drive through the engine (default: stale_lidar_restricted_mode)",
    )
    parser.add_argument(
        "--ros-launch",
        action="store_true",
        help=(
            "drive the scenario against a live ROS 2 stack instead of "
            "the deterministic engine; requires Jazzy + Gazebo + "
            "fault-injection node"
        ),
    )
    parser.add_argument(
        "--runs-root",
        type=Path,
        default=Path("runs/runtime"),
        help="root directory under which the scenario run is recorded",
    )
    args = parser.parse_args(argv)

    available, why = detect_rclpy()
    use_live = available and args.ros_launch and not args.static_only
    mode = "live" if use_live else "static-only"

    run_id = args.run_id or new_runtime_run_id(prefix=f"capture-{args.scenario}")
    layout = EvidenceLayout(root=args.evidence_root, run_id=run_id).ensure()

    static_payload = run_static(
        scenario_id=args.scenario,
        runs_root=args.runs_root,
    )
    payload = {
        "run_id": run_id,
        "mode": mode,
        "generated_at_utc": datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
        "scenario": args.scenario,
        "static": static_payload,
    }

    if use_live:  # pragma: no cover - requires ros2 + gazebo
        # Live capture is intentionally not implemented in this
        # environment. Honest reporting: emit not_executed with the
        # reason, plus the deterministic-engine result for context.
        payload["live"] = {
            "status": "not_executed",
            "reason": (
                "live runtime fault-injection capture requires the "
                "rover_fault_injection ROS node, Gazebo Harmonic, and "
                "a Jazzy host; not exercised by this probe."
            ),
        }
        status = "not_executed"
        detail = (
            "live runtime capture not implemented; "
            f"deterministic engine reports {static_payload['status']}"
        )
        reason = payload["live"]["reason"]
    else:
        status = static_payload.get("status", "not_executed")
        detail = (
            f"deterministic-engine capture: scenario {args.scenario} "
            f"=> {status}"
        )
        reason = why or "static-only mode"

    snapshot_path = (
        layout.run_dir / f"runtime-capture-{args.scenario}.json"
    )
    write_json(snapshot_path, payload)
    outcome = ProbeOutcome(
        name="runtime_capture",
        mode=mode,
        status=status,
        detail=detail,
        reason=reason,
        artefact_paths=[str(snapshot_path)],
        payload=payload,
    )
    return emit(outcome, as_json=args.json)


if __name__ == "__main__":
    sys.exit(main())
