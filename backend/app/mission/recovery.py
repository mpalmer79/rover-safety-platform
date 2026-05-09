"""Recovery behaviour selection.

The recovery policy is a small state machine that lives alongside the
mission orchestrator. Its responsibilities:

* select an appropriate :class:`RecoveryBehavior` given the failure
  signature (waypoint timeout, keepout pending, sensor health
  degradation),
* track per-waypoint recovery attempts against the plan's
  ``max_recovery_attempts`` budget,
* escalate to ``MISSION_ABORTING`` when the budget is exhausted.

Recovery behaviours never override safety state. The orchestrator
records recovery markers for replay; the supervisor still owns
``/safety/state`` and the actual zero-motion authorisation in
``SAFE_STOP``.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Optional

from app.mission.enums import (
    MissionState,
    RecoveryBehavior,
    RecoveryDecision,
)


@dataclass(frozen=True)
class RecoverySnapshot:
    """Per-tick snapshot of recovery state."""

    active_behavior: Optional[RecoveryBehavior]
    decision: RecoveryDecision
    reason_code: str
    attempt_count: int
    waypoint_id: Optional[str]
    summary: str
    started_at_ms: Optional[int] = None
    elapsed_ms: int = 0


class RecoveryPolicy:
    """Decision logic for engaging / clearing recovery behaviours."""

    def __init__(
        self,
        *,
        max_attempts: int = 3,
        backup_duration_ms: int = 1500,
    ) -> None:
        if max_attempts < 0:
            raise ValueError("max_attempts must be non-negative")
        if backup_duration_ms <= 0:
            raise ValueError("backup_duration_ms must be positive")
        self._max_attempts = max_attempts
        self._backup_duration_ms = backup_duration_ms
        self._active: Optional[RecoveryBehavior] = None
        self._active_waypoint_id: Optional[str] = None
        self._attempt_counts: dict[str, int] = {}
        self._started_at_ms: Optional[int] = None
        self._latest_reason: str = ""

    @property
    def active_behavior(self) -> Optional[RecoveryBehavior]:
        return self._active

    @property
    def is_active(self) -> bool:
        return self._active is not None

    def attempt_count(self, *, waypoint_id: str) -> int:
        return self._attempt_counts.get(waypoint_id, 0)

    def evaluate(
        self,
        *,
        active_waypoint_id: Optional[str],
        active_waypoint_timed_out: bool,
        keepout_violation: bool,
        keepout_pending: bool,
        sensor_health_degraded: bool,
        operator_recovery_request: bool,
        safety_state_inhibits_motion: bool,
        now_ms: int,
    ) -> RecoverySnapshot:
        # Mission abort is terminal: once set we hold without
        # re-emitting engage events.
        if self._active == RecoveryBehavior.MISSION_ABORT:
            return self._snapshot(
                decision=RecoveryDecision.CONTINUE,
                summary="recovery active: mission_abort latched",
                now_ms=now_ms,
            )

        # Operator request always takes precedence.
        if operator_recovery_request and self._active is None:
            self._engage(
                RecoveryBehavior.STOP_AND_REEVALUATE,
                waypoint_id=active_waypoint_id,
                now_ms=now_ms,
                reason="operator_recovery",
            )
            return self._snapshot(
                decision=RecoveryDecision.ENGAGE,
                summary="recovery engaged: operator_recovery",
                now_ms=now_ms,
            )

        if keepout_violation and self._active != RecoveryBehavior.MISSION_ABORT:
            transitioning = self._active != RecoveryBehavior.SAFE_STOP_ESCALATION
            self._engage(
                RecoveryBehavior.SAFE_STOP_ESCALATION,
                waypoint_id=active_waypoint_id,
                now_ms=now_ms,
                reason="keepout_violation",
            )
            return self._snapshot(
                decision=RecoveryDecision.ESCALATE
                if transitioning
                else RecoveryDecision.CONTINUE,
                summary="recovery escalated: keepout_violation"
                if transitioning
                else "recovery active: keepout_violation persists",
                now_ms=now_ms,
            )

        if active_waypoint_timed_out:
            already_in_backup = (
                self._active == RecoveryBehavior.BACKUP_AND_RETRY
                and self._active_waypoint_id == active_waypoint_id
            )
            if already_in_backup:
                # We already engaged BACKUP_AND_RETRY for this waypoint
                # and the attempt counter has been incremented. Hold
                # until the backup duration elapses, then clear so a
                # subsequent timeout can increment the attempt counter.
                elapsed = (
                    now_ms - self._started_at_ms
                    if self._started_at_ms is not None
                    else 0
                )
                if elapsed >= self._backup_duration_ms:
                    cleared = self._active
                    self._clear()
                    return RecoverySnapshot(
                        active_behavior=None,
                        decision=RecoveryDecision.CLEAR,
                        reason_code="recovery_cleared",
                        attempt_count=self._attempt_counts.get(
                            active_waypoint_id or "", 0
                        ),
                        waypoint_id=active_waypoint_id,
                        summary=f"recovery cleared: {cleared.value} elapsed",
                        started_at_ms=None,
                        elapsed_ms=elapsed,
                    )
                return self._snapshot(
                    decision=RecoveryDecision.CONTINUE,
                    summary=(
                        f"recovery active: waypoint {active_waypoint_id} backup_and_retry"
                    ),
                    now_ms=now_ms,
                )
            attempts = self._increment_attempts(active_waypoint_id)
            if attempts > self._max_attempts:
                self._engage(
                    RecoveryBehavior.MISSION_ABORT,
                    waypoint_id=active_waypoint_id,
                    now_ms=now_ms,
                    reason="recovery_attempts_exceeded",
                )
                return self._snapshot(
                    decision=RecoveryDecision.ESCALATE,
                    summary=(
                        f"mission abort: waypoint {active_waypoint_id} "
                        f"exceeded {self._max_attempts} attempts"
                    ),
                    now_ms=now_ms,
                )
            self._engage(
                RecoveryBehavior.BACKUP_AND_RETRY,
                waypoint_id=active_waypoint_id,
                now_ms=now_ms,
                reason="waypoint_timeout",
            )
            return self._snapshot(
                decision=RecoveryDecision.ENGAGE,
                summary=(
                    f"recovery engaged: waypoint {active_waypoint_id} "
                    f"timed out (attempt {attempts}/{self._max_attempts})"
                ),
                now_ms=now_ms,
            )

        if sensor_health_degraded and self._active is None:
            self._engage(
                RecoveryBehavior.WAIT_FOR_SENSOR_RECOVERY,
                waypoint_id=active_waypoint_id,
                now_ms=now_ms,
                reason="sensor_health_degraded",
            )
            return self._snapshot(
                decision=RecoveryDecision.ENGAGE,
                summary="recovery engaged: sensor_health_degraded",
                now_ms=now_ms,
            )

        if safety_state_inhibits_motion and self._active != RecoveryBehavior.SAFE_STOP_ESCALATION:
            # The supervisor already owns the response, but we record the
            # corresponding mission-recovery state for replay.
            self._engage(
                RecoveryBehavior.SAFE_STOP_ESCALATION,
                waypoint_id=active_waypoint_id,
                now_ms=now_ms,
                reason="safety_state_inhibits_motion",
            )
            return self._snapshot(
                decision=RecoveryDecision.ESCALATE,
                summary="recovery follows supervisor: safety_state_inhibits_motion",
                now_ms=now_ms,
            )

        if self._active is not None:
            should_clear = self._should_clear(
                active_waypoint_id=active_waypoint_id,
                keepout_violation=keepout_violation,
                keepout_pending=keepout_pending,
                sensor_health_degraded=sensor_health_degraded,
                safety_state_inhibits_motion=safety_state_inhibits_motion,
                now_ms=now_ms,
            )
            if should_clear:
                cleared_behavior = self._active
                self._clear()
                return RecoverySnapshot(
                    active_behavior=None,
                    decision=RecoveryDecision.CLEAR,
                    reason_code="recovery_cleared",
                    attempt_count=self._attempt_counts.get(active_waypoint_id or "", 0),
                    waypoint_id=active_waypoint_id,
                    summary=f"recovery cleared: {cleared_behavior.value}",
                    started_at_ms=None,
                    elapsed_ms=0,
                )
            # Hold.
            return self._snapshot(
                decision=RecoveryDecision.CONTINUE,
                summary=f"recovery active: {self._active.value}",
                now_ms=now_ms,
            )

        # Nothing to engage and nothing was active.
        return RecoverySnapshot(
            active_behavior=None,
            decision=RecoveryDecision.CONTINUE,
            reason_code="no_recovery",
            attempt_count=self._attempt_counts.get(active_waypoint_id or "", 0),
            waypoint_id=active_waypoint_id,
            summary="no recovery in progress",
            started_at_ms=None,
            elapsed_ms=0,
        )

    def force_abort(self, *, waypoint_id: Optional[str], now_ms: int, reason: str) -> RecoverySnapshot:
        """Force the policy into ``MISSION_ABORT`` immediately."""

        self._engage(
            RecoveryBehavior.MISSION_ABORT,
            waypoint_id=waypoint_id,
            now_ms=now_ms,
            reason=reason,
        )
        return self._snapshot(
            decision=RecoveryDecision.ESCALATE,
            summary=f"forced abort: {reason}",
            now_ms=now_ms,
        )

    def reset_after_abort(self) -> None:
        self._clear()
        self._attempt_counts.clear()

    def implied_state(self, current_state: MissionState) -> MissionState:
        """Return the mission state implied by the active recovery."""

        if self._active is None:
            return current_state
        if self._active == RecoveryBehavior.MISSION_ABORT:
            return MissionState.MISSION_ABORTING
        if self._active == RecoveryBehavior.SAFE_STOP_ESCALATION:
            return MissionState.MISSION_DEGRADED
        return MissionState.MISSION_RECOVERY

    # ------------------------------------------------------------------
    def _engage(
        self,
        behavior: RecoveryBehavior,
        *,
        waypoint_id: Optional[str],
        now_ms: int,
        reason: str,
    ) -> None:
        self._active = behavior
        self._active_waypoint_id = waypoint_id
        self._latest_reason = reason
        if self._started_at_ms is None or self._active != behavior:
            self._started_at_ms = now_ms

    def _increment_attempts(self, waypoint_id: Optional[str]) -> int:
        if not waypoint_id:
            return 1
        new = self._attempt_counts.get(waypoint_id, 0) + 1
        self._attempt_counts[waypoint_id] = new
        return new

    def _clear(self) -> None:
        self._active = None
        self._started_at_ms = None
        self._latest_reason = "recovery_cleared"

    def _should_clear(
        self,
        *,
        active_waypoint_id: Optional[str],
        keepout_violation: bool,
        keepout_pending: bool,
        sensor_health_degraded: bool,
        safety_state_inhibits_motion: bool,
        now_ms: int,
    ) -> bool:
        if self._active == RecoveryBehavior.MISSION_ABORT:
            return False
        if self._active == RecoveryBehavior.SAFE_STOP_ESCALATION:
            return not keepout_violation and not safety_state_inhibits_motion
        if self._active == RecoveryBehavior.WAIT_FOR_SENSOR_RECOVERY:
            return not sensor_health_degraded
        if self._active == RecoveryBehavior.STOP_AND_REEVALUATE:
            return not keepout_pending and not sensor_health_degraded
        if self._active == RecoveryBehavior.BACKUP_AND_RETRY:
            # Clears either when the active waypoint changes (queue
            # advanced) or when the configured backup duration elapses,
            # whichever comes first. The duration-based clear is what
            # lets the next timeout increment the attempt counter.
            if active_waypoint_id != self._active_waypoint_id:
                return True
            elapsed = (
                now_ms - self._started_at_ms
                if self._started_at_ms is not None
                else 0
            )
            return elapsed >= self._backup_duration_ms
        return False

    def _snapshot(
        self, *, decision: RecoveryDecision, summary: str, now_ms: int
    ) -> RecoverySnapshot:
        attempts = (
            self._attempt_counts.get(self._active_waypoint_id or "", 0)
            if self._active_waypoint_id
            else 0
        )
        elapsed = now_ms - self._started_at_ms if self._started_at_ms is not None else 0
        return RecoverySnapshot(
            active_behavior=self._active,
            decision=decision,
            reason_code=self._latest_reason,
            attempt_count=attempts,
            waypoint_id=self._active_waypoint_id,
            summary=summary,
            started_at_ms=self._started_at_ms,
            elapsed_ms=max(0, elapsed),
        )
