"""Phase 1C scenario validation suite.

Runs every required scenario through the deterministic engine and
asserts the documented outcomes. The suite is the primary acceptance
gate for "fault injection propagates correctly" and "scenario validation
suite executes correctly" in Phase 1C.

The suite is intentionally narrow: it does not try to be a property
tester. Each :class:`ScenarioCase` declares the required outcome (final
safety state, fault IDs that must have fired, transition reason codes
that must be present in the event stream). The suite asserts those and
nothing else.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from app.domain.enums import SafetyState
from app.domain.identifiers import RunId, SequentialIdGenerator
from app.domain.scenarios import ScenarioDefinition
from app.domain.time import ManualClock
from app.simulation.engine import SimulationEngine
from app.validation.replay_validator import (
    ReplayValidationResult,
    validate_run_directory,
)


SCENARIOS_DIR = Path(__file__).resolve().parents[2] / "scenarios"


@dataclass(frozen=True)
class ScenarioCase:
    """Declarative description of an expected scenario outcome."""

    scenario_file: str
    expected_final_state: SafetyState
    expected_fired_faults: tuple[str, ...] = ()
    expected_transition_reason_codes: tuple[str, ...] = ()
    expected_min_transitions: int = 1
    description: str = ""
    expected_mission_state: str | None = None
    """Phase 2 mission cases: the orchestrator's terminal state."""

    expected_min_waypoints_completed: int = 0
    expected_min_recovery_engagements: int = 0
    expected_world_model_events: tuple[str, ...] = ()
    """Phase 2: ``world_model.*`` event types that must be present."""


@dataclass
class ScenarioOutcome:
    case: ScenarioCase
    ok: bool
    final_state: SafetyState
    fired_faults: tuple[str, ...]
    transitions: int
    reason_codes: tuple[str, ...]
    replay: ReplayValidationResult
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    run_dir: Path | None = None
    final_mission_state: str | None = None
    waypoints_completed: int = 0
    recovery_engagements: int = 0
    world_model_event_types: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {
            "scenario_file": self.case.scenario_file,
            "ok": self.ok,
            "final_state": self.final_state.value,
            "fired_faults": list(self.fired_faults),
            "transitions": self.transitions,
            "reason_codes": list(self.reason_codes),
            "replay": self.replay.as_dict(),
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "run_dir": str(self.run_dir) if self.run_dir else None,
            "final_mission_state": self.final_mission_state,
            "waypoints_completed": self.waypoints_completed,
            "recovery_engagements": self.recovery_engagements,
            "world_model_event_types": list(self.world_model_event_types),
        }


@dataclass
class SuiteResult:
    outcomes: list[ScenarioOutcome] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(o.ok for o in self.outcomes)

    @property
    def failure_count(self) -> int:
        return sum(0 if o.ok else 1 for o in self.outcomes)

    def as_dict(self) -> dict:
        return {
            "ok": self.ok,
            "failure_count": self.failure_count,
            "outcomes": [o.as_dict() for o in self.outcomes],
        }


def builtin_scenarios() -> tuple[ScenarioCase, ...]:
    """Return the seven Phase 1C scenarios required by the spec."""

    return (
        ScenarioCase(
            scenario_file="nominal_run.json",
            expected_final_state=SafetyState.ACTIVE_NORMAL,
            expected_fired_faults=(),
            expected_transition_reason_codes=(
                "boot_complete",
                "operator_activate",
            ),
            description="Healthy run; supervisor reaches ACTIVE_NORMAL.",
        ),
        ScenarioCase(
            scenario_file="stale_lidar_restricted_mode.json",
            expected_final_state=SafetyState.SAFE_STOP,
            expected_fired_faults=("f-stale-lidar",),
            expected_transition_reason_codes=("operator_activate", "stale_lidar"),
            expected_min_transitions=3,
            description="LiDAR drops mid-run; ACTIVE_DEGRADED then SAFE_STOP.",
        ),
        ScenarioCase(
            scenario_file="odometry_divergence_safe_stop.json",
            expected_final_state=SafetyState.ACTIVE_DEGRADED,
            expected_fired_faults=("f-disagreement",),
            expected_transition_reason_codes=("sensor_disagreement",),
            description="Encoder/IMU angular disagreement; ACTIVE_DEGRADED.",
        ),
        ScenarioCase(
            scenario_file="command_timeout_safe_stop.json",
            expected_final_state=SafetyState.SAFE_STOP,
            expected_fired_faults=("f-cmd-timeout",),
            expected_transition_reason_codes=("gateway_silent",),
            description="Hardware gateway silent; SAFE_STOP via gateway watchdog.",
        ),
        ScenarioCase(
            scenario_file="bridge_disconnect_safe_stop.json",
            expected_final_state=SafetyState.SAFE_STOP,
            expected_fired_faults=("f-bridge",),
            description="ros_gz_bridge disconnects; multi-stream freshness violation triggers SAFE_STOP.",
        ),
        ScenarioCase(
            scenario_file="wheel_slip_degraded_mode.json",
            expected_final_state=SafetyState.ACTIVE_DEGRADED,
            expected_fired_faults=("f-imu-bias", "f-slip"),
            expected_transition_reason_codes=("imu_bias",),
            description="Rough-terrain: wheel slip + IMU bias drives ACTIVE_DEGRADED.",
        ),
        ScenarioCase(
            scenario_file="estop_latched_manual_reset_required.json",
            expected_final_state=SafetyState.E_STOP_LATCHED,
            expected_transition_reason_codes=("operator_estop",),
            description="Operator E-stop latches; cannot self-clear.",
        ),
        # Phase 2 mission scenarios.
        ScenarioCase(
            scenario_file="nominal_waypoint_patrol.json",
            expected_final_state=SafetyState.ACTIVE_NORMAL,
            expected_mission_state="MISSION_COMPLETE",
            expected_min_waypoints_completed=3,
            description="Three-waypoint patrol; mission completes cleanly.",
        ),
        ScenarioCase(
            scenario_file="waypoint_timeout_recovery.json",
            expected_final_state=SafetyState.ACTIVE_NORMAL,
            expected_mission_state="MISSION_ABORTED",
            expected_min_recovery_engagements=2,
            description=(
                "Unreachable waypoint with budget=2; expect MISSION_ABORTED "
                "after BACKUP_AND_RETRY exhaustion."
            ),
        ),
        ScenarioCase(
            scenario_file="degraded_sensor_navigation.json",
            expected_final_state=SafetyState.ACTIVE_DEGRADED,
            expected_fired_faults=("f-imu-bias",),
            expected_mission_state="MISSION_COMPLETE",
            expected_min_waypoints_completed=1,
            description="Mission completes despite ACTIVE_DEGRADED supervisor state.",
        ),
        ScenarioCase(
            scenario_file="keepout_zone_violation.json",
            expected_final_state=SafetyState.ACTIVE_NORMAL,
            expected_mission_state="MISSION_DEGRADED",
            expected_world_model_events=(
                "world_model.keepout_pending",
                "world_model.keepout_violation",
            ),
            description=(
                "Rover crosses into a keepout zone; mission orchestrator "
                "escalates via SAFE_STOP_ESCALATION."
            ),
        ),
        ScenarioCase(
            scenario_file="restricted_mode_navigation.json",
            expected_final_state=SafetyState.ACTIVE_NORMAL,
            expected_mission_state="MISSION_COMPLETE",
            expected_min_waypoints_completed=1,
            expected_world_model_events=("world_model.restricted_speed_violation",),
            description=(
                "Rover passes through a restricted-speed zone; mission completes."
            ),
        ),
        ScenarioCase(
            scenario_file="safe_stop_during_active_mission.json",
            expected_final_state=SafetyState.SAFE_STOP,
            expected_fired_faults=("f-stale-lidar",),
            expected_mission_state="MISSION_DEGRADED",
            description=(
                "Mid-mission LiDAR drop; supervisor SAFE_STOP and orchestrator "
                "MISSION_DEGRADED."
            ),
        ),
        ScenarioCase(
            scenario_file="mission_abort_after_fault_escalation.json",
            expected_final_state=SafetyState.ACTIVE_NORMAL,
            expected_mission_state="MISSION_ABORTED",
            expected_min_recovery_engagements=3,
            description="Repeated waypoint timeouts; mission aborts after exhausting budget.",
        ),
    )


def run_scenario_suite(
    *,
    runs_root: Path | str,
    cases: Iterable[ScenarioCase] | None = None,
    scenarios_dir: Path | str | None = None,
    clean: bool = True,
) -> SuiteResult:
    """Run the suite and validate every outcome.

    Each scenario writes to ``<runs_root>/<scenario_id>/`` so that
    re-running the suite is reproducible.
    """

    cases = tuple(cases or builtin_scenarios())
    scenarios_dir = Path(scenarios_dir or SCENARIOS_DIR)
    runs_root = Path(runs_root)
    if clean and runs_root.exists():
        shutil.rmtree(runs_root)
    runs_root.mkdir(parents=True, exist_ok=True)

    suite = SuiteResult()
    for case in cases:
        outcome = _run_one(case=case, runs_root=runs_root, scenarios_dir=scenarios_dir)
        suite.outcomes.append(outcome)
    return suite


def _run_one(
    *,
    case: ScenarioCase,
    runs_root: Path,
    scenarios_dir: Path,
) -> ScenarioOutcome:
    scenario_path = scenarios_dir / case.scenario_file
    scenario = ScenarioDefinition.from_json_file(scenario_path)
    run_id = RunId(f"suite-{scenario.scenario_id}")
    engine = SimulationEngine(
        scenario=scenario,
        runs_root=runs_root,
        run_id=run_id,
        clock=ManualClock(),
        id_generator=SequentialIdGenerator(),
    )
    engine.run()

    final_state = engine.supervisor.safety_state
    fired_faults = tuple(
        sorted(
            event.attributes.get("fault_id")
            for event in engine.event_store.all()
            if event.event_type == "fault_injection.fired"
            and isinstance(event.attributes.get("fault_id"), str)
        )
    )
    reason_codes = tuple(
        event.reason_code
        for event in engine.event_store.transitions()
    )
    transitions = len(reason_codes)

    replay = validate_run_directory(engine.recorder.run_dir)
    errors: list[str] = []
    warnings: list[str] = []

    if final_state != case.expected_final_state:
        errors.append(
            f"final state {final_state.value} != expected {case.expected_final_state.value}"
        )
    if set(case.expected_fired_faults) - set(fired_faults):
        errors.append(
            "expected fired faults not present: "
            + ", ".join(sorted(set(case.expected_fired_faults) - set(fired_faults)))
        )
    if transitions < case.expected_min_transitions:
        errors.append(
            f"expected at least {case.expected_min_transitions} transitions; got {transitions}"
        )
    for required_reason in case.expected_transition_reason_codes:
        if required_reason not in reason_codes:
            errors.append(
                f"expected transition reason {required_reason!r} not present"
            )
    if not replay.ok:
        errors.append(f"replay validation failed: {replay.errors}")

    # Phase 2 mission assertions.
    final_mission_state: str | None = None
    waypoints_completed = 0
    recovery_engagements = 0
    world_model_event_types: tuple[str, ...] = ()
    if engine._mission_orchestrator is not None:
        final_mission_state = engine._mission_orchestrator.state.value
        waypoints_completed = engine._mission_orchestrator.queue.completed_count
        recovery_engagements = sum(
            1
            for event in engine.event_store.all()
            if event.event_type == "mission_recovery.engaged"
        )
        world_model_event_types = tuple(
            sorted(
                {
                    event.event_type
                    for event in engine.event_store.all()
                    if event.event_type.startswith("world_model.")
                }
            )
        )

        if (
            case.expected_mission_state is not None
            and final_mission_state != case.expected_mission_state
        ):
            errors.append(
                f"final mission state {final_mission_state} != "
                f"expected {case.expected_mission_state}"
            )
        if waypoints_completed < case.expected_min_waypoints_completed:
            errors.append(
                f"completed waypoints {waypoints_completed} < "
                f"expected min {case.expected_min_waypoints_completed}"
            )
        if recovery_engagements < case.expected_min_recovery_engagements:
            errors.append(
                f"recovery engagements {recovery_engagements} < "
                f"expected min {case.expected_min_recovery_engagements}"
            )
        for required_event_type in case.expected_world_model_events:
            if required_event_type not in world_model_event_types:
                errors.append(
                    f"expected world_model event type {required_event_type!r} not present"
                )
    elif (
        case.expected_mission_state is not None
        or case.expected_min_waypoints_completed > 0
    ):
        errors.append("scenario expected a mission but none was loaded")

    ok = not errors
    return ScenarioOutcome(
        case=case,
        ok=ok,
        final_state=final_state,
        fired_faults=fired_faults,
        transitions=transitions,
        reason_codes=reason_codes,
        replay=replay,
        errors=errors,
        warnings=warnings,
        run_dir=engine.recorder.run_dir,
        final_mission_state=final_mission_state,
        waypoints_completed=waypoints_completed,
        recovery_engagements=recovery_engagements,
        world_model_event_types=world_model_event_types,
    )
