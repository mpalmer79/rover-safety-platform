"""Deterministic rehearsal runtime.

Drives the state machine from ``created`` through ``completed`` (or
the appropriate failure terminal) and emits the canonical event
stream. No real motion runs; the runtime only simulates the
authority chain by emitting `MOTION_REQUEST_SIMULATED` events that
the supervisor has *already* approved.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Mapping

from .models import (
    MissionRehearsalDecision,
    MissionRehearsalEvent,
    MissionRehearsalPlan,
    MissionRehearsalRequest,
    MissionRehearsalRuntime,
    MissionRehearsalTimeline,
    RehearsalDecisionStatus,
    RehearsalEventType,
    RehearsalFailureReason,
    RehearsalSafetyStatus,
    RehearsalStatus,
    RehearsalWaypoint,
)
from .rehearsal_events import build_event, deterministic_hash
from .rehearsal_state_machine import StateMachineError, next_status
from .rehearsal_timeline import build_timeline


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _waypoint_event(
    *,
    mission_id: str,
    sequence: int,
    waypoint: RehearsalWaypoint,
    subtype: str,
    description: str,
) -> MissionRehearsalEvent:
    return build_event(
        mission_id=mission_id,
        sequence=sequence,
        event_type=RehearsalEventType.MOTION.value,
        event_subtype=subtype,
        source_phase="rehearsal_runtime",
        severity="info",
        description=description,
        payload={
            "waypoint_id": waypoint.waypoint_id,
            "label": waypoint.label,
            "stage_kind": waypoint.stage_kind,
            "bounded_distance_m": waypoint.bounded_distance_m,
            "bounded_angle_deg": waypoint.bounded_angle_deg,
            "bounded_speed_mps": waypoint.bounded_speed_mps,
        },
    )


def _supervisor_event(
    *,
    mission_id: str,
    sequence: int,
    decision: MissionRehearsalDecision,
) -> MissionRehearsalEvent:
    return build_event(
        mission_id=mission_id,
        sequence=sequence,
        event_type=RehearsalEventType.SUPERVISOR.value,
        event_subtype=decision.decision_status,
        source_phase="rehearsal_supervisor",
        severity=(
            "info"
            if decision.decision_status == RehearsalDecisionStatus.APPROVED.value
            else "rejection"
        ),
        description=" | ".join(decision.rationale) or decision.decision_status,
        payload={
            "decision_id": decision.decision_id,
            "decision_status": decision.decision_status,
            "safety_status": decision.safety_status,
            "rejected_reasons": list(decision.rejected_reasons),
        },
    )


def _validation_event(
    *,
    mission_id: str,
    sequence: int,
    diagnostics: tuple[Mapping[str, object], ...],
) -> MissionRehearsalEvent:
    any_rejection = any(
        isinstance(d, Mapping) and d.get("severity") == "rejection"
        for d in diagnostics
    )
    return build_event(
        mission_id=mission_id,
        sequence=sequence,
        event_type=RehearsalEventType.VALIDATION.value,
        event_subtype="rejected" if any_rejection else "passed",
        source_phase="rehearsal_validator",
        severity="rejection" if any_rejection else "info",
        description=(
            "validation rejected"
            if any_rejection
            else "validation passed"
        ),
        payload={"diagnostics": [dict(d) for d in diagnostics if isinstance(d, Mapping)]},
    )


def run_rehearsal(
    *,
    request: MissionRehearsalRequest,
    plan: MissionRehearsalPlan,
    decision: MissionRehearsalDecision,
    validation_diagnostics: Iterable[Mapping[str, object]] = (),
    started_at_utc: str | None = None,
) -> MissionRehearsalRuntime:
    """Run the deterministic state machine and produce the event stream."""

    diagnostics = tuple(validation_diagnostics)
    timestamp = started_at_utc or _now_iso()

    events: list[MissionRehearsalEvent] = []
    transitions: list[tuple[str, str, str]] = []
    sequence = 0
    current_status: str = RehearsalStatus.CREATED.value
    safety_escalations = 0
    failure_reason = ""

    events.append(
        build_event(
            mission_id=plan.mission_id,
            sequence=sequence,
            event_type=RehearsalEventType.MISSION.value,
            event_subtype="created",
            source_phase="rehearsal_runtime",
            severity="info",
            description="mission rehearsal created",
            payload={
                "request_id": request.request_id,
                "seed": request.seed,
                "risk_band": plan.risk_band,
                "deterministic_hash": plan.deterministic_hash,
            },
        )
    )
    sequence += 1

    events.append(_validation_event(
        mission_id=plan.mission_id, sequence=sequence, diagnostics=diagnostics
    ))
    sequence += 1

    has_validator_rejection = any(
        isinstance(d, Mapping) and d.get("severity") == "rejection"
        for d in diagnostics
    )

    if has_validator_rejection:
        transitions.append((current_status, RehearsalStatus.REJECTED.value, "validator_rejected"))
        current_status = next_status(current_status, RehearsalStatus.REJECTED.value)
        failure_reason = _first_rejection_code(diagnostics)
    else:
        transitions.append((current_status, RehearsalStatus.VALIDATED.value, "validation_passed"))
        current_status = next_status(current_status, RehearsalStatus.VALIDATED.value)

    # Supervisor decision event
    events.append(_supervisor_event(
        mission_id=plan.mission_id, sequence=sequence, decision=decision
    ))
    sequence += 1

    if current_status != RehearsalStatus.REJECTED.value:
        if decision.decision_status != RehearsalDecisionStatus.APPROVED.value:
            transitions.append((current_status, RehearsalStatus.REJECTED.value, "supervisor_rejected"))
            current_status = next_status(current_status, RehearsalStatus.REJECTED.value)
            failure_reason = (
                RehearsalFailureReason.MISSING_SUPERVISOR_APPROVAL.value
                if not decision.rejected_reasons
                else decision.rejected_reasons[0]
            )
        else:
            transitions.append((current_status, RehearsalStatus.APPROVED.value, "supervisor_approved"))
            current_status = next_status(current_status, RehearsalStatus.APPROVED.value)

    # If approved, run the deterministic motion-event sequence.
    if current_status == RehearsalStatus.APPROVED.value:
        transitions.append((current_status, RehearsalStatus.REHEARSING.value, "runtime_started"))
        current_status = next_status(current_status, RehearsalStatus.REHEARSING.value)

        events.append(
            build_event(
                mission_id=plan.mission_id,
                sequence=sequence,
                event_type=RehearsalEventType.MISSION.value,
                event_subtype="rehearsal_started",
                source_phase="rehearsal_runtime",
                severity="info",
                description="mission rehearsal started",
                payload={"seed": request.seed},
            )
        )
        sequence += 1

        for waypoint in plan.waypoints:
            events.append(_waypoint_event(
                mission_id=plan.mission_id,
                sequence=sequence,
                waypoint=waypoint,
                subtype="waypoint_requested",
                description=f"waypoint {waypoint.waypoint_id} requested",
            ))
            sequence += 1
            events.append(
                build_event(
                    mission_id=plan.mission_id,
                    sequence=sequence,
                    event_type=RehearsalEventType.SAFETY.value,
                    event_subtype="safety_check_passed",
                    source_phase="rehearsal_supervisor",
                    severity="info",
                    description=f"safety check passed for {waypoint.waypoint_id}",
                    payload={"waypoint_id": waypoint.waypoint_id},
                )
            )
            sequence += 1
            events.append(_waypoint_event(
                mission_id=plan.mission_id,
                sequence=sequence,
                waypoint=waypoint,
                subtype="motion_request_simulated",
                description=f"simulated motion request for {waypoint.waypoint_id}",
            ))
            sequence += 1
            if waypoint.stage_kind in {"move", "patrol", "inspect"}:
                events.append(_waypoint_event(
                    mission_id=plan.mission_id,
                    sequence=sequence,
                    waypoint=waypoint,
                    subtype="waypoint_reached",
                    description=f"waypoint {waypoint.waypoint_id} reached (simulated)",
                ))
                sequence += 1

        transitions.append((current_status, RehearsalStatus.COMPLETED.value, "mission_completed"))
        current_status = next_status(current_status, RehearsalStatus.COMPLETED.value)
        events.append(
            build_event(
                mission_id=plan.mission_id,
                sequence=sequence,
                event_type=RehearsalEventType.MISSION.value,
                event_subtype="completed",
                source_phase="rehearsal_runtime",
                severity="info",
                description="mission rehearsal completed (simulated)",
                payload={},
            )
        )
        sequence += 1
    else:
        # Emit a single audit-trail event recording the terminal state.
        events.append(
            build_event(
                mission_id=plan.mission_id,
                sequence=sequence,
                event_type=RehearsalEventType.AUDIT.value,
                event_subtype="rehearsal_terminated_early",
                source_phase="rehearsal_runtime",
                severity="warning",
                description=f"rehearsal terminated in state {current_status}",
                payload={"failure_reason": failure_reason},
            )
        )
        sequence += 1

    safety_status = (
        RehearsalSafetyStatus.SAFE.value
        if current_status == RehearsalStatus.COMPLETED.value
        and decision.safety_status == RehearsalSafetyStatus.SAFE.value
        else (
            RehearsalSafetyStatus.GUARDED.value
            if current_status == RehearsalStatus.COMPLETED.value
            else RehearsalSafetyStatus.UNSAFE_REJECTED.value
        )
    )

    events_tuple = tuple(events)
    timeline = build_timeline(
        mission_id=plan.mission_id,
        transitions=tuple(transitions),
        events=events_tuple,
    )

    finished_at = _now_iso()
    runtime_hash = deterministic_hash(
        {
            "mission_id": plan.mission_id,
            "plan_hash": plan.deterministic_hash,
            "seed": request.seed,
            "final_status": current_status,
            "events": [e.deterministic_hash for e in events_tuple],
        }
    )

    return MissionRehearsalRuntime(
        mission_id=plan.mission_id,
        final_status=current_status,
        final_failure_reason=failure_reason,
        safety_status=safety_status,
        events=events_tuple,
        timeline=timeline,
        deterministic_hash=runtime_hash,
        started_at_utc=timestamp,
        finished_at_utc=finished_at,
    )


def _first_rejection_code(diagnostics: tuple[Mapping[str, object], ...]) -> str:
    for d in diagnostics:
        if isinstance(d, Mapping) and d.get("severity") == "rejection":
            code = d.get("code")
            if code:
                return str(code)
    return RehearsalFailureReason.MALFORMED_MISSION_GRAPH.value
