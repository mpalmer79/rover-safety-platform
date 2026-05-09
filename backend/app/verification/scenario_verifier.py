"""Scenario verifier.

For each scenario covered by Phase 1C and Phase 2, declare a stable
:class:`ScenarioExpectation` listing:

* the requirement IDs that the scenario exercises,
* the expected final safety state (always known),
* the expected mission state (Phase 2 only),
* event types that *must* be present,
* event types that *must not* be present (the forbidden list),
* recovery expectations,
* world-model expectations.

Verifying a scenario means: run it via the deterministic engine,
produce its run directory, then run the command audit, the
safety-transition audit, and the replay-integrity verifier against
the artefacts. The combined :class:`ScenarioVerification` carries
``passed`` / ``failed`` / ``partial`` / ``skipped`` /
``not_executed`` plus the per-check breakdown.

When a scenario cannot be executed in the current environment, the
verifier returns ``not_executed`` with a reason. Reports must surface
those reasons honestly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from app.domain.enums import SafetyState
from app.domain.identifiers import RunId, SequentialIdGenerator
from app.domain.scenarios import ScenarioDefinition
from app.domain.time import ManualClock
from app.simulation.engine import SimulationEngine
from app.verification.acceptance import AcceptanceStatus, aggregate_status
from app.verification.command_audit import CommandAuditResult, audit_command_path
from app.verification.replay_integrity import (
    ReplayIntegrityResult,
    verify_replay_integrity,
)
from app.verification.safety_audit import (
    SafetyTransitionAuditResult,
    audit_safety_transitions,
)


SCENARIOS_DIR = Path(__file__).resolve().parents[2] / "scenarios"


@dataclass(frozen=True)
class ScenarioExpectation:
    scenario_file: str
    requirement_ids: tuple[str, ...]
    expected_safety_state: SafetyState
    expected_mission_state: str | None = None
    required_event_types: tuple[str, ...] = ()
    forbidden_event_types: tuple[str, ...] = ()
    expected_fired_faults: tuple[str, ...] = ()
    min_recovery_engagements: int = 0
    expected_safe_stop_zero_motion: bool = False
    description: str = ""

    @property
    def scenario_id(self) -> str:
        return self.scenario_file.removesuffix(".json")


@dataclass
class ScenarioCheck:
    name: str
    status: AcceptanceStatus
    detail: str = ""
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status.value,
            "detail": self.detail,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


@dataclass
class ScenarioVerification:
    expectation: ScenarioExpectation
    status: AcceptanceStatus
    run_dir: Path | None
    final_safety_state: SafetyState | None
    final_mission_state: str | None
    fired_faults: tuple[str, ...]
    recovery_engagement_count: int
    checks: list[ScenarioCheck] = field(default_factory=list)
    not_executed_reason: str = ""

    @property
    def ok(self) -> bool:
        return self.status == AcceptanceStatus.PASSED

    def as_dict(self) -> dict:
        return {
            "scenario_file": self.expectation.scenario_file,
            "scenario_id": self.expectation.scenario_id,
            "requirement_ids": list(self.expectation.requirement_ids),
            "expected_safety_state": self.expectation.expected_safety_state.value,
            "expected_mission_state": self.expectation.expected_mission_state,
            "status": self.status.value,
            "ok": self.ok,
            "run_dir": str(self.run_dir) if self.run_dir else None,
            "final_safety_state": (
                self.final_safety_state.value if self.final_safety_state else None
            ),
            "final_mission_state": self.final_mission_state,
            "fired_faults": list(self.fired_faults),
            "recovery_engagement_count": self.recovery_engagement_count,
            "checks": [c.as_dict() for c in self.checks],
            "not_executed_reason": self.not_executed_reason,
        }


# ---------------------------------------------------------------------------
# Per-scenario expectations.
#
# Adding a scenario:
# 1. Confirm its JSON file exists in backend/scenarios/.
# 2. Add an entry below citing the relevant REQ-* IDs.
# 3. The verifier asserts the expected safety / mission state, the
#    required event types, and the forbidden event types.
# ---------------------------------------------------------------------------


SCENARIO_EXPECTATIONS: tuple[ScenarioExpectation, ...] = (
    ScenarioExpectation(
        scenario_file="nominal_run.json",
        requirement_ids=("REQ-SAFE-001", "REQ-REPLAY-001"),
        expected_safety_state=SafetyState.ACTIVE_NORMAL,
        required_event_types=("safety_transition.entered", "system_lifecycle.boot"),
        forbidden_event_types=("safety_transition.refused",),
        description="Healthy nominal run; supervisor reaches ACTIVE_NORMAL.",
    ),
    ScenarioExpectation(
        scenario_file="stale_lidar_restricted_mode.json",
        requirement_ids=("REQ-SAFE-001", "REQ-SAFE-002", "REQ-FAULT-001", "REQ-FAULT-002"),
        expected_safety_state=SafetyState.SAFE_STOP,
        required_event_types=(
            "fault_injection.fired",
            "sensor_health.stale",
            "safety_transition.entered",
        ),
        forbidden_event_types=(),
        expected_fired_faults=("f-stale-lidar",),
        expected_safe_stop_zero_motion=True,
        description="LiDAR drop forces SAFE_STOP through freshness gates.",
    ),
    ScenarioExpectation(
        scenario_file="odometry_divergence_safe_stop.json",
        requirement_ids=("REQ-SAFE-001", "REQ-FAULT-001", "REQ-FAULT-002"),
        expected_safety_state=SafetyState.ACTIVE_DEGRADED,
        required_event_types=("fault_injection.fired", "safety_transition.entered"),
        expected_fired_faults=("f-disagreement",),
        description="Encoder/IMU disagreement; ACTIVE_DEGRADED.",
    ),
    ScenarioExpectation(
        scenario_file="command_timeout_safe_stop.json",
        requirement_ids=("REQ-SAFE-001", "REQ-SAFE-002", "REQ-FAULT-001", "REQ-FAULT-002"),
        expected_safety_state=SafetyState.SAFE_STOP,
        required_event_types=(
            "fault_injection.fired",
            "watchdog.expired",
            "safety_transition.entered",
        ),
        expected_fired_faults=("f-cmd-timeout",),
        expected_safe_stop_zero_motion=True,
        description="Hardware gateway silent; SAFE_STOP via gateway watchdog.",
    ),
    ScenarioExpectation(
        scenario_file="bridge_disconnect_safe_stop.json",
        requirement_ids=("REQ-SAFE-001", "REQ-SAFE-002", "REQ-FAULT-001", "REQ-FAULT-002"),
        expected_safety_state=SafetyState.SAFE_STOP,
        required_event_types=("fault_injection.fired", "safety_transition.entered"),
        expected_fired_faults=("f-bridge",),
        expected_safe_stop_zero_motion=True,
        description="Bridge disconnect; multi-stream freshness violation.",
    ),
    ScenarioExpectation(
        scenario_file="wheel_slip_degraded_mode.json",
        requirement_ids=("REQ-SAFE-001", "REQ-FAULT-001", "REQ-FAULT-002"),
        expected_safety_state=SafetyState.ACTIVE_DEGRADED,
        required_event_types=("fault_injection.fired", "safety_transition.entered"),
        expected_fired_faults=("f-imu-bias", "f-slip"),
        description="Rough-terrain slip + IMU bias; ACTIVE_DEGRADED.",
    ),
    ScenarioExpectation(
        scenario_file="estop_latched_manual_reset_required.json",
        requirement_ids=("REQ-SAFE-003", "REQ-OP-001"),
        expected_safety_state=SafetyState.E_STOP_LATCHED,
        required_event_types=("safety_transition.entered",),
        expected_safe_stop_zero_motion=True,
        description="Operator E-stop latches and does not self-clear.",
    ),
    # Phase 2 mission scenarios.
    ScenarioExpectation(
        scenario_file="nominal_waypoint_patrol.json",
        requirement_ids=("REQ-SAFE-001", "REQ-MISSION-001", "REQ-REPLAY-001"),
        expected_safety_state=SafetyState.ACTIVE_NORMAL,
        expected_mission_state="MISSION_COMPLETE",
        required_event_types=(
            "mission_lifecycle.entered",
            "mission_waypoint.completed",
        ),
        forbidden_event_types=("mission_lifecycle.refused",),
        description="Three-waypoint patrol; mission completes cleanly.",
    ),
    ScenarioExpectation(
        scenario_file="waypoint_timeout_recovery.json",
        requirement_ids=("REQ-MISSION-001", "REQ-MISSION-002"),
        expected_safety_state=SafetyState.ACTIVE_NORMAL,
        expected_mission_state="MISSION_ABORTED",
        required_event_types=(
            "mission_recovery.engaged",
            "mission_lifecycle.entered",
        ),
        min_recovery_engagements=2,
        description="Unreachable waypoint; recovery exhausts budget; MISSION_ABORTED.",
    ),
    ScenarioExpectation(
        scenario_file="degraded_sensor_navigation.json",
        requirement_ids=("REQ-MISSION-001", "REQ-FAULT-001"),
        expected_safety_state=SafetyState.ACTIVE_DEGRADED,
        expected_mission_state="MISSION_COMPLETE",
        required_event_types=("fault_injection.fired", "mission_lifecycle.entered"),
        expected_fired_faults=("f-imu-bias",),
        description="Mission completes despite ACTIVE_DEGRADED supervisor state.",
    ),
    ScenarioExpectation(
        scenario_file="keepout_zone_violation.json",
        requirement_ids=("REQ-MISSION-001", "REQ-WORLD-001"),
        expected_safety_state=SafetyState.ACTIVE_NORMAL,
        expected_mission_state="MISSION_DEGRADED",
        required_event_types=(
            "world_model.keepout_pending",
            "world_model.keepout_violation",
            "mission_recovery.engaged",
        ),
        description="Keepout violation triggers SAFE_STOP_ESCALATION recovery.",
    ),
    ScenarioExpectation(
        scenario_file="restricted_mode_navigation.json",
        requirement_ids=("REQ-SAFE-004", "REQ-MISSION-001", "REQ-WORLD-001"),
        expected_safety_state=SafetyState.ACTIVE_NORMAL,
        expected_mission_state="MISSION_COMPLETE",
        required_event_types=("world_model.restricted_speed_violation",),
        description="Mission passes through a restricted-speed zone; clamped, completes.",
    ),
    ScenarioExpectation(
        scenario_file="safe_stop_during_active_mission.json",
        requirement_ids=("REQ-SAFE-002", "REQ-MISSION-001", "REQ-FAULT-001"),
        expected_safety_state=SafetyState.SAFE_STOP,
        expected_mission_state="MISSION_DEGRADED",
        required_event_types=(
            "fault_injection.fired",
            "safety_transition.entered",
            "mission_lifecycle.entered",
        ),
        expected_fired_faults=("f-stale-lidar",),
        expected_safe_stop_zero_motion=True,
        description="Mid-mission LiDAR drop drives SAFE_STOP + MISSION_DEGRADED.",
    ),
    ScenarioExpectation(
        scenario_file="mission_abort_after_fault_escalation.json",
        requirement_ids=("REQ-MISSION-002",),
        expected_safety_state=SafetyState.ACTIVE_NORMAL,
        expected_mission_state="MISSION_ABORTED",
        required_event_types=(
            "mission_recovery.engaged",
            "mission_lifecycle.entered",
        ),
        min_recovery_engagements=3,
        description="Repeated waypoint timeouts; mission aborts after exhausting budget.",
    ),
)


# ---------------------------------------------------------------------------
# Verifier.
# ---------------------------------------------------------------------------


def verify_scenario(
    expectation: ScenarioExpectation,
    *,
    runs_root: Path | str,
    scenarios_dir: Path | str | None = None,
    skip_reason: Optional[str] = None,
) -> ScenarioVerification:
    """Run the scenario through the deterministic engine and audit the artefacts.

    If ``skip_reason`` is provided, the scenario is reported as
    ``skipped`` with that reason and no run directory is produced.
    """

    if skip_reason:
        return ScenarioVerification(
            expectation=expectation,
            status=AcceptanceStatus.SKIPPED,
            run_dir=None,
            final_safety_state=None,
            final_mission_state=None,
            fired_faults=(),
            recovery_engagement_count=0,
            checks=[
                ScenarioCheck(
                    name="execution",
                    status=AcceptanceStatus.SKIPPED,
                    detail=skip_reason,
                )
            ],
            not_executed_reason=skip_reason,
        )

    scenarios_dir = Path(scenarios_dir or SCENARIOS_DIR)
    runs_root = Path(runs_root)
    scenario_path = scenarios_dir / expectation.scenario_file
    if not scenario_path.exists():
        return ScenarioVerification(
            expectation=expectation,
            status=AcceptanceStatus.NOT_EXECUTED,
            run_dir=None,
            final_safety_state=None,
            final_mission_state=None,
            fired_faults=(),
            recovery_engagement_count=0,
            checks=[
                ScenarioCheck(
                    name="execution",
                    status=AcceptanceStatus.NOT_EXECUTED,
                    detail=f"scenario file missing: {scenario_path}",
                )
            ],
            not_executed_reason=f"scenario file missing: {scenario_path}",
        )

    runs_root.mkdir(parents=True, exist_ok=True)
    scenario = ScenarioDefinition.from_json_file(scenario_path)
    run_id = RunId(f"verify-{scenario.scenario_id}")
    engine = SimulationEngine(
        scenario=scenario,
        runs_root=runs_root,
        run_id=run_id,
        clock=ManualClock(),
        id_generator=SequentialIdGenerator(),
    )
    engine.run()

    final_safety = engine.supervisor.safety_state
    final_mission = (
        engine._mission_orchestrator.state.value
        if engine._mission_orchestrator is not None
        else None
    )
    fired = tuple(
        sorted(
            event.attributes.get("fault_id")
            for event in engine.event_store.all()
            if event.event_type == "fault_injection.fired"
            and isinstance(event.attributes.get("fault_id"), str)
        )
    )
    observed_event_types = {e.event_type for e in engine.event_store.all()}
    recovery_engagements = sum(
        1
        for e in engine.event_store.all()
        if e.event_type == "mission_recovery.engaged"
    )

    checks: list[ScenarioCheck] = []

    # 1. Execution succeeded.
    checks.append(
        ScenarioCheck(
            name="execution",
            status=AcceptanceStatus.PASSED,
            detail=f"engine completed; events={len(engine.event_store.all())}",
        )
    )

    # 2. Safety state matches.
    if final_safety == expectation.expected_safety_state:
        checks.append(
            ScenarioCheck(
                name="safety_state",
                status=AcceptanceStatus.PASSED,
                detail=f"final={final_safety.value}",
            )
        )
    else:
        checks.append(
            ScenarioCheck(
                name="safety_state",
                status=AcceptanceStatus.FAILED,
                detail=(
                    f"expected {expectation.expected_safety_state.value}, "
                    f"got {final_safety.value}"
                ),
            )
        )

    # 3. Mission state matches.
    if expectation.expected_mission_state is not None:
        if final_mission == expectation.expected_mission_state:
            checks.append(
                ScenarioCheck(
                    name="mission_state",
                    status=AcceptanceStatus.PASSED,
                    detail=f"final={final_mission}",
                )
            )
        else:
            checks.append(
                ScenarioCheck(
                    name="mission_state",
                    status=AcceptanceStatus.FAILED,
                    detail=(
                        f"expected {expectation.expected_mission_state}, "
                        f"got {final_mission}"
                    ),
                )
            )

    # 4. Required events present.
    missing_required = [
        et for et in expectation.required_event_types if et not in observed_event_types
    ]
    if missing_required:
        checks.append(
            ScenarioCheck(
                name="required_events",
                status=AcceptanceStatus.FAILED,
                detail=f"missing: {', '.join(missing_required)}",
            )
        )
    elif expectation.required_event_types:
        checks.append(
            ScenarioCheck(
                name="required_events",
                status=AcceptanceStatus.PASSED,
                detail=f"all {len(expectation.required_event_types)} present",
            )
        )

    # 5. Forbidden events absent.
    present_forbidden = [
        et for et in expectation.forbidden_event_types if et in observed_event_types
    ]
    if present_forbidden:
        checks.append(
            ScenarioCheck(
                name="forbidden_events",
                status=AcceptanceStatus.FAILED,
                detail=f"present: {', '.join(present_forbidden)}",
            )
        )
    elif expectation.forbidden_event_types:
        checks.append(
            ScenarioCheck(
                name="forbidden_events",
                status=AcceptanceStatus.PASSED,
                detail=f"all {len(expectation.forbidden_event_types)} absent",
            )
        )

    # 6. Fault expectations.
    if expectation.expected_fired_faults:
        missing_faults = [
            f for f in expectation.expected_fired_faults if f not in fired
        ]
        checks.append(
            ScenarioCheck(
                name="fired_faults",
                status=(
                    AcceptanceStatus.PASSED
                    if not missing_faults
                    else AcceptanceStatus.FAILED
                ),
                detail=(
                    f"observed {fired}"
                    if not missing_faults
                    else f"missing: {', '.join(missing_faults)}"
                ),
            )
        )

    # 7. Recovery engagements.
    if expectation.min_recovery_engagements:
        checks.append(
            ScenarioCheck(
                name="recovery_engagements",
                status=(
                    AcceptanceStatus.PASSED
                    if recovery_engagements >= expectation.min_recovery_engagements
                    else AcceptanceStatus.FAILED
                ),
                detail=(
                    f"observed {recovery_engagements}; "
                    f"expected at least {expectation.min_recovery_engagements}"
                ),
            )
        )

    # 8. Command path audit.
    cmd_audit = audit_command_path(engine.recorder.run_dir)
    checks.append(
        ScenarioCheck(
            name="command_path_audit",
            status=cmd_audit.status,
            detail=(
                f"commands={cmd_audit.command_count} clamped={cmd_audit.clamped_count} "
                f"zeroed={cmd_audit.zeroed_count} expired={cmd_audit.expired_count}"
            ),
            errors=list(cmd_audit.errors),
            warnings=list(cmd_audit.warnings),
        )
    )

    # 9. Safety transition audit.
    safety_audit = audit_safety_transitions(engine.recorder.run_dir)
    checks.append(
        ScenarioCheck(
            name="safety_transition_audit",
            status=safety_audit.status,
            detail=(
                f"transitions={safety_audit.transition_count} "
                f"final={safety_audit.final_state}"
            ),
            errors=list(safety_audit.errors),
            warnings=list(safety_audit.warnings),
        )
    )

    # 10. Replay integrity.
    replay = verify_replay_integrity(engine.recorder.run_dir)
    checks.append(
        ScenarioCheck(
            name="replay_integrity",
            status=replay.status,
            detail=(
                f"events={replay.event_count} transitions={replay.transition_count} "
                f"mission_states={replay.mission_state_count}"
            ),
            errors=list(replay.errors),
            warnings=list(replay.warnings),
        )
    )

    # 11. Optional safe-stop zero motion check.
    if expectation.expected_safe_stop_zero_motion:
        zero_check_status = AcceptanceStatus.PASSED
        zero_check_detail = "all safe-stop / e-stop commands zero"
        if cmd_audit.errors:
            zero_check_status = AcceptanceStatus.FAILED
            zero_check_detail = "; ".join(
                e for e in cmd_audit.errors if "non-zero motion" in e
            ) or "command_path_audit reported errors"
        checks.append(
            ScenarioCheck(
                name="safe_stop_zero_motion",
                status=zero_check_status,
                detail=zero_check_detail,
            )
        )

    overall = aggregate_status(c.status for c in checks)
    return ScenarioVerification(
        expectation=expectation,
        status=overall,
        run_dir=engine.recorder.run_dir,
        final_safety_state=final_safety,
        final_mission_state=final_mission,
        fired_faults=fired,
        recovery_engagement_count=recovery_engagements,
        checks=checks,
    )
