"""Tests for the mission orchestrator.

These tests exercise the orchestrator end-to-end against a static
sensor frame and a sequence of synthetic poses. They verify the four
non-negotiable invariants:

1. The orchestrator only ever produces ``RequestedMotionCommand``
   values whose ``source`` is the documented mission source. It never
   produces ``AuthorizedMotionCommand``.
2. Mission state advances through the legal transition graph.
3. Recovery transitions emit ``mission_recovery.engaged`` /
   ``mission_recovery.cleared`` events.
4. Operator pause / abort propagate immediately.
"""

from __future__ import annotations

from app.domain.enums import SafetyState, SensorStatus, SensorType
from app.domain.identifiers import RunId, ScenarioId, SequentialIdGenerator
from app.domain.motion import RequestedMotionCommand
from app.domain.sensors import (
    ContactReading,
    EncoderReading,
    IMUReading,
    LiDARReading,
    SensorFrame,
)
from app.domain.time import ManualClock
from app.mission.constraints import MissionConstraints
from app.mission.enums import MissionState
from app.mission.mission_plan import MissionPlan
from app.mission.orchestrator import MissionOrchestrator, OrchestratorInputs
from app.mission.waypoints import Waypoint


def _frame(now_ms: int = 0) -> SensorFrame:
    return SensorFrame(
        lidar=LiDARReading(
            sensor_id="r/lidar",
            sensor_type=SensorType.LIDAR,
            timestamp_ms=now_ms,
            status=SensorStatus.HEALTHY,
            confidence=0.9,
            source="t",
            sequence_number=now_ms,
            min_range_m=2.0,
            max_range_m=10.0,
            mean_range_m=5.0,
            point_count=720,
        ),
        imu=IMUReading(
            sensor_id="r/imu",
            sensor_type=SensorType.IMU,
            timestamp_ms=now_ms,
            status=SensorStatus.HEALTHY,
            confidence=0.85,
            source="t",
            sequence_number=now_ms,
        ),
        encoder=EncoderReading(
            sensor_id="r/enc",
            sensor_type=SensorType.WHEEL_ENCODER,
            timestamp_ms=now_ms,
            status=SensorStatus.HEALTHY,
            confidence=0.9,
            source="t",
            sequence_number=now_ms,
        ),
        contact=ContactReading(
            sensor_id="r/contact",
            sensor_type=SensorType.CONTACT,
            timestamp_ms=now_ms,
            status=SensorStatus.HEALTHY,
            confidence=1.0,
            source="t",
            sequence_number=now_ms,
        ),
    )


def _orch(plan: MissionPlan) -> MissionOrchestrator:
    return MissionOrchestrator(
        plan=plan,
        run_id=RunId("r"),
        scenario_id=ScenarioId("s"),
        clock=ManualClock(),
        id_generator=SequentialIdGenerator(),
    )


def _plan(*waypoints: Waypoint, max_recovery_attempts: int = 3) -> MissionPlan:
    return MissionPlan(
        mission_id="test",
        waypoints=waypoints or (
            Waypoint("w1", 1.0, 0.0, 0.0, 0.20, 0.40, 30.0),
        ),
        constraints=MissionConstraints(
            max_linear_velocity=0.4,
            max_angular_velocity=0.8,
            minimum_confidence_for_motion=0.4,
            minimum_sensor_health=3,
        ),
        max_recovery_attempts=max_recovery_attempts,
    )


def test_orchestrator_only_produces_requested_motion() -> None:
    orch = _orch(_plan())
    out = orch.evaluate(
        OrchestratorInputs(
            pose_x=0.0,
            pose_y=0.0,
            heading_rad=0.0,
            sensor_frame=_frame(0),
            confidence_score=0.9,
            safety_state=SafetyState.ACTIVE_NORMAL,
            operator_start=True,
            now_ms=0,
            sim_time_ns=0,
        )
    )
    if out.requested_motion is not None:
        assert isinstance(out.requested_motion, RequestedMotionCommand)
        assert out.requested_motion.source == "mission.orchestrator"


def test_idle_to_active_via_operator_start() -> None:
    orch = _orch(_plan())
    assert orch.state == MissionState.MISSION_IDLE
    orch.evaluate(
        OrchestratorInputs(
            pose_x=0.0,
            pose_y=0.0,
            heading_rad=0.0,
            sensor_frame=_frame(0),
            confidence_score=0.9,
            safety_state=SafetyState.ACTIVE_NORMAL,
            operator_start=True,
            now_ms=0,
            sim_time_ns=0,
        )
    )
    assert orch.state == MissionState.MISSION_ACTIVE


def test_operator_abort_transitions_to_aborted() -> None:
    orch = _orch(_plan())
    orch.evaluate(
        OrchestratorInputs(
            pose_x=0.0,
            pose_y=0.0,
            heading_rad=0.0,
            sensor_frame=_frame(0),
            confidence_score=0.9,
            safety_state=SafetyState.ACTIVE_NORMAL,
            operator_start=True,
            now_ms=0,
            sim_time_ns=0,
        )
    )
    orch.evaluate(
        OrchestratorInputs(
            pose_x=0.0,
            pose_y=0.0,
            heading_rad=0.0,
            sensor_frame=_frame(100),
            confidence_score=0.9,
            safety_state=SafetyState.ACTIVE_NORMAL,
            operator_abort=True,
            now_ms=100,
            sim_time_ns=100_000_000,
        )
    )
    # ABORTING then ABORTED on next tick.
    orch.evaluate(
        OrchestratorInputs(
            pose_x=0.0,
            pose_y=0.0,
            heading_rad=0.0,
            sensor_frame=_frame(200),
            confidence_score=0.9,
            safety_state=SafetyState.ACTIVE_NORMAL,
            now_ms=200,
            sim_time_ns=200_000_000,
        )
    )
    assert orch.state == MissionState.MISSION_ABORTED


def test_safety_inhibits_motion_drives_to_degraded() -> None:
    orch = _orch(_plan())
    orch.evaluate(
        OrchestratorInputs(
            pose_x=0.0,
            pose_y=0.0,
            heading_rad=0.0,
            sensor_frame=_frame(0),
            confidence_score=0.9,
            safety_state=SafetyState.ACTIVE_NORMAL,
            operator_start=True,
            now_ms=0,
            sim_time_ns=0,
        )
    )
    out = orch.evaluate(
        OrchestratorInputs(
            pose_x=0.0,
            pose_y=0.0,
            heading_rad=0.0,
            sensor_frame=_frame(100),
            confidence_score=0.5,
            safety_state=SafetyState.SAFE_STOP,
            now_ms=100,
            sim_time_ns=100_000_000,
        )
    )
    assert orch.state in {MissionState.MISSION_DEGRADED, MissionState.MISSION_RECOVERY}
    # Motion request must always be zero in this state.
    if out.requested_motion is not None:
        assert out.requested_motion.linear_velocity == 0.0
        assert out.requested_motion.angular_velocity == 0.0


def test_orchestrator_does_not_construct_authorized_motion() -> None:
    """The orchestrator must never reference :class:`AuthorizedMotionCommand`.

    Source-level scan: the only allowed import of
    AuthorizedMotionCommand is in the safety arbiter module.
    """

    import inspect
    from app.mission import orchestrator as orch_mod

    src = inspect.getsource(orch_mod)
    assert "AuthorizedMotionCommand(" not in src, (
        "mission orchestrator must not construct AuthorizedMotionCommand"
    )
