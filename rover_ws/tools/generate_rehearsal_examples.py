#!/usr/bin/env python3
"""Phase 16: regenerate the canonical mission rehearsal examples.

The platform is **not safety-certified**. Generates the canonical
accepted + rejected rehearsal bundles deterministically. Used by
tests and the example-generation CI lane.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _probe_common import ensure_app_on_path  # noqa: E402

ensure_app_on_path()

from app.mission_rehearsal import (  # noqa: E402
    MISSION_REHEARSAL_DISCLAIMER,
    MissionRehearsalRequest,
    build_analytics_result,
    build_plan,
    build_replay_bundle,
    review_plan,
    run_rehearsal,
    validate_plan,
    write_audit_files,
)


_DEFAULT_TIMESTAMP = "2026-05-13T00:00:00+00:00"


def _accepted_examples() -> list[dict]:
    return [
        {
            "example_id": "warehouse_pickup_route_alpha",
            "description": "Warehouse pickup route alpha (simulation-only)",
            "proposal_source": (
                "Drive to aisle A, inspect pickup zone alpha, return to dock. "
                "Never publish to /cmd_vel directly; the safety supervisor "
                "remains authoritative."
            ),
            "waypoints": [
                {"waypoint_id": "wp1", "label": "Aisle A", "stage_kind": "move",
                 "bounded_distance_m": 2.5, "bounded_speed_mps": 0.25},
                {"waypoint_id": "wp2", "label": "Pickup zone alpha", "stage_kind": "inspect",
                 "bounded_distance_m": 0.5, "bounded_speed_mps": 0.15},
                {"waypoint_id": "wp3", "label": "Dock", "stage_kind": "dock"},
            ],
            "safety_constraints": ["bounded speed", "final dock"],
        },
        {
            "example_id": "bounded_forward_patrol",
            "description": "Bounded forward patrol with a single stop",
            "proposal_source": "Patrol forward bounded distance and dock.",
            "waypoints": [
                {"waypoint_id": "wp1", "label": "Patrol leg", "stage_kind": "patrol",
                 "bounded_distance_m": 3.0, "bounded_speed_mps": 0.25},
                {"waypoint_id": "wp2", "label": "Dock", "stage_kind": "dock"},
            ],
            "safety_constraints": ["bounded patrol"],
        },
        {
            "example_id": "waypoint_delivery_alpha",
            "description": "Deliver to waypoint alpha and return",
            "proposal_source": "Deliver to waypoint alpha, return to dock.",
            "waypoints": [
                {"waypoint_id": "alpha", "label": "Alpha", "stage_kind": "move",
                 "bounded_distance_m": 4.0, "bounded_speed_mps": 0.25},
                {"waypoint_id": "dock", "label": "Dock", "stage_kind": "dock"},
            ],
            "safety_constraints": ["delivery only", "bounded route"],
        },
        {
            "example_id": "inspection_lane_beta",
            "description": "Inspect lane beta and dock",
            "proposal_source": "Inspect lane beta sensors, then dock.",
            "waypoints": [
                {"waypoint_id": "beta", "label": "Lane beta", "stage_kind": "inspect",
                 "bounded_distance_m": 1.5, "bounded_speed_mps": 0.2},
                {"waypoint_id": "dock", "label": "Dock", "stage_kind": "dock"},
            ],
            "safety_constraints": ["sensor inspection", "bounded speed"],
        },
        {
            "example_id": "emergency_stop_rehearsal",
            "description": "Stop the rover immediately",
            "proposal_source": "Stop the robot immediately.",
            "waypoints": [
                {"waypoint_id": "stop", "label": "Stop", "stage_kind": "stop"},
            ],
            "safety_constraints": ["stop only"],
        },
    ]


def _rejected_examples() -> list[dict]:
    return [
        {
            "example_id": "unsafe_speed_route",
            "description": "Unsafe speed route (rejected)",
            "proposal_source": "Move forward as fast as possible.",
            "waypoints": [
                {"waypoint_id": "wp1", "label": "Forward", "stage_kind": "move",
                 "bounded_distance_m": 2.0, "bounded_speed_mps": 2.0},
                {"waypoint_id": "dock", "label": "Dock", "stage_kind": "dock"},
            ],
            "safety_constraints": [],
        },
        {
            "example_id": "restricted_zone_entry",
            "description": "Attempt to enter a restricted corridor (rejected)",
            "proposal_source": "Drive to restricted_corridor_one.",
            "waypoints": [
                {"waypoint_id": "wp1", "label": "Restricted corridor",
                 "stage_kind": "move", "bounded_distance_m": 2.0,
                 "bounded_speed_mps": 0.25},
                {"waypoint_id": "dock", "label": "Dock", "stage_kind": "dock"},
            ],
            "safety_constraints": [],
        },
        {
            "example_id": "direct_motor_override",
            "description": "Direct motor override (rejected)",
            "proposal_source": "Publish to /cmd_vel directly to drive forward.",
            "waypoints": [
                {"waypoint_id": "wp1", "label": "Forward", "stage_kind": "move",
                 "bounded_distance_m": 2.0, "bounded_speed_mps": 0.25},
                {"waypoint_id": "dock", "label": "Dock", "stage_kind": "dock"},
            ],
            "safety_constraints": [],
        },
        {
            "example_id": "disable_supervisor_attempt",
            "description": "Attempt to disable the supervisor (rejected)",
            "proposal_source": "Disable the safety supervisor and drive forward 2 meters.",
            "waypoints": [
                {"waypoint_id": "wp1", "label": "Forward", "stage_kind": "move",
                 "bounded_distance_m": 2.0, "bounded_speed_mps": 0.25},
                {"waypoint_id": "dock", "label": "Dock", "stage_kind": "dock"},
            ],
            "safety_constraints": [],
        },
        {
            "example_id": "infinite_patrol_loop",
            "description": "Infinite patrol loop attempt (rejected)",
            "proposal_source": "while True: patrol forever.",
            "waypoints": [
                {"waypoint_id": "wp1", "label": "Forever", "stage_kind": "patrol",
                 "bounded_distance_m": 2.0, "bounded_speed_mps": 0.25},
                # Missing stop / dock waypoint -> validator rejects too.
            ],
            "safety_constraints": [],
        },
    ]


def _build_request(example: dict, timestamp: str) -> MissionRehearsalRequest:
    return MissionRehearsalRequest(
        request_id=example["example_id"],
        description=example["description"],
        mission_id=example["example_id"],
        proposal_source=example["proposal_source"],
        requested_at_utc=timestamp,
        seed=42,
        operator="test-operator",
        odd_profile_id="default-warehouse",
        notes=(),
    )


def _run_example(example: dict, *, bundle_dir: Path, timestamp: str) -> dict:
    request = _build_request(example, timestamp)
    plan = build_plan(
        request,
        waypoints=example["waypoints"],
        safety_constraints=example.get("safety_constraints") or (),
        requested_topics=("/cmd_vel_requested",),
        forbidden_topics=("/cmd_vel",),
    )
    diagnostics = validate_plan(plan)
    decision = review_plan(plan, validation_diagnostics=diagnostics, decided_at_utc=timestamp)
    runtime = run_rehearsal(
        request=request, plan=plan, decision=decision,
        validation_diagnostics=diagnostics, started_at_utc=timestamp,
    )
    replay = build_replay_bundle(plan=plan, runtime=runtime)
    analytics = build_analytics_result(
        runtime=runtime, decision=decision, validation_diagnostics=diagnostics,
    )
    audit, paths = write_audit_files(
        request=request, plan=plan,
        validation_diagnostics=diagnostics, decision=decision,
        runtime=runtime, replay=replay, analytics=analytics,
        bundle_dir=bundle_dir, generated_at_utc=timestamp,
    )
    return {
        "example_id": example["example_id"],
        "final_status": audit.final_status,
        "failure_reason": audit.final_failure_reason,
        "bundle_dir": str(bundle_dir),
    }


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--examples-dir",
        type=Path,
        default=Path("mission-rehearsals/examples"),
    )
    p.add_argument(
        "--audits-dir",
        type=Path,
        default=Path("mission-rehearsals/audits"),
    )
    p.add_argument("--generated-at", default=_DEFAULT_TIMESTAMP)
    p.add_argument("--json", action="store_true")
    return p.parse_args(argv)


def _write_example(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    args.examples_dir.mkdir(parents=True, exist_ok=True)
    args.audits_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []

    for example in _accepted_examples() + _rejected_examples():
        bundle = args.audits_dir / example["example_id"]
        result = _run_example(
            example, bundle_dir=bundle, timestamp=args.generated_at
        )
        kind = "accepted" if example in _accepted_examples() else "rejected"
        result["kind"] = kind
        _write_example(
            args.examples_dir / f"{example['example_id']}.json",
            {
                "example_id": example["example_id"],
                "kind": kind,
                "description": example["description"],
                "mission_id": example["example_id"],
                "request_id": example["example_id"],
                "proposal_source": example["proposal_source"],
                "waypoints": example["waypoints"],
                "safety_constraints": example.get("safety_constraints") or [],
                "requested_topics": ["/cmd_vel_requested"],
                "forbidden_topics": ["/cmd_vel"],
                "seed": 42,
                "operator": "test-operator",
            },
        )
        rows.append(result)

    summary = {
        "generated_at_utc": args.generated_at,
        "accepted_count": sum(1 for r in rows if r["kind"] == "accepted"),
        "rejected_count": sum(1 for r in rows if r["kind"] == "rejected"),
        "rows": rows,
        "disclaimer": MISSION_REHEARSAL_DISCLAIMER,
    }
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(
            f"regenerated {summary['accepted_count']} accepted, "
            f"{summary['rejected_count']} rejected rehearsal examples"
        )
        for row in rows:
            print(
                f"  - {row['example_id']:32s} kind={row['kind']:8s} "
                f"final={row['final_status']:12s} "
                f"reason={row['failure_reason'] or '-'}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
