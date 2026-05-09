"""Controlled vocabularies used across the platform.

These enums are the *only* legal values for the corresponding fields in the
event envelope, the motion arbitration record, and the replay manifest.
Producers must not invent new values at runtime.
"""

from __future__ import annotations

from enum import Enum


class SafetyState(str, Enum):
    """Safety states defined in docs/SAFETY_MODEL.md.

    The order is significant: states later in the enum are more restrictive.
    Comparisons use :meth:`is_more_restrictive_than` rather than ``<`` to
    avoid surprising orderings.
    """

    BOOT = "BOOT"
    INACTIVE = "INACTIVE"
    ACTIVE_NORMAL = "ACTIVE_NORMAL"
    ACTIVE_RESTRICTED = "ACTIVE_RESTRICTED"
    ACTIVE_DEGRADED = "ACTIVE_DEGRADED"
    SAFE_STOP = "SAFE_STOP"
    E_STOP_LATCHED = "E_STOP_LATCHED"
    RECOVERY = "RECOVERY"

    @property
    def is_active(self) -> bool:
        """True for states that authorize non-zero motion."""
        return self in _ACTIVE_STATES

    @property
    def authorizes_motion(self) -> bool:
        """True if the state may authorize non-zero motion at all."""
        return self in _ACTIVE_STATES

    @property
    def forces_zero_motion(self) -> bool:
        """True if the state must force authorized motion to zero."""
        return self in _ZERO_MOTION_STATES

    def is_more_restrictive_than(self, other: "SafetyState") -> bool:
        return _RESTRICTION_ORDER[self] > _RESTRICTION_ORDER[other]


_ACTIVE_STATES: frozenset[SafetyState] = frozenset(
    {
        SafetyState.ACTIVE_NORMAL,
        SafetyState.ACTIVE_RESTRICTED,
        SafetyState.ACTIVE_DEGRADED,
    }
)

_ZERO_MOTION_STATES: frozenset[SafetyState] = frozenset(
    {
        SafetyState.BOOT,
        SafetyState.INACTIVE,
        SafetyState.SAFE_STOP,
        SafetyState.E_STOP_LATCHED,
        SafetyState.RECOVERY,
    }
)

# Higher number == more restrictive. Used for "never go less restrictive
# automatically" checks.
_RESTRICTION_ORDER: dict[SafetyState, int] = {
    SafetyState.ACTIVE_NORMAL: 0,
    SafetyState.ACTIVE_RESTRICTED: 1,
    SafetyState.ACTIVE_DEGRADED: 2,
    SafetyState.BOOT: 3,
    SafetyState.INACTIVE: 3,
    SafetyState.RECOVERY: 4,
    SafetyState.SAFE_STOP: 5,
    SafetyState.E_STOP_LATCHED: 6,
}


class LifecycleState(str, Enum):
    """ROS 2-style lifecycle states for the supervisor and adapters."""

    UNCONFIGURED = "unconfigured"
    INACTIVE = "inactive"
    ACTIVE = "active"
    FINALIZED = "finalized"
    ERROR = "error"


class SensorType(str, Enum):
    LIDAR = "lidar"
    IMU = "imu"
    WHEEL_ENCODER = "wheel_encoder"
    CONTACT = "contact"


class SensorStatus(str, Enum):
    HEALTHY = "healthy"
    STALE = "stale"
    DISAGREEING = "disagreeing"
    BIASED = "biased"
    DISCONNECTED = "disconnected"


class FaultType(str, Enum):
    """Fault classes defined in docs/FAULT_INJECTION.md section 4."""

    STALE_LIDAR = "stale_lidar"
    ENCODER_DRIFT = "encoder_drift"
    IMU_BIAS = "imu_bias"
    BRIDGE_DISCONNECT = "bridge_disconnect"
    COMMAND_TIMEOUT = "command_timeout"
    WATCHDOG_EXPIRATION = "watchdog_expiration"
    PACKET_DELAY = "packet_delay"
    SENSOR_DISAGREEMENT = "sensor_disagreement"
    WHEEL_SLIP = "wheel_slip"


class FaultStatus(str, Enum):
    """Fault lifecycle phases (docs/FAULT_INJECTION.md section 5)."""

    CONFIGURED = "configured"
    ARMED = "armed"
    FIRED = "fired"
    CLEARED = "cleared"


class EventSeverity(str, Enum):
    """Severity vocabulary (docs/EVENT_MODEL.md section 3)."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    NOTICE = "NOTICE"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class EventCategory(str, Enum):
    """Event categories (docs/EVENT_MODEL.md section 5)."""

    SYSTEM_LIFECYCLE = "system_lifecycle"
    SENSOR_HEALTH = "sensor_health"
    STATE_ESTIMATION = "state_estimation"
    SAFETY_TRANSITION = "safety_transition"
    MOTION_ARBITRATION = "motion_arbitration"
    FAULT_INJECTION = "fault_injection"
    WATCHDOG = "watchdog"
    REPLAY = "replay"
    OPERATOR_ACTION = "operator_action"
    # Phase 2 additions.
    MISSION_LIFECYCLE = "mission_lifecycle"
    MISSION_WAYPOINT = "mission_waypoint"
    MISSION_RECOVERY = "mission_recovery"
    WORLD_MODEL = "world_model"


class MotionDecision(str, Enum):
    """Outcome of a single arbitration evaluation."""

    AUTHORIZED = "authorized"
    AUTHORIZED_CLAMPED = "authorized_clamped"
    REJECTED_ZEROED = "rejected_zeroed"
    REJECTED_EXPIRED = "rejected_expired"
    REJECTED_DEGRADED = "rejected_degraded"


class MotionConstraintReason(str, Enum):
    """Stable reason codes for motion arbitration outcomes.

    Values must be kept in sync with the reason-code vocabulary in
    docs/EVENT_MODEL.md section 6.
    """

    NONE = "none"
    VELOCITY_CLAMP = "velocity_clamp"
    ANGULAR_CLAMP = "angular_clamp"
    ACCELERATION_CLAMP = "acceleration_clamp"
    SAFE_STOP_ZERO = "safe_stop_zero"
    E_STOP_ZERO = "e_stop_zero"
    DEGRADED_ZERO = "degraded_zero"
    BOOT_ZERO = "boot_zero"
    INACTIVE_ZERO = "inactive_zero"
    RECOVERY_ZERO = "recovery_zero"
    COMMAND_EXPIRED = "command_expired"
    STALE_INPUT = "stale_input"
    OPERATOR_ESTOP = "operator_estop"


class ScenarioStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    ABORTED = "aborted"
    FAILED = "failed"


class ReplayStatus(str, Enum):
    OPEN = "open"
    FINALIZED = "finalized"
    INVALID = "invalid"
