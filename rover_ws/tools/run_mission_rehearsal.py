#!/usr/bin/env python3
"""Phase 16: run a deterministic mission rehearsal end-to-end.

The platform is **not safety-certified**. This CLI is the operator
entry point to the Phase 16 governed mission-to-rehearsal pipeline.
It NEVER runs on real hardware, NEVER publishes to ROS, NEVER opens
a network socket, and NEVER executes user code.

Usage::

    rover_ws/tools/run_mission_rehearsal.py
        --mission mission-rehearsals/examples/warehouse_pickup_route_alpha.json
        [--seed 42]
        [--output mission-rehearsals/audits/<id>]
        [--generated-at <iso8601>]
        [--json]

The ``--mission`` JSON declares the request envelope plus the
deterministic waypoint list. See ``docs/SIMULATION_REHEARSAL_PIPELINE.md``
for the schema.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
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
    validate_request,
    write_audit_files,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mission", required=True, type=Path)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--generated-at", default=None)
    p.add_argument("--json", action="store_true")
    return p.parse_args(argv)


def _load_mission(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _str_tuple(value) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    return tuple(str(v) for v in value)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    try:
        mission = _load_mission(args.mission)
    except FileNotFoundError:
        print(f"mission file not found: {args.mission}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"mission file is not valid JSON: {exc}", file=sys.stderr)
        return 2

    if not isinstance(mission, dict):
        print("mission file must contain a JSON object", file=sys.stderr)
        return 2

    timestamp = args.generated_at or _now_iso()
    seed = args.seed if args.seed is not None else int(mission.get("seed", 42))

    request = MissionRehearsalRequest(
        request_id=str(mission.get("request_id", args.output.name or "rehearsal")),
        description=str(mission.get("description", "")),
        mission_id=str(mission.get("mission_id", args.output.name or "mission")),
        proposal_source=str(mission.get("proposal_source", "")),
        requested_at_utc=timestamp,
        seed=seed,
        operator=str(mission.get("operator", "")),
        odd_profile_id=str(mission.get("odd_profile_id", "default-warehouse")),
        notes=_str_tuple(mission.get("notes")),
    )

    req_diags = validate_request(request)
    if req_diags:
        print("request validation failed:", file=sys.stderr)
        for d in req_diags:
            if isinstance(d, dict):
                print(f"  [{d.get('severity')}] {d.get('code')}: {d.get('message')}", file=sys.stderr)
        # Continue: severity-warning diagnostics shouldn't kill the CLI.

    plan = build_plan(
        request,
        waypoints=mission.get("waypoints") or [],
        safety_constraints=mission.get("safety_constraints") or (),
        requested_topics=mission.get("requested_topics") or ("/cmd_vel_requested",),
        forbidden_topics=mission.get("forbidden_topics") or ("/cmd_vel",),
        notes=mission.get("plan_notes") or (),
    )

    diagnostics = validate_plan(plan)
    decision = review_plan(
        plan,
        validation_diagnostics=diagnostics,
        operator=request.operator,
        decided_at_utc=timestamp,
    )
    runtime = run_rehearsal(
        request=request,
        plan=plan,
        decision=decision,
        validation_diagnostics=diagnostics,
        started_at_utc=timestamp,
    )
    replay = build_replay_bundle(plan=plan, runtime=runtime)
    analytics = build_analytics_result(
        runtime=runtime,
        decision=decision,
        validation_diagnostics=diagnostics,
    )
    audit, paths = write_audit_files(
        request=request,
        plan=plan,
        validation_diagnostics=diagnostics,
        decision=decision,
        runtime=runtime,
        replay=replay,
        analytics=analytics,
        bundle_dir=args.output,
        generated_at_utc=timestamp,
    )

    summary = {
        "mission_id": request.mission_id,
        "request_id": request.request_id,
        "final_status": audit.final_status,
        "final_failure_reason": audit.final_failure_reason,
        "safety_status": audit.safety_status,
        "supervisor_decision": decision.decision_status,
        "plan_hash": plan.deterministic_hash,
        "runtime_hash": runtime.deterministic_hash,
        "event_count": len(runtime.events),
        "paths": paths,
        "disclaimer": MISSION_REHEARSAL_DISCLAIMER,
        "generated_at_utc": timestamp,
    }
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"mission_id:        {request.mission_id}")
        print(f"final_status:      {audit.final_status}")
        if audit.final_failure_reason:
            print(f"failure_reason:    {audit.final_failure_reason}")
        print(f"safety_status:     {audit.safety_status}")
        print(f"supervisor:        {decision.decision_status}")
        for label, path in paths.items():
            print(f"  wrote {label}: {path}")

    return 0 if audit.final_status == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
