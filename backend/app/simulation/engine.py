"""Deterministic simulation engine.

The engine wires together the manual clock, the vehicle model, the
sensor simulator, the fault injector, the safety supervisor, and the
run recorder. It is the single place that drives the system one
``time_step_ms`` at a time.

Determinism is preserved by:

* a manual clock (no wall-clock reads),
* injectable identifier and clock instances,
* explicit, ordered evaluation of subsystems each tick.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from app.domain.enums import EventSeverity, LifecycleState, ReplayStatus, SafetyState
from app.domain.events import Event, EventBuilder
from app.domain.identifiers import IdGenerator, RunId, ScenarioId, UuidIdGenerator
from app.domain.motion import (
    AuthorizedMotionCommand,
    RequestedMotionCommand,
)
from app.domain.replay import RunMetadata
from app.domain.rover_state import RoverState
from app.domain.scenarios import ScenarioDefinition
from app.domain.time import ManualClock
from app.faults.injector import FaultInjector
from app.mission.mission_plan import MissionPlan
from app.mission.orchestrator import MissionOrchestrator, OrchestratorInputs
from app.safety.supervisor import SafetySupervisor, SupervisorInputs
from app.simulation.sensor_simulator import SensorSimulator
from app.simulation.vehicle_model import DifferentialDriveModel
from app.telemetry.event_bus import EventBus
from app.telemetry.event_store import EventStore
from app.telemetry.run_recorder import RunRecorder


_DEFAULT_RECORDED_TOPICS: tuple[str, ...] = (
    "/scan",
    "/odom",
    "/imu",
    "/tf",
    "/tf_static",
    "/cmd_vel_requested",
    "/cmd_vel_authorized",
    "/safety/state",
    "/safety/events",
    "/faults/injected",
    "/mission/status",
)


@dataclass(slots=True)
class SimulationResult:
    run_id: RunId
    scenario_id: ScenarioId
    final_state: RoverState
    final_safety_state: SafetyState
    duration_ms: int
    transitions: int
    fired_faults: tuple[str, ...]
    event_count: int
    run_dir: Path
    summary_path: Path


@dataclass(slots=True)
class _MissionLayer:
    """Tiny mission stub that produces a constant motion request.

    The Phase 1A engine does not yet host BehaviorTree.CPP. Scenarios
    declare what the mission would request, and this stub republishes
    that request via the supervisor. The mission is, by construction,
    incapable of writing authorized motion: it returns a
    :class:`RequestedMotionCommand`, and only the supervisor produces
    :class:`AuthorizedMotionCommand`.
    """

    scenario: ScenarioDefinition
    builder: EventBuilder

    def request(self, *, now_ms: int) -> Optional[RequestedMotionCommand]:
        plan = self.scenario.requested_motion
        if now_ms < plan.starts_at_ms:
            return None
        if plan.ends_at_ms is not None and now_ms >= plan.ends_at_ms:
            return None
        return RequestedMotionCommand(
            linear_velocity=plan.linear_velocity,
            angular_velocity=plan.angular_velocity,
            source="mission.scenario_runner",
            issued_at_ms=now_ms,
            expires_at_ms=now_ms + plan.command_lifetime_ms,
        )


@dataclass(slots=True)
class _GatewayLayer:
    """Hardware gateway stub.

    The gateway in Phase 1A only consumes :class:`AuthorizedMotionCommand`
    values produced by the supervisor. It updates the rover via the
    vehicle model. It explicitly does **not** subscribe to the mission
    layer's requested motion: that subscription does not exist.
    """

    vehicle: DifferentialDriveModel
    builder: EventBuilder

    last_authorized_at_ms: int = -1
    command_timeout_ms: int = 750

    def apply(
        self,
        *,
        state: RoverState,
        authorized: AuthorizedMotionCommand,
        dt_ms: int,
        now_ms: int,
        slip_factor: float,
    ) -> tuple[RoverState, list[Event]]:
        events: list[Event] = []
        if (now_ms - self.last_authorized_at_ms) > self.command_timeout_ms and self.last_authorized_at_ms >= 0:
            # Independent gateway timeout - also forces zero motion in the
            # vehicle model and emits an event.
            events.append(
                self.builder.build(
                    event_type="motion_arbitration.zeroed",
                    severity=EventSeverity.WARNING,
                    reason_code="command_timeout",
                    message="gateway zeroed actuator due to authorized-command silence",
                    safety_state=authorized.safety_state,
                )
            )
            zeroed = state.with_updates(
                linear_velocity=0.0,
                angular_velocity=0.0,
                last_update_ms=now_ms,
            )
            return zeroed, events
        self.last_authorized_at_ms = now_ms
        new_state = self.vehicle.step(
            state=state,
            authorized=authorized,
            dt_ms=dt_ms,
            now_ms=now_ms,
            slip_factor=slip_factor,
        )
        return new_state, events


class SimulationEngine:
    """Deterministic engine for one scenario run."""

    def __init__(
        self,
        *,
        scenario: ScenarioDefinition,
        runs_root: str | Path,
        run_id: Optional[RunId] = None,
        clock: Optional[ManualClock] = None,
        id_generator: Optional[IdGenerator] = None,
        wheel_radius_m: float = 0.05,
        wheel_separation_m: float = 0.30,
        contact_assertions: tuple[int, ...] = (),
    ) -> None:
        self._scenario = scenario
        self._clock = clock if clock is not None else ManualClock()
        self._ids = id_generator if id_generator is not None else UuidIdGenerator()
        self._run_id = run_id if run_id is not None else self._ids.run_id()
        self._scenario_id = scenario.scenario_id
        self._bus = EventBus()
        self._store = EventStore()
        self._bus.subscribe(self._store.append)

        self._supervisor = SafetySupervisor(
            run_id=self._run_id,
            scenario_id=self._scenario_id,
            clock=self._clock,
            id_generator=self._ids,
        )
        self._injector = FaultInjector(
            run_id=self._run_id,
            scenario_id=self._scenario_id,
            clock=self._clock,
            id_generator=self._ids,
            profiles=scenario.fault_profiles(),
            scenario_duration_ms=scenario.duration_ms,
        )

        self._vehicle = DifferentialDriveModel(
            wheel_radius_m=wheel_radius_m,
            wheel_separation_m=wheel_separation_m,
        )
        self._sensor_sim = SensorSimulator()
        self._mission_builder = EventBuilder(
            run_id=self._run_id,
            scenario_id=self._scenario_id,
            clock=self._clock,
            id_generator=self._ids,
            subsystem="mission",
            node="/rover/mission_runtime",
        )
        self._gateway_builder = EventBuilder(
            run_id=self._run_id,
            scenario_id=self._scenario_id,
            clock=self._clock,
            id_generator=self._ids,
            subsystem="hardware_gateway",
            node="/rover/hw_gateway",
        )
        self._mission = _MissionLayer(scenario=scenario, builder=self._mission_builder)
        self._gateway = _GatewayLayer(vehicle=self._vehicle, builder=self._gateway_builder)

        # Optional Phase-2 mission orchestrator. When the scenario
        # carries a ``mission_plan`` dict, the orchestrator owns motion
        # requests for the rest of the run. The static
        # ``RequestedMotionPlan`` ("just drive forward") fallback is
        # used when no mission plan is present.
        self._mission_orchestrator: Optional[MissionOrchestrator] = None
        self._mission_confidence: float = 1.0
        if scenario.mission_plan is not None:
            plan = MissionPlan.from_dict(scenario.mission_plan)
            self._mission_orchestrator = MissionOrchestrator(
                plan=plan,
                run_id=self._run_id,
                scenario_id=self._scenario_id,
                clock=self._clock,
                id_generator=self._ids,
            )

        ts = self._clock.stamp()
        metadata = RunMetadata(
            run_id=self._run_id,
            scenario_id=self._scenario_id,
            started_wall=ts.wall,
            started_sim_ns=ts.sim_time_ns,
            recorded_topics=_DEFAULT_RECORDED_TOPICS,
            armed_faults=tuple(p.fault_id for p in scenario.fault_profiles()),
        )
        self._recorder = RunRecorder(
            runs_root=runs_root,
            run_id=self._run_id,
            scenario_id=self._scenario_id,
            metadata=metadata,
        )
        self._bus.subscribe(self._recorder.append_event)

        self._state = RoverState.initial(
            pose_x=scenario.initial_state.pose_x,
            pose_y=scenario.initial_state.pose_y,
            heading_rad=scenario.initial_state.heading_rad,
        )
        self._contact_assertions = set(int(t) for t in contact_assertions)

        # Emit boot and arming events.
        self._publish(self._supervisor.emit_boot_event())
        for evt in self._injector.emit_arming():
            self._publish(evt)
        self._publish(
            self._mission_builder.build(
                event_type="system_lifecycle.node_activated",
                severity=EventSeverity.INFO,
                reason_code="scenario_loaded",
                message=f"scenario loaded: {self._scenario_id}",
                lifecycle_state=LifecycleState.ACTIVE,
            )
        )

    # ------------------------------------------------------------------
    # Public properties.
    # ------------------------------------------------------------------
    @property
    def run_id(self) -> RunId:
        return self._run_id

    @property
    def scenario_id(self) -> ScenarioId:
        return self._scenario_id

    @property
    def supervisor(self) -> SafetySupervisor:
        return self._supervisor

    @property
    def event_store(self) -> EventStore:
        return self._store

    @property
    def state(self) -> RoverState:
        return self._state

    @property
    def recorder(self) -> RunRecorder:
        return self._recorder

    @property
    def event_bus(self) -> EventBus:
        return self._bus

    # ------------------------------------------------------------------
    # Single-step API for tests and interactive use.
    # ------------------------------------------------------------------
    def step(self) -> SafetyState:
        """Advance the simulation by one tick and return the new state."""

        now_ms = self._clock.now_ms()
        # 1. Fault injection updates lifecycle, returns effect.
        injection = self._injector.evaluate(now_ms=now_ms)
        for evt in injection.events:
            self._publish(evt)

        # 2. Sensor simulator produces a frame (post-fault perturbation).
        # Sensor generation moves earlier in the tick because the
        # mission orchestrator (if any) consumes the same frame the
        # supervisor will see.
        contact_asserted = now_ms in self._contact_assertions
        frame = self._sensor_sim.generate(
            state=self._state,
            now_ms=now_ms,
            effect=injection.effect,
            wheel_radius_m=self._vehicle.wheel_radius_m,
            wheel_separation_m=self._vehicle.wheel_separation_m,
            contact_asserted=contact_asserted,
        )
        self._recorder.append_sensor_frame(frame, sim_time_ns=self._clock.now_ns())

        # 3. Operator inputs from scenario timeline.
        ops = self._operator_pulses(now_ms=now_ms)

        # 4. Mission requests motion.
        if self._mission_orchestrator is None:
            requested = self._mission.request(now_ms=now_ms)
            mission_evaluation = None
        else:
            mission_evaluation = self._mission_orchestrator.evaluate(
                OrchestratorInputs(
                    pose_x=self._state.pose_x,
                    pose_y=self._state.pose_y,
                    heading_rad=self._state.heading_rad,
                    sensor_frame=frame,
                    confidence_score=self._mission_confidence,
                    safety_state=self._supervisor.safety_state,
                    operator_start=ops["activate"],
                    operator_pause=False,
                    operator_resume=False,
                    operator_abort=False,
                    operator_recovery=ops["recovery"],
                    now_ms=now_ms,
                    sim_time_ns=self._clock.now_ns(),
                    command_lifetime_ms=500,
                )
            )
            for evt in mission_evaluation.events:
                self._publish(evt)
            requested = mission_evaluation.requested_motion
            self._recorder.append_world_model_snapshot(mission_evaluation.world_snapshot)
            self._recorder.append_mission_progress(
                mission_state=mission_evaluation.mission_state,
                progress=mission_evaluation.progress,
                recovery=mission_evaluation.recovery,
                sim_time_ns=self._clock.now_ns(),
            )

        # 5. Supervisor evaluation.
        supervisor_inputs = SupervisorInputs(
            frame=frame,
            requested_motion=requested,
            operator_activate=ops["activate"],
            operator_estop=ops["estop"],
            operator_recovery=ops["recovery"],
            operator_reset_armed=ops["reset_armed"],
            operator_reset=ops["reset"],
            gateway_heartbeat=not injection.effect.suppress_gateway_heartbeat,
            now_ms=now_ms,
        )
        evaluation = self._supervisor.evaluate(supervisor_inputs)
        for evt in evaluation.events:
            self._publish(evt)
        # Feed the supervisor's confidence back to the orchestrator so
        # the next tick's constraint evaluation uses the same number
        # the supervisor saw this tick.
        self._mission_confidence = float(evaluation.confidence.score)

        # 6. Gateway applies authorized command and integrates the vehicle.
        new_state, gateway_events = self._gateway.apply(
            state=self._state,
            authorized=evaluation.authorized,
            dt_ms=self._scenario.time_step_ms,
            now_ms=now_ms,
            slip_factor=injection.effect.wheel_slip_factor,
        )
        for evt in gateway_events:
            self._publish(evt)

        new_state = new_state.with_updates(
            safety_state=self._supervisor.safety_state,
            lifecycle_state=self._supervisor.lifecycle_state,
        )
        self._state = new_state
        self._recorder.append_state(new_state)
        self._recorder.append_command(
            requested=requested,
            authorized=evaluation.authorized,
            sim_time_ns=self._clock.now_ns(),
        )
        self._clock.advance_ms(self._scenario.time_step_ms)
        return self._supervisor.safety_state

    def run(self) -> SimulationResult:
        """Run the entire scenario. Returns a :class:`SimulationResult`."""

        for _ in range(self._scenario.total_steps):
            self.step()
        ts = self._clock.stamp()
        summary = self._recorder.finalize(ended_wall=ts.wall, ended_sim_ns=ts.sim_time_ns, status=ReplayStatus.FINALIZED)
        self._recorder.close()
        result = SimulationResult(
            run_id=self._run_id,
            scenario_id=self._scenario_id,
            final_state=self._state,
            final_safety_state=self._supervisor.safety_state,
            duration_ms=self._scenario.duration_ms,
            transitions=len(summary.transitions),
            fired_faults=summary.fired_faults,
            event_count=summary.event_count,
            run_dir=self._recorder.run_dir,
            summary_path=self._recorder.run_dir / "incident-summary.md",
        )
        return result

    # ------------------------------------------------------------------
    # Helpers.
    # ------------------------------------------------------------------
    def _publish(self, event: Event) -> None:
        self._bus.publish(event)

    def _operator_pulses(self, *, now_ms: int) -> dict[str, bool]:
        init = self._scenario.initial_state
        # Pulses are emitted exactly when their configured time matches
        # the current step. Engine guarantees ``now_ms`` advances by
        # ``time_step_ms`` per call.
        step = self._scenario.time_step_ms
        in_step = lambda v: v is not None and now_ms <= v < now_ms + step
        return {
            "activate": in_step(init.operator_activate_at_ms),
            "estop": in_step(init.operator_estop_at_ms),
            "recovery": in_step(init.operator_recovery_at_ms),
            "reset_armed": in_step(init.operator_reset_armed_at_ms),
            "reset": in_step(init.operator_reset_at_ms),
        }
