"""Tests for the recovery policy state machine."""

from __future__ import annotations

from app.mission.enums import RecoveryBehavior, RecoveryDecision
from app.mission.recovery import RecoveryPolicy


def _evaluate(
    policy: RecoveryPolicy,
    *,
    waypoint_id: str | None = "w1",
    timed_out: bool = False,
    keepout: bool = False,
    keepout_pending: bool = False,
    sensor_degraded: bool = False,
    operator_recovery: bool = False,
    safety_inhibits: bool = False,
    now_ms: int = 0,
):
    return policy.evaluate(
        active_waypoint_id=waypoint_id,
        active_waypoint_timed_out=timed_out,
        keepout_violation=keepout,
        keepout_pending=keepout_pending,
        sensor_health_degraded=sensor_degraded,
        operator_recovery_request=operator_recovery,
        safety_state_inhibits_motion=safety_inhibits,
        now_ms=now_ms,
    )


def test_no_signals_returns_continue() -> None:
    p = RecoveryPolicy()
    s = _evaluate(p)
    assert s.decision == RecoveryDecision.CONTINUE
    assert s.active_behavior is None


def test_waypoint_timeout_engages_backup_and_retry() -> None:
    p = RecoveryPolicy(max_attempts=3)
    s = _evaluate(p, timed_out=True, now_ms=100)
    assert s.decision == RecoveryDecision.ENGAGE
    assert s.active_behavior == RecoveryBehavior.BACKUP_AND_RETRY
    assert p.attempt_count(waypoint_id="w1") == 1


def test_repeated_timeout_increments_attempts_after_backup_clears() -> None:
    p = RecoveryPolicy(max_attempts=3, backup_duration_ms=500)
    _evaluate(p, timed_out=True, now_ms=100)
    # Mid-backup: continue, attempt count unchanged.
    s2 = _evaluate(p, timed_out=True, now_ms=400)
    assert s2.decision == RecoveryDecision.CONTINUE
    # Backup elapses: clear.
    s3 = _evaluate(p, timed_out=True, now_ms=700)
    assert s3.decision == RecoveryDecision.CLEAR
    # Next timeout (after waypoint timer reset by orchestrator) increments.
    s4 = _evaluate(p, timed_out=True, now_ms=900)
    assert s4.decision == RecoveryDecision.ENGAGE
    assert p.attempt_count(waypoint_id="w1") == 2


def test_attempts_exceeded_engages_mission_abort() -> None:
    p = RecoveryPolicy(max_attempts=1, backup_duration_ms=200)
    _evaluate(p, timed_out=True, now_ms=0)
    _evaluate(p, timed_out=True, now_ms=300)  # CLEAR
    s = _evaluate(p, timed_out=True, now_ms=500)
    assert s.decision == RecoveryDecision.ESCALATE
    assert s.active_behavior == RecoveryBehavior.MISSION_ABORT


def test_mission_abort_is_terminal() -> None:
    p = RecoveryPolicy(max_attempts=0)
    p.force_abort(waypoint_id="w1", now_ms=0, reason="test")
    s = _evaluate(p, timed_out=False, now_ms=100)
    # Once MISSION_ABORT is set, no further engagements happen.
    assert s.active_behavior == RecoveryBehavior.MISSION_ABORT
    assert s.decision == RecoveryDecision.CONTINUE


def test_keepout_violation_escalates_to_safe_stop_escalation() -> None:
    p = RecoveryPolicy()
    s = _evaluate(p, keepout=True)
    assert s.active_behavior == RecoveryBehavior.SAFE_STOP_ESCALATION
    assert s.decision == RecoveryDecision.ESCALATE


def test_safety_state_inhibits_motion_escalates() -> None:
    p = RecoveryPolicy()
    s = _evaluate(p, safety_inhibits=True)
    assert s.active_behavior == RecoveryBehavior.SAFE_STOP_ESCALATION


def test_sensor_health_degraded_engages_wait() -> None:
    p = RecoveryPolicy()
    s = _evaluate(p, sensor_degraded=True)
    assert s.active_behavior == RecoveryBehavior.WAIT_FOR_SENSOR_RECOVERY


def test_operator_recovery_engages_stop_and_reevaluate() -> None:
    p = RecoveryPolicy()
    s = _evaluate(p, operator_recovery=True)
    assert s.active_behavior == RecoveryBehavior.STOP_AND_REEVALUATE
