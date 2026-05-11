"""Build a deterministic mission rehearsal plan from request inputs.

The plan is a frozen value object that captures the *intended*
rehearsal. Validation happens in :mod:`rehearsal_validator`; the
plan builder only assembles structured data and computes the
deterministic hash.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Mapping, Sequence

from .models import (
    MissionRehearsalPlan,
    MissionRehearsalRequest,
    RehearsalWaypoint,
)
from .rehearsal_safety import SAFETY_LIMITS


@dataclass(frozen=True)
class BoundedMotionLimits:
    """Per-plan bounded-motion envelope."""

    max_distance_meters: float = SAFETY_LIMITS["max_distance_meters"]
    max_angle_degrees: float = SAFETY_LIMITS["max_angle_degrees"]
    max_linear_speed_mps: float = SAFETY_LIMITS["max_linear_speed_mps"]
    max_angular_speed_rad_s: float = SAFETY_LIMITS["max_angular_speed_rad_s"]


def _hash_plan(payload: dict) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:16]


def _coerce_waypoints(value: Sequence[Mapping[str, object]]) -> tuple[RehearsalWaypoint, ...]:
    out: list[RehearsalWaypoint] = []
    for entry in value:
        if not isinstance(entry, Mapping):
            continue
        out.append(
            RehearsalWaypoint(
                waypoint_id=str(entry.get("waypoint_id") or ""),
                label=str(entry.get("label") or ""),
                stage_kind=str(entry.get("stage_kind") or "move"),
                bounded_distance_m=float(entry.get("bounded_distance_m") or 0.0),
                bounded_angle_deg=float(entry.get("bounded_angle_deg") or 0.0),
                bounded_speed_mps=float(entry.get("bounded_speed_mps") or 0.0),
            )
        )
    return tuple(out)


def _coerce_str_tuple(value) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    return tuple(str(v) for v in value)


def _risk_band(waypoints: tuple[RehearsalWaypoint, ...]) -> str:
    if not waypoints:
        return "blocked"
    risky = any(w.stage_kind not in {"stop", "wait", "dock", "patrol"} for w in waypoints)
    return "guarded" if risky else "low"


def build_plan(
    request: MissionRehearsalRequest,
    *,
    waypoints: Sequence[Mapping[str, object]],
    safety_constraints: Sequence[str] = (),
    requested_topics: Sequence[str] = ("/cmd_vel_requested",),
    forbidden_topics: Sequence[str] = ("/cmd_vel",),
    notes: Sequence[str] = (),
) -> MissionRehearsalPlan:
    wp = _coerce_waypoints(waypoints)
    hash_payload = {
        "mission_id": request.mission_id,
        "request_id": request.request_id,
        "proposal_source": request.proposal_source,
        "odd_profile_id": request.odd_profile_id,
        "seed": request.seed,
        "waypoints": [
            {
                "waypoint_id": w.waypoint_id,
                "label": w.label,
                "stage_kind": w.stage_kind,
                "bounded_distance_m": w.bounded_distance_m,
                "bounded_angle_deg": w.bounded_angle_deg,
                "bounded_speed_mps": w.bounded_speed_mps,
            }
            for w in wp
        ],
        "safety_constraints": list(safety_constraints),
        "requested_topics": list(requested_topics),
        "forbidden_topics": list(forbidden_topics),
    }
    return MissionRehearsalPlan(
        mission_id=request.mission_id,
        request_id=request.request_id,
        proposal_source=request.proposal_source,
        waypoints=wp,
        safety_constraints=_coerce_str_tuple(safety_constraints),
        requested_topics=_coerce_str_tuple(requested_topics),
        forbidden_topics=_coerce_str_tuple(forbidden_topics),
        odd_profile_id=request.odd_profile_id,
        deterministic_hash=_hash_plan(hash_payload),
        risk_band=_risk_band(wp),
        notes=_coerce_str_tuple(notes),
    )
