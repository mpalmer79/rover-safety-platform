"""Allowed mission state transitions.

The transition table is the contract between the mission orchestrator
and any external observer (operator, dashboards, replay tooling). The
table is authoritative; the orchestrator must consult
:func:`is_mission_transition_allowed` and emit a
``mission_lifecycle.refused`` event for any disallowed transition
rather than silently changing state.
"""

from __future__ import annotations

from app.mission.enums import MissionState


# Mapping: from -> set of allowed-to states.
ALLOWED_MISSION_TRANSITIONS: dict[MissionState, frozenset[MissionState]] = {
    MissionState.MISSION_IDLE: frozenset(
        {
            MissionState.MISSION_PREPARING,
            MissionState.MISSION_ABORTED,
        }
    ),
    MissionState.MISSION_PREPARING: frozenset(
        {
            MissionState.MISSION_ACTIVE,
            MissionState.MISSION_PAUSED,
            MissionState.MISSION_ABORTING,
            MissionState.MISSION_ABORTED,
        }
    ),
    MissionState.MISSION_ACTIVE: frozenset(
        {
            MissionState.MISSION_PAUSED,
            MissionState.MISSION_RECOVERY,
            MissionState.MISSION_DEGRADED,
            MissionState.MISSION_ABORTING,
            MissionState.MISSION_COMPLETE,
        }
    ),
    MissionState.MISSION_PAUSED: frozenset(
        {
            MissionState.MISSION_ACTIVE,
            MissionState.MISSION_RECOVERY,
            MissionState.MISSION_ABORTING,
        }
    ),
    MissionState.MISSION_RECOVERY: frozenset(
        {
            MissionState.MISSION_ACTIVE,
            MissionState.MISSION_DEGRADED,
            MissionState.MISSION_ABORTING,
        }
    ),
    MissionState.MISSION_DEGRADED: frozenset(
        {
            MissionState.MISSION_ACTIVE,
            MissionState.MISSION_RECOVERY,
            MissionState.MISSION_ABORTING,
        }
    ),
    MissionState.MISSION_ABORTING: frozenset({MissionState.MISSION_ABORTED}),
    MissionState.MISSION_ABORTED: frozenset(),
    MissionState.MISSION_COMPLETE: frozenset(),
}


INVALID_MISSION_TRANSITION_REASON = "invalid_mission_transition"


def is_mission_transition_allowed(
    from_state: MissionState, to_state: MissionState
) -> bool:
    """Return True if ``from_state -> to_state`` is permitted.

    A self-transition is always allowed (it is a no-op).
    """

    if from_state == to_state:
        return True
    return to_state in ALLOWED_MISSION_TRANSITIONS.get(from_state, frozenset())
