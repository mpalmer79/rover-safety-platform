#!/usr/bin/env python3
"""Phase 16: re-validate a stored mission rehearsal audit.

The platform is **not safety-certified**. Reads a stored
``rehearsal-audit.json`` and re-runs the validator + supervisor
gates against the plan it records. Used by the CI lane to detect
tampered audits.

Usage::

    rover_ws/tools/validate_mission_rehearsal.py
        --audit mission-rehearsals/audits/<id>/rehearsal-audit.json
        [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _probe_common import ensure_app_on_path  # noqa: E402

ensure_app_on_path()

from app.mission_rehearsal import (  # noqa: E402
    MissionRehearsalPlan,
    MissionRehearsalRequest,
    RehearsalWaypoint,
    review_plan,
    validate_plan,
    validate_request,
)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--audit", required=True, type=Path)
    p.add_argument("--json", action="store_true")
    return p.parse_args(argv)


def _str_tuple(value) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    return tuple(str(v) for v in value)


def _request_from_dict(d) -> MissionRehearsalRequest:
    return MissionRehearsalRequest(
        request_id=str(d.get("request_id") or ""),
        description=str(d.get("description") or ""),
        mission_id=str(d.get("mission_id") or ""),
        proposal_source=str(d.get("proposal_source") or ""),
        requested_at_utc=str(d.get("requested_at_utc") or ""),
        seed=int(d.get("seed") or 0),
        operator=str(d.get("operator") or ""),
        odd_profile_id=str(d.get("odd_profile_id") or "default-warehouse"),
        notes=_str_tuple(d.get("notes")),
    )


def _plan_from_dict(d) -> MissionRehearsalPlan:
    waypoints = tuple(
        RehearsalWaypoint(
            waypoint_id=str(w.get("waypoint_id") or ""),
            label=str(w.get("label") or ""),
            stage_kind=str(w.get("stage_kind") or "move"),
            bounded_distance_m=float(w.get("bounded_distance_m") or 0.0),
            bounded_angle_deg=float(w.get("bounded_angle_deg") or 0.0),
            bounded_speed_mps=float(w.get("bounded_speed_mps") or 0.0),
        )
        for w in (d.get("waypoints") or [])
    )
    return MissionRehearsalPlan(
        mission_id=str(d.get("mission_id") or ""),
        request_id=str(d.get("request_id") or ""),
        proposal_source=str(d.get("proposal_source") or ""),
        waypoints=waypoints,
        safety_constraints=_str_tuple(d.get("safety_constraints")),
        requested_topics=_str_tuple(d.get("requested_topics")),
        forbidden_topics=_str_tuple(d.get("forbidden_topics")),
        odd_profile_id=str(d.get("odd_profile_id") or "default-warehouse"),
        deterministic_hash=str(d.get("deterministic_hash") or ""),
        risk_band=str(d.get("risk_band") or "guarded"),
        notes=_str_tuple(d.get("notes")),
    )


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    try:
        payload = json.loads(args.audit.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"audit file not found: {args.audit}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"audit file is not valid JSON: {exc}", file=sys.stderr)
        return 2

    request = _request_from_dict(payload.get("request") or {})
    plan_dict = payload.get("plan")
    if plan_dict is None:
        print("audit has no plan; nothing to validate", file=sys.stderr)
        return 1
    plan = _plan_from_dict(plan_dict)

    req_diags = validate_request(request)
    plan_diags = validate_plan(plan)
    decision = review_plan(plan, validation_diagnostics=plan_diags)

    summary = {
        "audit_path": str(args.audit),
        "request_diagnostics": [dict(d) for d in req_diags],
        "plan_diagnostics": [dict(d) for d in plan_diags],
        "supervisor_decision": {
            "decision_status": decision.decision_status,
            "safety_status": decision.safety_status,
            "rejected_reasons": list(decision.rejected_reasons),
        },
        "valid": (
            not req_diags
            and not any(d.get("severity") == "rejection" for d in plan_diags)
            and decision.decision_status == "approved"
        ),
    }
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"valid: {summary['valid']}")
        for d in plan_diags:
            print(f"  [{d.get('severity')}] {d.get('code')}: {d.get('message')}")
        print(f"supervisor: {decision.decision_status}")

    return 0 if summary["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
