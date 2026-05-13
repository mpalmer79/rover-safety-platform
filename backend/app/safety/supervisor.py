"""Safety supervisor.

The supervisor evaluates the rover's inputs once per tick and produces:

* the next safety state (transitioning if needed),
* an authorized motion command (always present, possibly zero),
* a list of structured events describing every operationally
  significant fact that occurred during the evaluation.

The supervisor is the **only** authority that publishes
``AuthorizedMotionCommand`` values. The arbiter constructs them, but
only at the supervisor's call.

The supervisor does not directly read fault state. The fault subsystem
alters inputs (sensor readings, watchdog pets) and the supervisor
reacts to those altered inputs through normal mechanisms.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from app.domain.enums import (
    EventSeverity,
    LifecycleState,
    MotionDecision,
    SafetyState,
    SensorType,
)
from app.domain.events import Event, EventBuilder
from app.domain.identifiers import IdGenerator, RunId, ScenarioId
from app.domain.motion import (
    AuthorizedMotionCommand,
    MotionArbitrationResult,
    RequestedMotionCommand,
)
from app.domain.sensors import SensorFrame
from app.domain.time import SimulationClock
from app.safety.arbitration import MotionArbiter
from app.safety.confidence import ConfidenceReport, ConfidenceScorer
from app.safety.freshness import (
    DEFAULT_FRESHNESS_THRESHOLDS,
    FreshnessEvaluator,
    FreshnessReport,
    FreshnessThresholds,
)
from app.safety.transitions import (
    INVALID_TRANSITION_REASON,
    TransitionRequest,
    is_transition_allowed,
)
from app.safety.watchdog import (
    WatchdogConfig,
    WatchdogRegistry,
    WatchdogReport,
)


_SUBSYSTEM = "safety_supervisor"
_NODE = "/rover/safety_supervisor"


@dataclass(frozen=True, slots=True)
class SupervisorInputs:
    """Inputs presented to the supervisor for one evaluation."""

    frame: SensorFrame
    requested_motion: Optional[RequestedMotionCommand]
    operator_activate: bool = False
    operator_estop: bool = False
    operator_recovery: bool = False
    # Two-step armed reset: ``operator_reset`` only clears the E-stop
    # latch if the previous tick saw ``operator_reset_armed`` AND the
    # reset is not unsafe given current freshness / contact. A bare
    # reset pulse is refused with reason ``estop_reset_unsafe``.
    operator_reset_armed: bool = False
    operator_reset: bool = False
    gateway_heartbeat: bool = True
    now_ms: int = 0


@dataclass(slots=True)
class SupervisorEvaluation:
    """The supervisor's per-tick output bundle."""

    next_state: SafetyState
    arbitration: MotionArbitrationResult
    freshness: FreshnessReport
    confidence: ConfidenceReport
    watchdog: WatchdogReport
    events: list[Event] = field(default_factory=list)

    @property
    def authorized(self) -> AuthorizedMotionCommand:
        return self.arbitration.authorized


class SafetySupervisor:
    """The single point of motion authorization for the platform."""

    def __init__(
        self,
        *,
        run_id: RunId,
        scenario_id: ScenarioId,
        clock: SimulationClock,
        id_generator: IdGenerator,
        freshness_thresholds: Optional[dict] = None,
        gateway_watchdog_deadline_ms: int = 500,
        command_lifetime_ms: int = 500,
        recovery_required_warm_ms: int = 1000,
    ) -> None:
        self._clock = clock
        self._state = SafetyState.BOOT
        self._lifecycle = LifecycleState.INACTIVE
        self._builder = EventBuilder(
            run_id=run_id,
            scenario_id=scenario_id,
            clock=clock,
            id_generator=id_generator,
            subsystem=_SUBSYSTEM,
            node=_NODE,
            lifecycle_state=self._lifecycle,
            safety_state=self._state,
        )
        thresholds: dict = (
            freshness_thresholds
            if freshness_thresholds is not None
            else dict(DEFAULT_FRESHNESS_THRESHOLDS)
        )
        if not all(isinstance(t, FreshnessThresholds) for t in thresholds.values()):
            raise TypeError("freshness_thresholds must map SensorType to FreshnessThresholds")
        self._freshness = FreshnessEvaluator(thresholds=thresholds)
        self._confidence_scorer = ConfidenceScorer()
        self._arbiter = MotionArbiter(command_lifetime_ms=command_lifetime_ms)
        self._watchdogs = WatchdogRegistry()
        self._estop_latched = False
        # Latch the prior tick's ``operator_reset_armed`` value so a
        # single-pulse reset is rejected. Cleared when reset is
        # accepted or when the latch is dropped.
        self._reset_armed_prev = False
        self._recovery_warm_ms = recovery_required_warm_ms
        self._recovery_entered_ms: Optional[int] = None
        # Recovery-validation flag: once RECOVERY passes its
        # warm-and-fresh check the supervisor steps through SAFE_STOP;
        # this flag tells SAFE_STOP it may promote back to
        # ACTIVE_NORMAL on the next eligible tick. Cleared when the
        # supervisor enters any ACTIVE_* state or re-enters E_STOP.
        self._recovery_validated = False
        self._gateway_watchdog_name = "gateway_heartbeat"
        self._lidar_watchdog_name = "lidar_freshness"
        self._imu_watchdog_name = "imu_freshness"
        self._encoder_watchdog_name = "encoder_freshness"
        self._gateway_watchdog_deadline = gateway_watchdog_deadline_ms

        # Register watchdogs once at construction time. They are pet
        # later when their corresponding inputs are observed healthy.
        now0 = self._clock.now_ms()
        self._watchdogs.register(
            WatchdogConfig(
                name=self._gateway_watchdog_name,
                deadline_ms=gateway_watchdog_deadline_ms,
                escalation_state=SafetyState.SAFE_STOP,
                reason_code="gateway_silent",
            ),
            now_ms=now0,
        )
        self._watchdogs.register(
            WatchdogConfig(
                name=self._lidar_watchdog_name,
                deadline_ms=DEFAULT_FRESHNESS_THRESHOLDS[SensorType.LIDAR].safe_stop_ms,
                escalation_state=SafetyState.SAFE_STOP,
                reason_code="stale_lidar",
            ),
            now_ms=now0,
        )
        self._watchdogs.register(
            WatchdogConfig(
                name=self._imu_watchdog_name,
                deadline_ms=DEFAULT_FRESHNESS_THRESHOLDS[SensorType.IMU].safe_stop_ms,
                escalation_state=SafetyState.SAFE_STOP,
                reason_code="stale_imu",
            ),
            now_ms=now0,
        )
        self._watchdogs.register(
            WatchdogConfig(
                name=self._encoder_watchdog_name,
                deadline_ms=DEFAULT_FRESHNESS_THRESHOLDS[SensorType.WHEEL_ENCODER].safe_stop_ms,
                escalation_state=SafetyState.SAFE_STOP,
                reason_code="stale_encoders",
            ),
            now_ms=now0,
        )

    # Read-only properties.
    @property
    def safety_state(self) -> SafetyState:
        return self._state

    @property
    def lifecycle_state(self) -> LifecycleState:
        return self._lifecycle

    @property
    def is_estop_latched(self) -> bool:
        return self._estop_latched

    def emit_boot_event(self) -> Event:
        """Emit the canonical ``system_lifecycle.boot`` event."""

        evt = self._builder.build(
            event_type="system_lifecycle.boot",
            severity=EventSeverity.INFO,
            reason_code="boot",
            message="safety supervisor booted",
        )
        return evt

    def evaluate(self, inputs: SupervisorInputs) -> SupervisorEvaluation:
        """Evaluate one tick and return the authorized motion + events."""

        events: list[Event] = []
        now_ms = inputs.now_ms
        # Snapshot prev-armed before any state update; updated at end.
        prev_armed = self._reset_armed_prev

        # 1. Pet the gateway watchdog if heartbeat present.
        if inputs.gateway_heartbeat:
            self._watchdogs.pet(self._gateway_watchdog_name, now_ms=now_ms)

        # 2. Pet sensor watchdogs based on freshness of inputs.
        freshness = self._freshness.evaluate(inputs.frame, now_ms=now_ms)
        if (
            inputs.frame.lidar is not None
            and not freshness.streams[SensorType.LIDAR].is_safe_stop_stale
        ):
            self._watchdogs.pet(self._lidar_watchdog_name, now_ms=now_ms)
        if (
            inputs.frame.imu is not None
            and not freshness.streams[SensorType.IMU].is_safe_stop_stale
        ):
            self._watchdogs.pet(self._imu_watchdog_name, now_ms=now_ms)
        if (
            inputs.frame.encoder is not None
            and not freshness.streams[SensorType.WHEEL_ENCODER].is_safe_stop_stale
        ):
            self._watchdogs.pet(self._encoder_watchdog_name, now_ms=now_ms)

        # 3. Evaluate watchdogs after petting.
        watchdog_report = self._watchdogs.evaluate(now_ms=now_ms)

        # 4. Confidence scoring.
        confidence = self._confidence_scorer.evaluate(
            frame=inputs.frame, freshness=freshness
        )

        # 5. Determine the proposed next state.
        proposed_state, transition_reason, transition_message = self._propose_state(
            inputs=inputs,
            freshness=freshness,
            confidence=confidence,
            watchdog_report=watchdog_report,
            prev_reset_armed=prev_armed,
            refusal_events=events,
        )

        # 6. Apply the proposed transition (with validation and event emission).
        if proposed_state != self._state:
            transition_event = self._maybe_transition(
                target=proposed_state,
                reason_code=transition_reason,
                message=transition_message,
                events=events,
            )
            if transition_event is not None:
                events.append(transition_event)

        # 7. Emit watchdog expiration events.
        for wd in watchdog_report.expired:
            events.append(
                self._builder.build(
                    event_type="watchdog.expired",
                    severity=EventSeverity.ERROR,
                    reason_code=wd.config.reason_code,
                    message=f"watchdog expired: {wd.config.name}",
                    safety_state=self._state,
                    attributes={
                        "watchdog_name": wd.config.name,
                        "deadline_ms": wd.config.deadline_ms,
                        "now_ms": now_ms,
                    },
                )
            )

        # 8. Emit sensor health events for any newly-stale streams.
        for stream in freshness.streams.values():
            if not stream.is_present and stream.reason_code is not None:
                events.append(
                    self._builder.build(
                        event_type="sensor_health.stale",
                        severity=EventSeverity.ERROR,
                        reason_code=stream.reason_code,
                        message=stream.message,
                        confidence_score=confidence.score,
                        safety_state=self._state,
                        attributes={"sensor_type": stream.sensor_type.value, "missing": True},
                    )
                )
            elif stream.is_safe_stop_stale and stream.reason_code is not None:
                events.append(
                    self._builder.build(
                        event_type="sensor_health.stale",
                        severity=EventSeverity.ERROR,
                        reason_code=stream.reason_code,
                        message=stream.message,
                        confidence_score=confidence.score,
                        safety_state=self._state,
                        attributes={
                            "sensor_type": stream.sensor_type.value,
                            "age_ms": stream.age_ms,
                            "level": "safe_stop",
                        },
                    )
                )
            elif not stream.is_fresh and stream.reason_code is not None:
                events.append(
                    self._builder.build(
                        event_type="sensor_health.stale",
                        severity=EventSeverity.WARNING,
                        reason_code=stream.reason_code,
                        message=stream.message,
                        confidence_score=confidence.score,
                        safety_state=self._state,
                        attributes={
                            "sensor_type": stream.sensor_type.value,
                            "age_ms": stream.age_ms,
                            "level": "warn",
                        },
                    )
                )

        if confidence.contact_asserted:
            events.append(
                self._builder.build(
                    event_type="sensor_health.contact",
                    severity=EventSeverity.CRITICAL,
                    reason_code="contact_asserted",
                    message="contact / bumper asserted",
                    confidence_score=confidence.score,
                    safety_state=self._state,
                )
            )

        # 9. Run motion arbitration against the (possibly new) state.
        arbitration = self._arbiter.arbitrate(
            requested=inputs.requested_motion,
            safety_state=self._state,
            now_ms=now_ms,
            operator_estop=inputs.operator_estop or self._estop_latched,
            confidence_score=confidence.score,
        )

        # Emit a motion_arbitration event for every clamp / drop / zero.
        if arbitration.decision in {
            MotionDecision.AUTHORIZED_CLAMPED,
            MotionDecision.REJECTED_ZEROED,
            MotionDecision.REJECTED_EXPIRED,
            MotionDecision.REJECTED_DEGRADED,
        }:
            severity = (
                EventSeverity.NOTICE
                if arbitration.decision == MotionDecision.AUTHORIZED_CLAMPED
                else EventSeverity.WARNING
            )
            events.append(
                self._builder.build(
                    event_type=self._arbitration_event_type(arbitration),
                    severity=severity,
                    reason_code=arbitration.reason.value,
                    message=self._arbitration_message(arbitration),
                    requested_motion=arbitration.requested,
                    final_motion=arbitration.authorized,
                    confidence_score=confidence.score,
                    safety_state=self._state,
                )
            )

        evaluation = SupervisorEvaluation(
            next_state=self._state,
            arbitration=arbitration,
            freshness=freshness,
            confidence=confidence,
            watchdog=watchdog_report,
            events=events,
        )
        # Carry the *current* tick's armed pulse forward for the next
        # tick to consume. A scenario must drive ``operator_reset_armed``
        # for at least one tick BEFORE pulsing ``operator_reset``.
        self._reset_armed_prev = inputs.operator_reset_armed
        return evaluation

    # ------------------------------------------------------------------
    # State machine helpers.
    # ------------------------------------------------------------------
    def _propose_state(
        self,
        *,
        inputs: SupervisorInputs,
        freshness: FreshnessReport,
        confidence: ConfidenceReport,
        watchdog_report: WatchdogReport,
        prev_reset_armed: bool,
        refusal_events: list[Event],
    ) -> tuple[SafetyState, str, str]:
        # 1. E-stop is highest priority.
        if inputs.operator_estop:
            self._estop_latched = True
            self._recovery_validated = False
            return (SafetyState.E_STOP_LATCHED, "operator_estop", "E-stop asserted by operator")

        if self._estop_latched:
            if inputs.operator_reset:
                # Two-step armed reset, plus a safety-conditions gate.
                reset_unsafe = (
                    freshness.any_safe_stop
                    or freshness.any_missing_required
                    or confidence.contact_asserted
                )
                if not prev_reset_armed or reset_unsafe:
                    refusal_events.append(
                        self._builder.build(
                            event_type="safety_transition.refused",
                            severity=EventSeverity.ERROR,
                            reason_code="estop_reset_unsafe",
                            message=(
                                "operator_reset refused: not armed by prior tick"
                                if not prev_reset_armed
                                else "operator_reset refused: unsafe conditions"
                            ),
                            safety_state=self._state,
                            attributes={
                                "prev_reset_armed": prev_reset_armed,
                                "any_safe_stop": freshness.any_safe_stop,
                                "any_missing_required": freshness.any_missing_required,
                                "contact_asserted": confidence.contact_asserted,
                            },
                        )
                    )
                    return (
                        SafetyState.E_STOP_LATCHED,
                        "estop_reset_unsafe",
                        "operator_reset refused",
                    )
                self._estop_latched = False
                self._recovery_entered_ms = inputs.now_ms
                self._recovery_validated = False
                return (SafetyState.RECOVERY, "operator_reset", "operator reset; entering RECOVERY")
            return (SafetyState.E_STOP_LATCHED, "estop_held", "E-stop remains latched")

        # 2. Watchdog escalations.
        wd_state = watchdog_report.highest_escalation()
        if wd_state is not None and wd_state != self._state:
            return (
                wd_state,
                watchdog_report.expired_reason_codes()[0]
                if watchdog_report.expired_reason_codes()
                else "watchdog_expiration",
                "watchdog escalation",
            )

        # 3. Contact assertion forces SAFE_STOP.
        if confidence.contact_asserted:
            return (SafetyState.SAFE_STOP, "contact_asserted", "contact asserted; entering SAFE_STOP")

        # 4. Freshness escalations.
        if freshness.any_safe_stop or freshness.any_missing_required:
            reason = (freshness.safe_stop_reason_codes() or freshness.stale_reason_codes() or ("stale_input",))[0]
            return (SafetyState.SAFE_STOP, reason, "stale or missing required input")

        # 5. Recovery flow.
        if self._state == SafetyState.SAFE_STOP and inputs.operator_recovery:
            self._recovery_entered_ms = inputs.now_ms
            return (SafetyState.RECOVERY, "operator_recovery", "operator initiated recovery")

        if self._state == SafetyState.RECOVERY:
            warm_elapsed = inputs.now_ms - (self._recovery_entered_ms or inputs.now_ms)
            if (
                not freshness.any_safe_stop
                and not freshness.any_missing_required
                and not freshness.any_warn
                and warm_elapsed >= self._recovery_warm_ms
                and confidence.score >= 0.6
            ):
                # Two-step reactivation: validation step lands in
                # SAFE_STOP; promotion to ACTIVE_NORMAL happens on the
                # next tick when ``_recovery_validated`` is observed.
                self._recovery_validated = True
                return (
                    SafetyState.SAFE_STOP,
                    "recovery_validated",
                    "recovery validation passed; awaiting promotion",
                )
            if freshness.any_safe_stop or freshness.any_missing_required:
                return (SafetyState.SAFE_STOP, "recovery_failed", "recovery validation failed")
            return (SafetyState.RECOVERY, "recovery_in_progress", "recovery in progress")

        # Recovery-validated promotion out of SAFE_STOP. Requires inputs
        # to still be healthy on this tick — if not, hold SAFE_STOP and
        # keep the flag (we re-validate next tick).
        if (
            self._state == SafetyState.SAFE_STOP
            and self._recovery_validated
            and not freshness.any_safe_stop
            and not freshness.any_missing_required
            and not freshness.any_warn
            and not confidence.contact_asserted
        ):
            self._recovery_validated = False
            return (
                SafetyState.ACTIVE_NORMAL,
                "recovery_promoted",
                "promotion from SAFE_STOP after recovery validation",
            )

        # 6. Activation flow.
        if self._state in {SafetyState.BOOT, SafetyState.INACTIVE}:
            if (
                inputs.operator_activate
                and not freshness.any_safe_stop
                and not freshness.any_missing_required
                and not freshness.any_warn
            ):
                return (SafetyState.ACTIVE_NORMAL, "operator_activate", "operator activation accepted")
            if not freshness.any_safe_stop and not freshness.any_missing_required and self._state == SafetyState.BOOT:
                return (SafetyState.INACTIVE, "boot_complete", "boot complete; awaiting activation")

        # 7. Active state choices based on confidence and freshness.
        if self._state in {
            SafetyState.ACTIVE_NORMAL,
            SafetyState.ACTIVE_RESTRICTED,
            SafetyState.ACTIVE_DEGRADED,
        }:
            if confidence.sensor_disagreement or confidence.bias_detected or freshness.any_warn:
                return (SafetyState.ACTIVE_DEGRADED, self._degrade_reason(confidence, freshness), "degraded inputs detected")
            if confidence.score < 0.7:
                return (SafetyState.ACTIVE_RESTRICTED, "confidence_drop", "reduced confidence")
            return (SafetyState.ACTIVE_NORMAL, "nominal", "nominal operation")

        # 8. Default: hold.
        return (self._state, "hold", "no transition")

    @staticmethod
    def _degrade_reason(confidence: ConfidenceReport, freshness: FreshnessReport) -> str:
        if confidence.sensor_disagreement:
            return "sensor_disagreement"
        if confidence.bias_detected:
            return "imu_bias"
        if freshness.stale_reason_codes():
            return freshness.stale_reason_codes()[0]
        return "confidence_drop"

    def _maybe_transition(
        self,
        *,
        target: SafetyState,
        reason_code: str,
        message: str,
        events: list[Event],
    ) -> Optional[Event]:
        if target == self._state:
            return None
        if not is_transition_allowed(self._state, target):
            # Refuse and emit an explicit rejection event; do not change state.
            return self._builder.build(
                event_type="safety_transition.refused",
                severity=EventSeverity.ERROR,
                reason_code=INVALID_TRANSITION_REASON,
                message=f"refused {self._state.value} -> {target.value}: {message}",
                safety_state=self._state,
                attributes={
                    "from_state": self._state.value,
                    "to_state": target.value,
                    "underlying_reason": reason_code,
                },
            )

        previous = self._state
        self._state = target
        self._builder.update_safety_state(target)
        if target == SafetyState.E_STOP_LATCHED:
            severity = EventSeverity.CRITICAL
        elif target == SafetyState.SAFE_STOP:
            severity = EventSeverity.ERROR
        elif target == SafetyState.ACTIVE_DEGRADED:
            severity = EventSeverity.WARNING
        else:
            severity = EventSeverity.INFO

        if target == SafetyState.RECOVERY:
            self._recovery_entered_ms = self._clock.now_ms()

        return self._builder.build(
            event_type="safety_transition.entered",
            severity=severity,
            reason_code=reason_code,
            message=f"{previous.value} -> {target.value}: {message}",
            safety_state=target,
            attributes={"from_state": previous.value, "to_state": target.value},
        )

    @staticmethod
    def _arbitration_event_type(arbitration: MotionArbitrationResult) -> str:
        if arbitration.decision == MotionDecision.AUTHORIZED_CLAMPED:
            return "motion_arbitration.clamped"
        if arbitration.decision == MotionDecision.REJECTED_EXPIRED:
            return "motion_arbitration.dropped"
        if arbitration.decision in {MotionDecision.REJECTED_ZEROED, MotionDecision.REJECTED_DEGRADED}:
            return "motion_arbitration.zeroed"
        return "motion_arbitration.clamped"

    @staticmethod
    def _arbitration_message(arbitration: MotionArbitrationResult) -> str:
        if arbitration.decision == MotionDecision.AUTHORIZED_CLAMPED:
            return f"authorized clamped to limits: {arbitration.reason.value}"
        if arbitration.decision == MotionDecision.REJECTED_EXPIRED:
            return "request expired; authorized zero motion"
        if arbitration.decision == MotionDecision.REJECTED_DEGRADED:
            return "confidence below floor; authorized zero motion"
        return f"authorized zero motion: {arbitration.reason.value}"
