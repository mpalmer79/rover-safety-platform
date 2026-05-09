"""Mission runtime: deterministic orchestration over the safety supervisor.

The mission runtime is an orchestration layer. It produces
:class:`RequestedMotionCommand` values; it never produces
:class:`AuthorizedMotionCommand`. The supervisor's arbiter remains
the only authority over actuator-bound motion.

The runtime is broken into pure-logic pieces so the unit tests, the
deterministic engine, and the ROS 2 ``rover_mission_runtime`` package
can share a single implementation:

* :mod:`app.mission.enums` — vocabularies
  (:class:`MissionState`, :class:`RecoveryBehavior`, ...).
* :mod:`app.mission.transitions` — allowed mission state transitions.
* :mod:`app.mission.waypoints` — :class:`Waypoint`, :class:`WaypointQueue`,
  :class:`WaypointProgress`.
* :mod:`app.mission.constraints` — :class:`MissionConstraints` and the
  per-state operational envelope.
* :mod:`app.mission.mission_plan` — :class:`MissionPlan` (declarative).
* :mod:`app.mission.controller` — pure-pursuit-style waypoint controller.
* :mod:`app.mission.recovery` — :class:`RecoveryPolicy` for selecting
  and tracking recovery behaviors.
* :mod:`app.mission.orchestrator` — the runtime itself.
"""

from app.mission.constraints import (
    ConstraintEvaluation,
    MissionConstraints,
)
from app.mission.controller import WaypointController, WaypointSteering
from app.mission.enums import (
    MissionState,
    RecoveryBehavior,
    RecoveryDecision,
    WaypointStatus,
)
from app.mission.mission_plan import MissionPlan
from app.mission.orchestrator import (
    MissionEvaluation,
    MissionOrchestrator,
    OrchestratorInputs,
)
from app.mission.recovery import RecoveryPolicy, RecoverySnapshot
from app.mission.transitions import (
    ALLOWED_MISSION_TRANSITIONS,
    INVALID_MISSION_TRANSITION_REASON,
    is_mission_transition_allowed,
)
from app.mission.waypoints import (
    Waypoint,
    WaypointProgress,
    WaypointQueue,
)

__all__ = [
    "ALLOWED_MISSION_TRANSITIONS",
    "ConstraintEvaluation",
    "INVALID_MISSION_TRANSITION_REASON",
    "MissionConstraints",
    "MissionEvaluation",
    "MissionOrchestrator",
    "MissionPlan",
    "MissionState",
    "OrchestratorInputs",
    "RecoveryBehavior",
    "RecoveryDecision",
    "RecoveryPolicy",
    "RecoverySnapshot",
    "Waypoint",
    "WaypointController",
    "WaypointProgress",
    "WaypointQueue",
    "WaypointStatus",
    "WaypointSteering",
    "is_mission_transition_allowed",
]
