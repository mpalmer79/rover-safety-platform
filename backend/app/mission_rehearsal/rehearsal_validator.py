"""Mission plan validator.

Runs after :mod:`rehearsal_plan` and before the supervisor review.
The validator never decides authority — it only flags structural
problems and per-waypoint safety violations.
"""

from __future__ import annotations

from typing import Mapping

from .models import (
    MissionRehearsalPlan,
    MissionRehearsalRequest,
    RehearsalFailureReason,
)
from .rehearsal_safety import SAFETY_LIMITS, scan_text


def _diagnostic(code: str, message: str, *, parameter: str = "", severity: str = "rejection") -> dict:
    return {
        "code": code,
        "severity": severity,
        "message": message,
        "parameter": parameter,
    }


def validate_request(request: MissionRehearsalRequest) -> tuple[Mapping[str, object], ...]:
    out: list[Mapping[str, object]] = []
    if not request.request_id.strip():
        out.append(
            _diagnostic(
                RehearsalFailureReason.MALFORMED_MISSION_GRAPH.value,
                "request_id is empty",
                parameter="request_id",
            )
        )
    if not request.mission_id.strip():
        out.append(
            _diagnostic(
                RehearsalFailureReason.MALFORMED_MISSION_GRAPH.value,
                "mission_id is empty",
                parameter="mission_id",
            )
        )
    if not request.proposal_source.strip():
        out.append(
            _diagnostic(
                RehearsalFailureReason.UNSAFE_PROPOSAL_SOURCE.value,
                "proposal_source is empty",
                parameter="proposal_source",
                severity="warning",
            )
        )
    return tuple(out)


def validate_plan(plan: MissionRehearsalPlan) -> tuple[Mapping[str, object], ...]:
    out: list[Mapping[str, object]] = []
    if not plan.waypoints:
        out.append(
            _diagnostic(
                RehearsalFailureReason.MALFORMED_MISSION_GRAPH.value,
                "mission plan has no waypoints",
            )
        )

    for waypoint in plan.waypoints:
        if waypoint.bounded_distance_m < 0:
            out.append(
                _diagnostic(
                    RehearsalFailureReason.OUT_OF_RANGE_PARAMETER.value,
                    f"waypoint {waypoint.waypoint_id} has negative distance",
                    parameter="bounded_distance_m",
                )
            )
        if waypoint.bounded_distance_m > SAFETY_LIMITS["max_distance_meters"]:
            out.append(
                _diagnostic(
                    RehearsalFailureReason.OUT_OF_RANGE_PARAMETER.value,
                    f"waypoint {waypoint.waypoint_id} distance "
                    f"{waypoint.bounded_distance_m} exceeds limit "
                    f"{SAFETY_LIMITS['max_distance_meters']}",
                    parameter="bounded_distance_m",
                )
            )
        if abs(waypoint.bounded_angle_deg) > SAFETY_LIMITS["max_angle_degrees"]:
            out.append(
                _diagnostic(
                    RehearsalFailureReason.OUT_OF_RANGE_PARAMETER.value,
                    f"waypoint {waypoint.waypoint_id} |angle| exceeds limit",
                    parameter="bounded_angle_deg",
                )
            )
        if waypoint.bounded_speed_mps > SAFETY_LIMITS["max_linear_speed_mps"]:
            out.append(
                _diagnostic(
                    RehearsalFailureReason.UNSAFE_SPEED.value,
                    f"waypoint {waypoint.waypoint_id} speed "
                    f"{waypoint.bounded_speed_mps} exceeds limit "
                    f"{SAFETY_LIMITS['max_linear_speed_mps']}",
                    parameter="bounded_speed_mps",
                )
            )
        if waypoint.stage_kind not in {
            "move",
            "patrol",
            "inspect",
            "wait",
            "stop",
            "dock",
        }:
            out.append(
                _diagnostic(
                    RehearsalFailureReason.MALFORMED_MISSION_GRAPH.value,
                    f"unsupported stage_kind {waypoint.stage_kind!r}",
                    parameter="stage_kind",
                )
            )

    if "/cmd_vel" in plan.requested_topics:
        out.append(
            _diagnostic(
                RehearsalFailureReason.DIRECT_ACTUATOR_COMMAND.value,
                "/cmd_vel is not a permitted requested topic",
                parameter="requested_topics",
            )
        )
    if "/cmd_vel_requested" not in plan.requested_topics and any(
        w.stage_kind in {"move", "patrol", "inspect"} for w in plan.waypoints
    ):
        out.append(
            _diagnostic(
                RehearsalFailureReason.MISSING_STOP_CONDITION.value,
                "motion waypoints require /cmd_vel_requested in requested_topics",
                parameter="requested_topics",
            )
        )

    has_stop = any(w.stage_kind in {"stop", "dock"} for w in plan.waypoints)
    if any(w.stage_kind in {"move", "patrol"} for w in plan.waypoints) and not has_stop:
        out.append(
            _diagnostic(
                RehearsalFailureReason.MISSING_STOP_CONDITION.value,
                "plan with motion waypoints must include a stop or dock waypoint",
            )
        )

    # Scan the proposal source for forbidden tokens.
    matches = scan_text(plan.proposal_source)
    for matched, reason, message in matches:
        out.append(
            _diagnostic(
                reason,
                f"proposal source contains {matched!r}: {message}",
                parameter="proposal_source",
            )
        )
    matches_notes = scan_text("\n".join(plan.notes))
    for matched, reason, message in matches_notes:
        out.append(
            _diagnostic(
                reason,
                f"plan note contains {matched!r}: {message}",
                parameter="notes",
            )
        )

    return tuple(out)
