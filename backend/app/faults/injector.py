"""Deterministic fault injector.

The injector consumes a list of :class:`FaultProfile` configurations and,
on every tick, produces:

* a :class:`FaultEffect` describing how the next sensor frame and the
  gateway/watchdog signals should be perturbed,
* a list of :class:`Event` records describing fault arming, firing, and
  clearing.

The injector itself **never** sets safety state and never consumes
``/safety/state``. The supervisor reacts to the perturbed inputs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from app.domain.enums import EventSeverity, FaultStatus, FaultType
from app.domain.events import Event, EventBuilder
from app.domain.faults import FaultProfile, FaultRuntimeState
from app.domain.identifiers import IdGenerator, RunId, ScenarioId
from app.domain.time import SimulationClock
from app.faults.models import FaultEffect


_SUBSYSTEM = "fault_injection"
_NODE = "/rover/fault_injection"


@dataclass(slots=True)
class InjectionContext:
    """Carry-over state used by faults that span multiple ticks."""

    accumulated_drift: float = 0.0
    last_evaluated_ms: int = 0


@dataclass(slots=True)
class InjectionOutput:
    effect: FaultEffect
    events: list[Event]
    active_faults: tuple[FaultRuntimeState, ...]


class FaultInjector:
    """Tracks fault lifecycle and produces deterministic perturbations."""

    def __init__(
        self,
        *,
        run_id: RunId,
        scenario_id: ScenarioId,
        clock: SimulationClock,
        id_generator: IdGenerator,
        profiles: Iterable[FaultProfile] = (),
        scenario_duration_ms: int = 0,
    ) -> None:
        self._builder = EventBuilder(
            run_id=run_id,
            scenario_id=scenario_id,
            clock=clock,
            id_generator=id_generator,
            subsystem=_SUBSYSTEM,
            node=_NODE,
        )
        self._faults: list[FaultRuntimeState] = []
        self._scenario_duration_ms = scenario_duration_ms
        self._context = InjectionContext()
        for profile in profiles:
            self._faults.append(FaultRuntimeState(profile=profile, status=FaultStatus.CONFIGURED))

    @property
    def active_faults(self) -> tuple[FaultRuntimeState, ...]:
        return tuple(f for f in self._faults if f.status == FaultStatus.FIRED)

    def configured_fault_ids(self) -> tuple[str, ...]:
        return tuple(f.profile.fault_id for f in self._faults)

    def emit_arming(self) -> list[Event]:
        """Move every CONFIGURED fault to ARMED at scenario start."""

        events: list[Event] = []
        for i, fault in enumerate(self._faults):
            if fault.status == FaultStatus.CONFIGURED:
                self._faults[i] = fault.transition(new_status=FaultStatus.ARMED, now_ms=0)
                events.append(self._build_event(self._faults[i], "armed", EventSeverity.INFO))
        return events

    def evaluate(self, *, now_ms: int) -> InjectionOutput:
        """Update fault lifecycle and produce the effect for this tick."""

        events: list[Event] = []

        # Move ARMED faults to FIRED at activation time.
        for i, fault in enumerate(self._faults):
            if fault.status == FaultStatus.ARMED and now_ms >= fault.profile.activation_ms:
                self._faults[i] = fault.transition(new_status=FaultStatus.FIRED, now_ms=now_ms)
                events.append(self._build_event(self._faults[i], "fired", EventSeverity.WARNING))

        # Move FIRED faults to CLEARED if their duration has elapsed.
        for i, fault in enumerate(self._faults):
            if fault.status == FaultStatus.FIRED and not fault.profile.runs_until_end_of_scenario:
                if now_ms >= fault.profile.activation_ms + fault.profile.duration_ms:
                    self._faults[i] = fault.transition(new_status=FaultStatus.CLEARED, now_ms=now_ms)
                    events.append(self._build_event(self._faults[i], "cleared", EventSeverity.INFO))

        # Compose the cumulative effect from active faults.
        effect = FaultEffect()
        for fault in self.active_faults:
            effect = effect.merge(self._effect_for(fault, now_ms=now_ms))

        self._context.last_evaluated_ms = now_ms
        return InjectionOutput(effect=effect, events=events, active_faults=self.active_faults)

    def _effect_for(self, fault: FaultRuntimeState, *, now_ms: int) -> FaultEffect:
        params = fault.profile.parameters
        ftype = fault.profile.fault_type
        if ftype == FaultType.STALE_LIDAR:
            mode = params.get("mode", "drop")
            if mode == "delay":
                return FaultEffect(delay_lidar_ms=int(params.get("delay_ms", 300)),
                                   notes=(f"stale_lidar:delay({params.get('delay_ms', 300)}ms)",))
            return FaultEffect(drop_lidar=True, notes=("stale_lidar:drop",))

        if ftype == FaultType.ENCODER_DRIFT:
            rate = float(params.get("drift_rate_mps", 0.05))
            return FaultEffect(encoder_drift_rate=rate, notes=(f"encoder_drift:{rate:+.3f} m/s",))

        if ftype == FaultType.IMU_BIAS:
            bias = float(params.get("bias_rad_s", 0.25))
            return FaultEffect(imu_bias_offset=bias, notes=(f"imu_bias:{bias:+.3f} rad/s",))

        if ftype == FaultType.BRIDGE_DISCONNECT:
            return FaultEffect(bridge_disconnected=True, notes=("bridge_disconnect",))

        if ftype == FaultType.COMMAND_TIMEOUT:
            mode = params.get("mode", "silent_consumer")
            return FaultEffect(
                suppress_gateway_heartbeat=True,
                delayed_command=True,
                notes=(f"command_timeout:{mode}",),
            )

        if ftype == FaultType.WATCHDOG_EXPIRATION:
            target = str(params.get("watchdog_name", fault.profile.target))
            return FaultEffect(watchdog_targets=(target,), notes=(f"watchdog_expiration:{target}",))

        if ftype == FaultType.PACKET_DELAY:
            return FaultEffect(
                delay_lidar_ms=int(params.get("delay_ms", 300)),
                notes=(f"packet_delay:{params.get('delay_ms', 300)}ms",),
            )

        if ftype == FaultType.SENSOR_DISAGREEMENT:
            offset = float(params.get("angular_offset_rad_s", 0.6))
            return FaultEffect(forced_disagreement_angular=offset, notes=(f"sensor_disagreement:{offset:+.3f}",))

        if ftype == FaultType.WHEEL_SLIP:
            slip = float(params.get("slip_factor", 0.4))
            return FaultEffect(wheel_slip_factor=slip, notes=(f"wheel_slip:{slip:.3f}",))

        return FaultEffect()  # pragma: no cover - defensive

    def _build_event(self, fault: FaultRuntimeState, phase: str, severity: EventSeverity) -> Event:
        if phase == "armed":
            event_type = "fault_injection.armed"
            reason_code = "fault_armed"
            message = f"fault armed: {fault.profile.fault_id} ({fault.profile.fault_type.value})"
        elif phase == "fired":
            event_type = "fault_injection.fired"
            reason_code = "fault_fired"
            message = f"fault fired: {fault.profile.fault_id} ({fault.profile.fault_type.value})"
        elif phase == "cleared":
            event_type = "fault_injection.cleared"
            reason_code = "fault_cleared"
            message = f"fault cleared: {fault.profile.fault_id} ({fault.profile.fault_type.value})"
        else:  # pragma: no cover - defensive
            raise ValueError(f"unknown phase: {phase}")
        return self._builder.build(
            event_type=event_type,
            severity=severity,
            reason_code=reason_code,
            message=message,
            attributes={
                "fault_id": fault.profile.fault_id,
                "fault_type": fault.profile.fault_type.value,
                "target": fault.profile.target,
                "activation_ms": fault.profile.activation_ms,
                "duration_ms": fault.profile.duration_ms,
                "parameters": dict(fault.profile.parameters),
            },
        )
