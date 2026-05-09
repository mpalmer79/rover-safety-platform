"""Controlled vocabularies for the mission runtime."""

from __future__ import annotations

from enum import Enum


class MissionState(str, Enum):
    """Mission lifecycle states.

    Mission states are independent of safety states. The mission
    runtime does not own ``/safety/state``; the supervisor does.
    """

    MISSION_IDLE = "MISSION_IDLE"
    MISSION_PREPARING = "MISSION_PREPARING"
    MISSION_ACTIVE = "MISSION_ACTIVE"
    MISSION_PAUSED = "MISSION_PAUSED"
    MISSION_RECOVERY = "MISSION_RECOVERY"
    MISSION_DEGRADED = "MISSION_DEGRADED"
    MISSION_ABORTING = "MISSION_ABORTING"
    MISSION_ABORTED = "MISSION_ABORTED"
    MISSION_COMPLETE = "MISSION_COMPLETE"

    @property
    def is_terminal(self) -> bool:
        return self in {MissionState.MISSION_COMPLETE, MissionState.MISSION_ABORTED}

    @property
    def is_active_motion(self) -> bool:
        return self in {MissionState.MISSION_ACTIVE, MissionState.MISSION_DEGRADED}


class RecoveryBehavior(str, Enum):
    """Recovery behaviours selected by :class:`RecoveryPolicy`.

    The orchestrator may activate exactly one recovery behaviour at a
    time. The active behaviour influences the requested motion the
    orchestrator generates each tick.
    """

    STOP_AND_REEVALUATE = "stop_and_reevaluate"
    BACKUP_AND_RETRY = "backup_and_retry"
    WAIT_FOR_SENSOR_RECOVERY = "wait_for_sensor_recovery"
    MISSION_ABORT = "mission_abort"
    SAFE_STOP_ESCALATION = "safe_stop_escalation"


class RecoveryDecision(str, Enum):
    """Outcome of evaluating the recovery policy on a single tick."""

    CONTINUE = "continue"
    ENGAGE = "engage"
    ESCALATE = "escalate"
    CLEAR = "clear"


class WaypointStatus(str, Enum):
    """Lifecycle of a single waypoint."""

    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    TIMED_OUT = "timed_out"
    ABORTED = "aborted"
