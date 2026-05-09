"""Mission orchestrator.

The orchestrator is the top of the mission runtime. Per evaluation
tick it consumes:

* the current rover pose,
* the supervisor's safety state and confidence,
* the active sensor health summary,
* the world model snapshot.

It produces:

* the new mission state (after consulting the transition table),
* an optional :class:`RequestedMotionCommand` (the only motion
  artefact the mission runtime ever produces — never an
  :class:`AuthorizedMotionCommand`),
* a :class:`WaypointProgress` for the active waypoint,
* a :class:`RecoverySnapshot` describing recovery behaviour,
* a list of structured :class:`Event` records for replay.

The orchestrator is pure-logic; it does not touch ROS or the
filesystem. The simulation engine and the ROS 2 ``mission_node`` both
embed an orchestrator and translate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from app.domain.enums import EventSeverity, LifecycleState, SafetyState, SensorType
from app.domain.events import Event, EventBuilder
from app.domain.identifiers import IdGenerator, RunId, ScenarioId
from app.domain.motion import RequestedMotionCommand
from app.domain.sensors import SensorFrame
from app.domain.time import SimulationClock
from app.mission.constraints import (
    ConstraintEvaluation,
    MissionConstraints,
    evaluate_constraints,
)
from app.mission.controller import WaypointController, WaypointSteering
from app.mission.enums import (
    MissionState,
    RecoveryBehavior,
    RecoveryDecision,
    WaypointStatus,
)
from app.mission.mission_plan import MissionPlan
from app.mission.recovery import RecoveryPolicy, RecoverySnapshot
from app.mission.transitions import (
    INVALID_MISSION_TRANSITION_REASON,
    is_mission_transition_allowed,
)
from app.mission.waypoints import Waypoint, WaypointProgress, WaypointQueue
from app.world_model.world_model import WorldModel, WorldModelInputs


_SUBSYSTEM = "mission"
_NODE = "/rover/mission_runtime"
_REQUEST_SOURCE = "mission.orchestrator"


@dataclass(frozen=True)
class OrchestratorInputs:
    """Inputs presented to the orchestrator for one tick."""

    pose_x: float
    pose_y: float
    heading_rad: float
    sensor_frame: SensorFrame
    confidence_score: float
    safety_state: SafetyState
    operator_start: bool = False
    operator_pause: bool = False
    operator_resume: bool = False
    operator_abort: bool = False
    operator_recovery: bool = False
    now_ms: int = 0
    sim_time_ns: int = 0
    command_lifetime_ms: int = 500


@dataclass
class MissionEvaluation:
    """One tick of orchestrator output."""

    mission_state: MissionState
    requested_motion: Optional[RequestedMotionCommand]
    progress: Optional[WaypointProgress]
    constraint_eval: ConstraintEvaluation
    recovery: RecoverySnapshot
    world_snapshot: object  # WorldModelSnapshot, kept loose to avoid circular import
    events: list[Event] = field(default_factory=list)


class MissionOrchestrator:
    """Top-level mission runtime."""

    def __init__(
        self,
        *,
        plan: MissionPlan,
        run_id: RunId,
        scenario_id: ScenarioId,
        clock: SimulationClock,
        id_generator: IdGenerator,
        world_model: Optional[WorldModel] = None,
        controller: Optional[WaypointController] = None,
        recovery_policy: Optional[RecoveryPolicy] = None,
    ) -> None:
        self._plan = plan
        self._clock = clock
        self._builder = EventBuilder(
            run_id=run_id,
            scenario_id=scenario_id,
            clock=clock,
            id_generator=id_generator,
            subsystem=_SUBSYSTEM,
            node=_NODE,
            lifecycle_state=LifecycleState.ACTIVE,
            safety_state=SafetyState.BOOT,
        )
        self._world = world_model or WorldModel(
            keepouts=plan.keepouts,
            restricted=plan.restricted_zones,
            boundaries=plan.boundaries,
        )
        self._controller = controller or WaypointController()
        self._recovery = recovery_policy or RecoveryPolicy(
            max_attempts=plan.max_recovery_attempts
        )
        self._queue = WaypointQueue(plan.waypoints)
        self._state = MissionState.MISSION_IDLE
        self._active_waypoint: Optional[Waypoint] = None
        self._active_started_at_ms: Optional[int] = None
        self._motion_requested = False
        self._completed_waypoints: list[Waypoint] = []
        self._timed_out_waypoints: list[Waypoint] = []
        self._aborted = False

    # ------------------------------------------------------------------
    # Read-only accessors.
    # ------------------------------------------------------------------
    @property
    def state(self) -> MissionState:
        return self._state

    @property
    def plan(self) -> MissionPlan:
        return self._plan

    @property
    def queue(self) -> WaypointQueue:
        return self._queue

    @property
    def world_model(self) -> WorldModel:
        return self._world

    @property
    def progress_fraction(self) -> float:
        return self._queue.progress_fraction()

    # ------------------------------------------------------------------
    # Per-tick evaluation.
    # ------------------------------------------------------------------
    def evaluate(self, inputs: OrchestratorInputs) -> MissionEvaluation:
        events: list[Event] = []
        self._builder.update_safety_state(inputs.safety_state)

        # 1. Update the world model with the current pose and sensor frame.
        snapshot = self._world.update(
            WorldModelInputs(
                pose_x=inputs.pose_x,
                pose_y=inputs.pose_y,
                heading_rad=inputs.heading_rad,
                sim_time_ns=inputs.sim_time_ns,
                sensor_frame=inputs.sensor_frame,
            )
        )
        # Emit world-model hazard events for new hazards. We re-emit
        # every tick (rate-limited at the recorder) so replay tools can
        # track persistence.
        for hazard in self._world.latest_hazards:
            events.append(
                self._builder.build(
                    event_type=f"world_model.{hazard.kind.value}",
                    severity=_severity_for(hazard.severity),
                    reason_code=hazard.reason_code,
                    message=hazard.summary,
                    safety_state=inputs.safety_state,
                    attributes=dict(hazard.attributes),
                )
            )

        # 2. Operator commands first.
        operator_event = self._handle_operator(inputs)
        if operator_event is not None:
            events.append(operator_event)

        # 3. Compute per-tick constraints.
        sensor_healthy_count = _count_healthy_sensors(inputs.sensor_frame)
        zone_check = self._world.latest_zone_check
        keepout_violation = bool(zone_check and zone_check.has_violation)
        keepout_pending = bool(zone_check and zone_check.is_pending())
        constraint_eval = evaluate_constraints(
            constraints=self._plan.constraints,
            confidence_score=inputs.confidence_score,
            sensor_healthy_count=sensor_healthy_count,
            zone_max_linear=zone_check.speed_limit_linear if zone_check else None,
            zone_max_angular=zone_check.speed_limit_angular if zone_check else None,
            forward_clearance_m=snapshot.forward_clearance_m if snapshot.occupancy_min_range_m > 0 else None,
            inside_keepout=keepout_violation,
            operator_paused=self._state == MissionState.MISSION_PAUSED,
            safety_state_inhibits_motion=_safety_state_inhibits(inputs.safety_state),
        )

        # 4. Recovery policy.
        sensor_health_degraded = (
            sensor_healthy_count < self._plan.constraints.minimum_sensor_health
        )
        active_wp = self._active_waypoint
        wp_timed_out = self._waypoint_timed_out(inputs.now_ms, active_wp)
        recovery = self._recovery.evaluate(
            active_waypoint_id=active_wp.waypoint_id if active_wp else None,
            active_waypoint_timed_out=wp_timed_out,
            keepout_violation=keepout_violation,
            keepout_pending=keepout_pending,
            sensor_health_degraded=sensor_health_degraded,
            operator_recovery_request=inputs.operator_recovery,
            safety_state_inhibits_motion=_safety_state_inhibits(inputs.safety_state),
            now_ms=inputs.now_ms,
        )
        if recovery.decision in {
            RecoveryDecision.ENGAGE,
            RecoveryDecision.ESCALATE,
        } and recovery.active_behavior is not None:
            events.append(
                self._builder.build(
                    event_type="mission_recovery.engaged",
                    severity=EventSeverity.WARNING
                    if recovery.decision == RecoveryDecision.ENGAGE
                    else EventSeverity.ERROR,
                    reason_code=recovery.reason_code,
                    message=recovery.summary,
                    safety_state=inputs.safety_state,
                    attributes={
                        "recovery_behavior": recovery.active_behavior.value,
                        "waypoint_id": recovery.waypoint_id,
                        "attempt_count": recovery.attempt_count,
                    },
                )
            )
        elif recovery.decision == RecoveryDecision.CLEAR:
            # When a backup-and-retry clears, give the (still-active)
            # waypoint a fresh timer so a subsequent timeout can
            # increment the attempt counter rather than firing on the
            # next tick.
            self._active_started_at_ms = inputs.now_ms
            events.append(
                self._builder.build(
                    event_type="mission_recovery.cleared",
                    severity=EventSeverity.INFO,
                    reason_code=recovery.reason_code,
                    message=recovery.summary,
                    safety_state=inputs.safety_state,
                    attributes={"waypoint_id": recovery.waypoint_id},
                )
            )

        # 5. Determine the next mission state.
        next_state, transition_event = self._determine_next_state(
            inputs=inputs,
            recovery=recovery,
            constraint_eval=constraint_eval,
            wp_timed_out=wp_timed_out,
        )
        if transition_event is not None:
            events.append(transition_event)

        # 6. Generate a requested motion if appropriate.
        motion: Optional[RequestedMotionCommand] = None
        progress: Optional[WaypointProgress] = None
        if self._state == MissionState.MISSION_ACTIVE:
            motion, progress, completion_events = self._drive_active_waypoint(
                inputs=inputs,
                constraint_eval=constraint_eval,
            )
            events.extend(completion_events)
        elif self._state == MissionState.MISSION_DEGRADED:
            # Degraded: we still produce a request, but at zero so the
            # supervisor's pipeline shows a healthy stream of zero
            # commands instead of going silent.
            motion = self._zero_motion(inputs)
        elif self._state == MissionState.MISSION_RECOVERY:
            # Recovery generates motion only for BACKUP_AND_RETRY.
            motion, progress, recovery_motion_events = self._drive_recovery(
                inputs=inputs,
                recovery=recovery,
                constraint_eval=constraint_eval,
            )
            events.extend(recovery_motion_events)
        # All other states (paused, aborting, complete, idle, preparing)
        # request no motion; the supervisor sees a missing request and
        # arbitrates accordingly.

        return MissionEvaluation(
            mission_state=self._state,
            requested_motion=motion,
            progress=progress,
            constraint_eval=constraint_eval,
            recovery=recovery,
            world_snapshot=snapshot,
            events=events,
        )

    # ------------------------------------------------------------------
    # Operator commands.
    # ------------------------------------------------------------------
    def _handle_operator(self, inputs: OrchestratorInputs) -> Optional[Event]:
        if inputs.operator_abort and self._state not in {
            MissionState.MISSION_ABORTED,
            MissionState.MISSION_ABORTING,
        }:
            return self._transition(
                MissionState.MISSION_ABORTING,
                reason="operator_abort",
                message="operator requested abort",
                inputs=inputs,
            )
        if inputs.operator_pause and self._state == MissionState.MISSION_ACTIVE:
            return self._transition(
                MissionState.MISSION_PAUSED,
                reason="operator_pause",
                message="operator paused mission",
                inputs=inputs,
            )
        if inputs.operator_resume and self._state == MissionState.MISSION_PAUSED:
            return self._transition(
                MissionState.MISSION_ACTIVE,
                reason="operator_resume",
                message="operator resumed mission",
                inputs=inputs,
            )
        if inputs.operator_start and self._state == MissionState.MISSION_IDLE:
            return self._transition(
                MissionState.MISSION_PREPARING,
                reason="operator_start",
                message="operator requested mission start",
                inputs=inputs,
            )
        return None

    # ------------------------------------------------------------------
    # State-transition policy.
    # ------------------------------------------------------------------
    def _determine_next_state(
        self,
        *,
        inputs: OrchestratorInputs,
        recovery: RecoverySnapshot,
        constraint_eval: ConstraintEvaluation,
        wp_timed_out: bool,
    ) -> tuple[MissionState, Optional[Event]]:
        if self._state == MissionState.MISSION_IDLE:
            return self._state, None
        if self._state == MissionState.MISSION_PREPARING:
            if inputs.safety_state.is_active and not constraint_eval.motion_inhibited:
                next_state = MissionState.MISSION_ACTIVE
                self._begin_next_waypoint(inputs.now_ms)
                return self._state, self._transition(
                    next_state,
                    reason="preparing_complete",
                    message="mission preparation complete",
                    inputs=inputs,
                )
            return self._state, None
        if self._state == MissionState.MISSION_ABORTING:
            # Always advance to ABORTED on the next tick.
            self._aborted = True
            self._queue.abort_remaining()
            return self._state, self._transition(
                MissionState.MISSION_ABORTED,
                reason="abort_completed",
                message="mission aborted",
                inputs=inputs,
            )
        if self._state in {MissionState.MISSION_ABORTED, MissionState.MISSION_COMPLETE}:
            return self._state, None
        if self._state == MissionState.MISSION_PAUSED:
            return self._state, None

        if recovery.active_behavior == RecoveryBehavior.MISSION_ABORT:
            return self._state, self._transition(
                MissionState.MISSION_ABORTING,
                reason="recovery_attempts_exceeded",
                message="recovery budget exceeded; aborting",
                inputs=inputs,
            )

        implied = self._recovery.implied_state(self._state)
        if implied != self._state:
            return self._state, self._transition(
                implied,
                reason=recovery.reason_code,
                message=recovery.summary,
                inputs=inputs,
            )

        # Recovery cleared while we were in RECOVERY/DEGRADED → resume.
        if (
            recovery.decision == RecoveryDecision.CLEAR
            and self._state in {MissionState.MISSION_RECOVERY, MissionState.MISSION_DEGRADED}
        ):
            return self._state, self._transition(
                MissionState.MISSION_ACTIVE,
                reason="recovery_cleared",
                message="recovery cleared; resuming",
                inputs=inputs,
            )

        return self._state, None

    # ------------------------------------------------------------------
    # Motion generation.
    # ------------------------------------------------------------------
    def _drive_active_waypoint(
        self,
        *,
        inputs: OrchestratorInputs,
        constraint_eval: ConstraintEvaluation,
    ) -> tuple[Optional[RequestedMotionCommand], Optional[WaypointProgress], list[Event]]:
        events: list[Event] = []
        if self._active_waypoint is None:
            self._begin_next_waypoint(inputs.now_ms)
        if self._active_waypoint is None:
            # Nothing left to do.
            event = self._transition(
                MissionState.MISSION_COMPLETE,
                reason="mission_complete",
                message="all waypoints completed",
                inputs=inputs,
            )
            if event is not None:
                events.append(event)
            return None, None, events

        wp = self._active_waypoint
        steering = self._controller.steer(
            waypoint=wp,
            pose_x=inputs.pose_x,
            pose_y=inputs.pose_y,
            heading_rad=inputs.heading_rad,
            max_linear=constraint_eval.effective_max_linear,
            max_angular=constraint_eval.effective_max_angular,
        )

        elapsed = inputs.now_ms - (self._active_started_at_ms or inputs.now_ms)
        progress = WaypointProgress(
            waypoint=wp,
            status=WaypointStatus.ACTIVE,
            started_at_ms=self._active_started_at_ms or inputs.now_ms,
            distance_to_goal_m=steering.distance_to_goal_m,
            heading_error_rad=steering.heading_error_rad,
            elapsed_ms=max(0, elapsed),
        )

        if steering.is_reached:
            popped = self._queue.pop_completed()
            if popped is not None:
                self._completed_waypoints.append(popped)
            events.append(
                self._builder.build(
                    event_type="mission_waypoint.completed",
                    severity=EventSeverity.INFO,
                    reason_code="waypoint_completed",
                    message=f"waypoint {wp.waypoint_id} completed",
                    safety_state=inputs.safety_state,
                    attributes={
                        "waypoint_id": wp.waypoint_id,
                        "elapsed_ms": progress.elapsed_ms,
                    },
                )
            )
            self._active_waypoint = None
            self._active_started_at_ms = None
            if self._queue.is_empty:
                # Transition handled in _determine_next_state on the
                # next tick; we still need a zero-motion request this
                # tick so the supervisor doesn't see a gap.
                pass
            else:
                self._begin_next_waypoint(inputs.now_ms)
            return self._zero_motion(inputs), progress.with_status(
                WaypointStatus.COMPLETED, now_ms=inputs.now_ms
            ), events

        motion = RequestedMotionCommand(
            linear_velocity=steering.linear_velocity,
            angular_velocity=steering.angular_velocity,
            source=_REQUEST_SOURCE,
            issued_at_ms=inputs.now_ms,
            expires_at_ms=inputs.now_ms + max(1, inputs.command_lifetime_ms),
        )
        return motion, progress, events

    def _drive_recovery(
        self,
        *,
        inputs: OrchestratorInputs,
        recovery: RecoverySnapshot,
        constraint_eval: ConstraintEvaluation,
    ) -> tuple[Optional[RequestedMotionCommand], Optional[WaypointProgress], list[Event]]:
        events: list[Event] = []
        if recovery.active_behavior == RecoveryBehavior.BACKUP_AND_RETRY and self._active_waypoint:
            # Drive backwards a small amount.
            backup_speed = min(
                constraint_eval.effective_max_linear,
                self._plan.constraints.max_linear_velocity * 0.5,
            )
            motion = RequestedMotionCommand(
                linear_velocity=-backup_speed,
                angular_velocity=0.0,
                source=_REQUEST_SOURCE,
                issued_at_ms=inputs.now_ms,
                expires_at_ms=inputs.now_ms + max(1, inputs.command_lifetime_ms),
            )
            progress = WaypointProgress(
                waypoint=self._active_waypoint,
                status=WaypointStatus.ACTIVE,
                started_at_ms=self._active_started_at_ms or inputs.now_ms,
                distance_to_goal_m=_distance(
                    self._active_waypoint.pose_x,
                    self._active_waypoint.pose_y,
                    inputs.pose_x,
                    inputs.pose_y,
                ),
                elapsed_ms=max(0, inputs.now_ms - (self._active_started_at_ms or inputs.now_ms)),
                notes=("backup_and_retry",),
            )
            return motion, progress, events
        # All other recovery behaviours request zero motion.
        return self._zero_motion(inputs), None, events

    def _waypoint_timed_out(self, now_ms: int, wp: Optional[Waypoint]) -> bool:
        if wp is None or self._active_started_at_ms is None:
            return False
        elapsed_s = (now_ms - self._active_started_at_ms) / 1000.0
        return elapsed_s >= wp.timeout_seconds

    def _begin_next_waypoint(self, now_ms: int) -> None:
        nxt = self._queue.peek()
        self._active_waypoint = nxt
        self._active_started_at_ms = now_ms if nxt is not None else None

    def _zero_motion(self, inputs: OrchestratorInputs) -> RequestedMotionCommand:
        return RequestedMotionCommand(
            linear_velocity=0.0,
            angular_velocity=0.0,
            source=_REQUEST_SOURCE,
            issued_at_ms=inputs.now_ms,
            expires_at_ms=inputs.now_ms + max(1, inputs.command_lifetime_ms),
        )

    def _transition(
        self,
        target: MissionState,
        *,
        reason: str,
        message: str,
        inputs: OrchestratorInputs,
    ) -> Optional[Event]:
        if target == self._state:
            return None
        if not is_mission_transition_allowed(self._state, target):
            return self._builder.build(
                event_type="mission_lifecycle.refused",
                severity=EventSeverity.ERROR,
                reason_code=INVALID_MISSION_TRANSITION_REASON,
                message=f"refused {self._state.value} -> {target.value}: {message}",
                safety_state=inputs.safety_state,
                attributes={
                    "from_state": self._state.value,
                    "to_state": target.value,
                    "underlying_reason": reason,
                },
            )
        previous = self._state
        self._state = target
        # Determine severity from semantics.
        if target == MissionState.MISSION_ABORTED:
            severity = EventSeverity.ERROR
        elif target == MissionState.MISSION_ABORTING:
            severity = EventSeverity.ERROR
        elif target == MissionState.MISSION_COMPLETE:
            severity = EventSeverity.INFO
        elif target == MissionState.MISSION_DEGRADED:
            severity = EventSeverity.WARNING
        elif target == MissionState.MISSION_RECOVERY:
            severity = EventSeverity.WARNING
        else:
            severity = EventSeverity.INFO
        return self._builder.build(
            event_type="mission_lifecycle.entered",
            severity=severity,
            reason_code=reason,
            message=f"{previous.value} -> {target.value}: {message}",
            safety_state=inputs.safety_state,
            attributes={"from_state": previous.value, "to_state": target.value},
        )


# ---------------------------------------------------------------------------
# Helpers.
# ---------------------------------------------------------------------------


def _safety_state_inhibits(state: SafetyState) -> bool:
    return state in {
        SafetyState.SAFE_STOP,
        SafetyState.E_STOP_LATCHED,
        SafetyState.RECOVERY,
        SafetyState.BOOT,
        SafetyState.INACTIVE,
    }


def _count_healthy_sensors(frame: SensorFrame) -> int:
    """Count how many of the four MVP sensors look healthy.

    "Healthy" for this purpose means: present, ``status == HEALTHY``,
    and ``confidence > 0.5``. The supervisor's freshness gate is the
    canonical detector of stale streams; this is a coarser, mission-
    facing signal.
    """

    from app.domain.enums import SensorStatus

    count = 0
    for reading in frame.all_readings():
        if reading.status == SensorStatus.HEALTHY and reading.confidence > 0.5:
            count += 1
    return count


def _distance(ax: float, ay: float, bx: float, by: float) -> float:
    import math

    return math.hypot(ax - bx, ay - by)


def _severity_for(value: str) -> EventSeverity:
    try:
        return EventSeverity(value)
    except ValueError:
        return EventSeverity.WARNING
