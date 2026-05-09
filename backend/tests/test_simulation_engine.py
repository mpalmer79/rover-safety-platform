"""End-to-end tests for the deterministic simulation engine."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.domain.enums import SafetyState
from app.domain.identifiers import RunId, ScenarioId, SequentialIdGenerator
from app.domain.scenarios import (
    RequestedMotionPlan,
    ScenarioDefinition,
    ScenarioFault,
    ScenarioInitialState,
)
from app.domain.time import ManualClock
from app.simulation.engine import SimulationEngine


def _engine(tmp_path: Path, scenario: ScenarioDefinition) -> SimulationEngine:
    return SimulationEngine(
        scenario=scenario,
        runs_root=tmp_path,
        run_id=RunId("run-eng-0001"),
        clock=ManualClock(),
        id_generator=SequentialIdGenerator(),
    )


def _nominal(*, scenario_id: str = "nominal") -> ScenarioDefinition:
    return ScenarioDefinition(
        scenario_id=ScenarioId(scenario_id),
        duration_seconds=4.0,
        time_step_ms=100,
        initial_state=ScenarioInitialState(operator_activate_at_ms=200),
        requested_motion=RequestedMotionPlan(linear_velocity=0.4, angular_velocity=0.0),
    )


def test_nominal_scenario_completes_in_active_normal(tmp_path: Path) -> None:
    eng = _engine(tmp_path, _nominal())
    result = eng.run()
    assert result.final_safety_state == SafetyState.ACTIVE_NORMAL
    assert result.event_count > 0
    assert result.run_dir.exists()
    assert (result.run_dir / "events.jsonl").exists()
    assert (result.run_dir / "states.jsonl").exists()
    assert (result.run_dir / "commands.jsonl").exists()
    assert (result.run_dir / "sensor_readings.jsonl").exists()
    assert (result.run_dir / "incident-summary.md").exists()
    assert (result.run_dir / "metadata.json").exists()


def test_stale_lidar_scenario_reaches_safe_stop(tmp_path: Path) -> None:
    sc = _nominal(scenario_id="stale-lidar")
    sc = ScenarioDefinition(
        scenario_id=sc.scenario_id,
        duration_seconds=5.0,
        time_step_ms=100,
        initial_state=sc.initial_state,
        requested_motion=sc.requested_motion,
        faults=(
            ScenarioFault(
                fault_id="f1",
                fault_type="stale_lidar",
                target="/scan",
                activation_ms=1500,
                duration_ms=-1,
            ),
        ),
    )
    result = _engine(tmp_path, sc).run()
    assert result.final_safety_state == SafetyState.SAFE_STOP
    assert "f1" in result.fired_faults


def test_estop_scenario_latches(tmp_path: Path) -> None:
    sc = ScenarioDefinition(
        scenario_id=ScenarioId("estop"),
        duration_seconds=4.0,
        time_step_ms=100,
        initial_state=ScenarioInitialState(
            operator_activate_at_ms=200, operator_estop_at_ms=1500
        ),
        requested_motion=RequestedMotionPlan(linear_velocity=0.4, angular_velocity=0.0),
    )
    result = _engine(tmp_path, sc).run()
    assert result.final_safety_state == SafetyState.E_STOP_LATCHED


def test_estop_does_not_self_clear(tmp_path: Path) -> None:
    sc = ScenarioDefinition(
        scenario_id=ScenarioId("estop-no-self-clear"),
        duration_seconds=6.0,
        time_step_ms=100,
        initial_state=ScenarioInitialState(
            operator_activate_at_ms=200, operator_estop_at_ms=1000
        ),
        requested_motion=RequestedMotionPlan(linear_velocity=0.4, angular_velocity=0.0),
    )
    result = _engine(tmp_path, sc).run()
    assert result.final_safety_state == SafetyState.E_STOP_LATCHED


def test_sensor_disagreement_scenario_reaches_degraded_or_safe_stop(tmp_path: Path) -> None:
    sc = ScenarioDefinition(
        scenario_id=ScenarioId("disagreement"),
        duration_seconds=5.0,
        time_step_ms=100,
        initial_state=ScenarioInitialState(operator_activate_at_ms=200),
        requested_motion=RequestedMotionPlan(linear_velocity=0.4, angular_velocity=0.0),
        faults=(
            ScenarioFault(
                fault_id="f-disagreement",
                fault_type="sensor_disagreement",
                target="/odom",
                activation_ms=1500,
                duration_ms=-1,
                parameters={"angular_offset_rad_s": 0.7},
            ),
        ),
    )
    result = _engine(tmp_path, sc).run()
    assert result.final_safety_state in {
        SafetyState.ACTIVE_DEGRADED,
        SafetyState.SAFE_STOP,
    }


def test_command_timeout_drives_supervisor_to_safe_stop(tmp_path: Path) -> None:
    sc = ScenarioDefinition(
        scenario_id=ScenarioId("cmd-timeout"),
        duration_seconds=5.0,
        time_step_ms=100,
        initial_state=ScenarioInitialState(operator_activate_at_ms=200),
        requested_motion=RequestedMotionPlan(linear_velocity=0.4, angular_velocity=0.0),
        faults=(
            ScenarioFault(
                fault_id="f-cmd-to",
                fault_type="command_timeout",
                target="rover_hw_gateway",
                activation_ms=1500,
                duration_ms=-1,
            ),
        ),
    )
    result = _engine(tmp_path, sc).run()
    assert result.final_safety_state == SafetyState.SAFE_STOP


def test_two_runs_are_event_deterministic(tmp_path: Path) -> None:
    sc1 = _nominal()

    eng_a = SimulationEngine(
        scenario=sc1,
        runs_root=tmp_path / "a",
        run_id=RunId("run-a"),
        clock=ManualClock(),
        id_generator=SequentialIdGenerator(),
    )
    eng_b = SimulationEngine(
        scenario=sc1,
        runs_root=tmp_path / "b",
        run_id=RunId("run-b"),
        clock=ManualClock(),
        id_generator=SequentialIdGenerator(),
    )
    eng_a.run()
    eng_b.run()
    a_types = [e.event_type for e in eng_a.event_store.all()]
    b_types = [e.event_type for e in eng_b.event_store.all()]
    assert a_types == b_types
    a_reasons = [e.reason_code for e in eng_a.event_store.all()]
    b_reasons = [e.reason_code for e in eng_b.event_store.all()]
    assert a_reasons == b_reasons


def test_supervisor_is_only_publisher_of_authorized_motion(tmp_path: Path) -> None:
    """Architectural invariant: every ``final_motion`` payload was constructed
    by the supervisor's arbiter, identifiable by its ``source`` field.
    """

    eng = _engine(tmp_path, _nominal())
    eng.run()
    arb_events = [
        e for e in eng.event_store.all()
        if e.final_motion is not None
    ]
    assert arb_events, "expected at least one event carrying final_motion"
    for e in arb_events:
        assert e.final_motion.source == "safety.supervisor.arbitration"


def test_fault_injection_does_not_emit_safety_transitions(tmp_path: Path) -> None:
    sc = ScenarioDefinition(
        scenario_id=ScenarioId("fault-no-direct-transitions"),
        duration_seconds=4.0,
        time_step_ms=100,
        initial_state=ScenarioInitialState(operator_activate_at_ms=200),
        requested_motion=RequestedMotionPlan(linear_velocity=0.4, angular_velocity=0.0),
        faults=(
            ScenarioFault(
                fault_id="f1",
                fault_type="stale_lidar",
                target="/scan",
                activation_ms=1500,
                duration_ms=-1,
            ),
        ),
    )
    eng = _engine(tmp_path, sc)
    eng.run()
    fault_events = [e for e in eng.event_store.all() if e.subsystem == "fault_injection"]
    for e in fault_events:
        assert not e.event_type.startswith("safety_transition.")
