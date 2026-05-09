"""Domain models for the rover safety platform.

Pure value objects with no dependencies outside the standard library.
Anything that mutates state at runtime lives outside this package.
"""

from app.domain.enums import (
    EventCategory,
    EventSeverity,
    FaultStatus,
    FaultType,
    LifecycleState,
    MotionConstraintReason,
    MotionDecision,
    ReplayStatus,
    SafetyState,
    ScenarioStatus,
    SensorStatus,
    SensorType,
)
from app.domain.events import Event, EventBuilder
from app.domain.faults import FaultProfile, FaultRuntimeState
from app.domain.identifiers import EventId, RunId, ScenarioId, SequentialIdGenerator, UuidIdGenerator
from app.domain.motion import (
    AuthorizedMotionCommand,
    MotionArbitrationResult,
    MotionCommand,
    MotionLimits,
    RequestedMotionCommand,
    motion_limits_for_state,
)
from app.domain.replay import IncidentEntry, RunMetadata, RunSummary
from app.domain.rover_state import RoverState
from app.domain.scenarios import (
    RequestedMotionPlan,
    ScenarioDefinition,
    ScenarioFault,
    ScenarioInitialState,
)
from app.domain.sensors import (
    ContactReading,
    EncoderReading,
    IMUReading,
    LiDARReading,
    SensorReading,
)
from app.domain.time import ManualClock, MonotonicClock, SimulationClock, Timestamp

__all__ = [
    "AuthorizedMotionCommand",
    "ContactReading",
    "EncoderReading",
    "Event",
    "EventBuilder",
    "EventCategory",
    "EventId",
    "EventSeverity",
    "FaultProfile",
    "FaultRuntimeState",
    "FaultStatus",
    "FaultType",
    "IMUReading",
    "IncidentEntry",
    "LiDARReading",
    "LifecycleState",
    "ManualClock",
    "MonotonicClock",
    "MotionArbitrationResult",
    "MotionCommand",
    "MotionConstraintReason",
    "MotionDecision",
    "MotionLimits",
    "RequestedMotionCommand",
    "RequestedMotionPlan",
    "ReplayStatus",
    "RoverState",
    "RunId",
    "RunMetadata",
    "RunSummary",
    "SafetyState",
    "ScenarioDefinition",
    "ScenarioFault",
    "ScenarioId",
    "ScenarioInitialState",
    "ScenarioStatus",
    "SensorReading",
    "SensorStatus",
    "SensorType",
    "SequentialIdGenerator",
    "SimulationClock",
    "Timestamp",
    "UuidIdGenerator",
    "motion_limits_for_state",
]
