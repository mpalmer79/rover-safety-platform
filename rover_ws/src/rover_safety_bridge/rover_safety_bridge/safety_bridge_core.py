"""Pure-logic core of the safety bridge.

The core hosts the deterministic ``SafetySupervisor`` from
:mod:`app.safety` and converts:

* ROS sensor messages and a requested ``geometry_msgs/Twist`` into
  :class:`SupervisorInputs`,
* a :class:`SupervisorEvaluation` into outbound ROS payloads
  (``/cmd_vel_authorized``, :class:`SafetyState`, :class:`MotionAuthorization`,
  ``Event`` records that the node serializes to JSON for ``/safety/events``).

The core is deliberately framework-light. It does not import ``rclpy``;
the node module owns all ROS plumbing. This separation keeps the core
unit-testable in environments without ROS installed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from app.domain.enums import LifecycleState, SafetyState, SensorStatus, SensorType
from app.domain.events import Event
from app.domain.identifiers import IdGenerator, RunId, ScenarioId, UuidIdGenerator
from app.domain.motion import (
    AuthorizedMotionCommand,
    RequestedMotionCommand,
)
from app.domain.sensors import (
    ContactReading,
    EncoderReading,
    IMUReading,
    LiDARReading,
    SensorFrame,
)
from app.domain.time import SimulationClock, Timestamp
from app.safety.supervisor import (
    SafetySupervisor,
    SupervisorEvaluation,
    SupervisorInputs,
)


# ---------------------------------------------------------------------------
# Lightweight value objects describing inbound ROS messages.
#
# The bridge does not depend on rclpy, so these dataclasses are the
# narrow API the node hands to the core. The node populates them from
# the corresponding sensor_msgs / nav_msgs / geometry_msgs values.
# ---------------------------------------------------------------------------


# NOTE (#15): ``timestamp_ms`` is the SUBSCRIBER receive time (the
# bridge's clock at message arrival), NOT the sender's
# ``header.stamp``. Freshness is measured against receive-time only;
# a sender that claims a future stamp cannot defeat the watchdog.
# ``sender_stamp_ms`` is retained for diagnostics — never used by
# freshness or arbitration.


@dataclass(frozen=True)
class IncomingScan:
    timestamp_ms: int  # receive-time at subscriber
    sequence_number: int
    min_range_m: float
    max_range_m: float
    mean_range_m: float
    point_count: int
    sender_stamp_ms: int = 0  # diagnostic only; do not use for freshness


@dataclass(frozen=True)
class IncomingImu:
    timestamp_ms: int  # receive-time at subscriber
    sequence_number: int
    angular_velocity_z: float
    linear_accel_x: float
    linear_accel_y: float
    orientation_rad: float
    sender_stamp_ms: int = 0  # diagnostic only


@dataclass(frozen=True)
class IncomingOdom:
    timestamp_ms: int  # receive-time at subscriber
    sequence_number: int
    derived_linear_velocity: float
    derived_angular_velocity: float
    pose_x: float
    pose_y: float
    heading_rad: float
    sender_stamp_ms: int = 0  # diagnostic only


@dataclass(frozen=True)
class IncomingContact:
    timestamp_ms: int  # receive-time at subscriber
    sequence_number: int
    asserted: bool
    sender_stamp_ms: int = 0  # diagnostic only


@dataclass(frozen=True)
class IncomingRequestedMotion:
    timestamp_ms: int
    linear_velocity: float
    angular_velocity: float
    source: str = "ros.cmd_vel_requested"
    lifetime_ms: int = 500


@dataclass(frozen=True)
class OperatorPulses:
    activate: bool = False
    estop: bool = False
    recovery: bool = False
    reset: bool = False
    # Two-step armed reset (#3 + #4): the supervisor requires
    # ``reset_armed=True`` on the prior tick before it will accept
    # ``reset=True``.
    reset_armed: bool = False


# ---------------------------------------------------------------------------
# Outbound publication container.
# ---------------------------------------------------------------------------


@dataclass
class OutboundPublication:
    """What the node should publish for a single evaluation cycle."""

    authorized: AuthorizedMotionCommand
    safety_state: SafetyState
    lifecycle_state: LifecycleState
    estop_latched: bool
    confidence_score: float
    requested_motion: Optional[RequestedMotionCommand]
    transition_events: list[Event] = field(default_factory=list)
    motion_arbitration_events: list[Event] = field(default_factory=list)
    sensor_health_events: list[Event] = field(default_factory=list)
    other_events: list[Event] = field(default_factory=list)

    @property
    def all_events(self) -> list[Event]:
        return (
            list(self.transition_events)
            + list(self.motion_arbitration_events)
            + list(self.sensor_health_events)
            + list(self.other_events)
        )


# ---------------------------------------------------------------------------
# A SimulationClock implementation that the node can advance from a ROS
# clock. Implemented inline so it stays decoupled from app.domain.time.
# ---------------------------------------------------------------------------


class HostedClock:
    """A clock the bridge node drives from ``node.get_clock()``."""

    def __init__(self) -> None:
        self._sim_ns = 0

    def set_now_ns(self, value: int) -> None:
        if value < 0:
            raise ValueError("clock value must be non-negative")
        self._sim_ns = int(value)

    # SimulationClock protocol --------------------------------------
    def now_ns(self) -> int:
        return self._sim_ns

    def now_ms(self) -> int:
        return self._sim_ns // 1_000_000

    def advance_ms(self, delta_ms: int) -> None:
        if delta_ms < 0:
            raise ValueError("delta_ms must be non-negative")
        self._sim_ns += int(delta_ms) * 1_000_000

    def stamp(self) -> Timestamp:
        from datetime import datetime, timezone

        seconds = self._sim_ns / 1_000_000_000
        wall = (
            datetime.fromtimestamp(seconds, tz=timezone.utc)
            .isoformat(timespec="microseconds")
            .replace("+00:00", "Z")
        )
        return Timestamp(wall=wall, sim_time_ns=self._sim_ns)


# ---------------------------------------------------------------------------
# The bridge core itself.
# ---------------------------------------------------------------------------


_LIDAR_SOURCE = "ros.scan"
_IMU_SOURCE = "ros.imu"
_ODOM_SOURCE = "ros.odom"
_CONTACT_SOURCE = "ros.contact"


class SafetyBridgeCore:
    """Per-cycle core: build inputs, run the supervisor, summarise outputs."""

    def __init__(
        self,
        *,
        run_id: RunId,
        scenario_id: ScenarioId,
        clock: Optional[SimulationClock] = None,
        id_generator: Optional[IdGenerator] = None,
    ) -> None:
        self._clock = clock if clock is not None else HostedClock()
        self._ids = id_generator if id_generator is not None else UuidIdGenerator()
        self._supervisor = SafetySupervisor(
            run_id=run_id,
            scenario_id=scenario_id,
            clock=self._clock,
            id_generator=self._ids,
        )
        self._latest_scan: Optional[IncomingScan] = None
        self._latest_imu: Optional[IncomingImu] = None
        self._latest_odom: Optional[IncomingOdom] = None
        self._latest_contact: Optional[IncomingContact] = None
        self._latest_request: Optional[IncomingRequestedMotion] = None

    # --- caches -------------------------------------------------------
    def update_clock(self, *, now_ns: int) -> None:
        if isinstance(self._clock, HostedClock):
            self._clock.set_now_ns(now_ns)

    def cache_scan(self, scan: IncomingScan) -> None:
        self._latest_scan = scan

    def cache_imu(self, imu: IncomingImu) -> None:
        self._latest_imu = imu

    def cache_odom(self, odom: IncomingOdom) -> None:
        self._latest_odom = odom

    def cache_contact(self, contact: IncomingContact) -> None:
        self._latest_contact = contact

    def cache_request(self, request: IncomingRequestedMotion) -> None:
        self._latest_request = request

    @property
    def supervisor(self) -> SafetySupervisor:
        return self._supervisor

    @property
    def clock(self) -> SimulationClock:
        return self._clock

    def emit_boot_event(self) -> Event:
        return self._supervisor.emit_boot_event()

    # --- evaluate -----------------------------------------------------
    def evaluate(
        self,
        *,
        operator: OperatorPulses,
        gateway_heartbeat: bool = True,
    ) -> OutboundPublication:
        now_ms = self._clock.now_ms()
        frame = SensorFrame(
            lidar=self._build_lidar(now_ms),
            imu=self._build_imu(now_ms),
            encoder=self._build_encoder(now_ms),
            contact=self._build_contact(now_ms),
        )
        request = self._build_request(now_ms)
        inputs = SupervisorInputs(
            frame=frame,
            requested_motion=request,
            operator_activate=operator.activate,
            operator_estop=operator.estop,
            operator_recovery=operator.recovery,
            operator_reset_armed=operator.reset_armed,
            operator_reset=operator.reset,
            gateway_heartbeat=gateway_heartbeat,
            now_ms=now_ms,
        )
        evaluation: SupervisorEvaluation = self._supervisor.evaluate(inputs)
        return _summarise(evaluation, request, self._supervisor)

    # --- frame builders ----------------------------------------------
    def _build_lidar(self, now_ms: int) -> Optional[LiDARReading]:
        if self._latest_scan is None:
            return None
        s = self._latest_scan
        return LiDARReading(
            sensor_id="rover/lidar",
            sensor_type=SensorType.LIDAR,
            timestamp_ms=s.timestamp_ms,
            status=SensorStatus.HEALTHY,
            confidence=0.9,
            source=_LIDAR_SOURCE,
            sequence_number=s.sequence_number,
            min_range_m=s.min_range_m,
            max_range_m=s.max_range_m,
            mean_range_m=s.mean_range_m,
            point_count=s.point_count,
        )

    def _build_imu(self, now_ms: int) -> Optional[IMUReading]:
        if self._latest_imu is None:
            return None
        i = self._latest_imu
        return IMUReading(
            sensor_id="rover/imu",
            sensor_type=SensorType.IMU,
            timestamp_ms=i.timestamp_ms,
            status=SensorStatus.HEALTHY,
            confidence=0.85,
            source=_IMU_SOURCE,
            sequence_number=i.sequence_number,
            angular_velocity_z=i.angular_velocity_z,
            linear_accel_x=i.linear_accel_x,
            linear_accel_y=i.linear_accel_y,
            orientation_rad=i.orientation_rad,
        )

    def _build_encoder(self, now_ms: int) -> Optional[EncoderReading]:
        if self._latest_odom is None:
            return None
        o = self._latest_odom
        return EncoderReading(
            sensor_id="rover/encoders",
            sensor_type=SensorType.WHEEL_ENCODER,
            timestamp_ms=o.timestamp_ms,
            status=SensorStatus.HEALTHY,
            confidence=0.9,
            source=_ODOM_SOURCE,
            sequence_number=o.sequence_number,
            derived_linear_velocity=o.derived_linear_velocity,
            derived_angular_velocity=o.derived_angular_velocity,
        )

    def _build_contact(self, now_ms: int) -> Optional[ContactReading]:
        if self._latest_contact is None:
            return None
        c = self._latest_contact
        return ContactReading(
            sensor_id="rover/contact",
            sensor_type=SensorType.CONTACT,
            timestamp_ms=c.timestamp_ms,
            status=SensorStatus.HEALTHY,
            confidence=1.0,
            source=_CONTACT_SOURCE,
            sequence_number=c.sequence_number,
            activated=c.asserted,
            contact_count=1 if c.asserted else 0,
        )

    def _build_request(self, now_ms: int) -> Optional[RequestedMotionCommand]:
        if self._latest_request is None:
            return None
        r = self._latest_request
        # If the request is older than its lifetime, the supervisor's
        # arbiter will reject it as expired. We pass it through and let
        # the arbiter decide.
        return RequestedMotionCommand(
            linear_velocity=r.linear_velocity,
            angular_velocity=r.angular_velocity,
            source=r.source,
            issued_at_ms=r.timestamp_ms,
            expires_at_ms=r.timestamp_ms + max(1, r.lifetime_ms),
        )


# ---------------------------------------------------------------------------
# Helpers.
# ---------------------------------------------------------------------------


def _summarise(
    evaluation: SupervisorEvaluation,
    request: Optional[RequestedMotionCommand],
    supervisor: SafetySupervisor,
) -> OutboundPublication:
    transition_events: list[Event] = []
    motion_events: list[Event] = []
    sensor_events: list[Event] = []
    other_events: list[Event] = []
    for evt in evaluation.events:
        if evt.event_type.startswith("safety_transition."):
            transition_events.append(evt)
        elif evt.event_type.startswith("motion_arbitration."):
            motion_events.append(evt)
        elif evt.event_type.startswith("sensor_health."):
            sensor_events.append(evt)
        else:
            other_events.append(evt)

    return OutboundPublication(
        authorized=evaluation.authorized,
        safety_state=supervisor.safety_state,
        lifecycle_state=supervisor.lifecycle_state,
        estop_latched=supervisor.is_estop_latched,
        confidence_score=evaluation.confidence.score,
        requested_motion=request,
        transition_events=transition_events,
        motion_arbitration_events=motion_events,
        sensor_health_events=sensor_events,
        other_events=other_events,
    )
