"""Structured events conforming to docs/EVENT_MODEL.md.

The :class:`Event` envelope is a single dataclass with strict validation.
Producers should not construct events directly except through
:class:`EventBuilder` or one of the helper factories: this guarantees
that the controlled vocabularies are enforced at emission time.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from app.domain.enums import EventCategory, EventSeverity, LifecycleState, SafetyState
from app.domain.identifiers import EventId, IdGenerator, RunId, ScenarioId, UuidIdGenerator
from app.domain.motion import AuthorizedMotionCommand, RequestedMotionCommand
from app.domain.time import SimulationClock, Timestamp


REQUIRED_EVENT_FIELDS: tuple[str, ...] = (
    "timestamp",
    "run_id",
    "scenario_id",
    "event_id",
    "event_type",
    "severity",
    "subsystem",
    "node",
    "lifecycle_state",
    "safety_state",
    "source_topic",
    "confidence_score",
    "requested_motion",
    "final_motion",
    "reason_code",
    "message",
)


@dataclass(frozen=True, slots=True)
class Event:
    """The canonical event envelope.

    The schema mirrors docs/EVENT_MODEL.md section 3. ``source_topic``,
    ``confidence_score``, ``requested_motion``, and ``final_motion`` are
    required *fields*, but their values may be ``None`` when not
    applicable.
    """

    timestamp: Timestamp
    run_id: RunId
    scenario_id: ScenarioId
    event_id: EventId
    event_type: str
    severity: EventSeverity
    subsystem: str
    node: str
    lifecycle_state: LifecycleState
    safety_state: SafetyState
    reason_code: str
    message: str
    source_topic: Optional[str] = None
    confidence_score: Optional[float] = None
    requested_motion: Optional[RequestedMotionCommand] = None
    final_motion: Optional[AuthorizedMotionCommand] = None
    correlation_id: Optional[str] = None
    parent_event_id: Optional[EventId] = None
    tags: tuple[str, ...] = field(default_factory=tuple)
    attributes: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if "." not in self.event_type:
            raise ValueError(
                f"event_type must use dot-namespaced form, got {self.event_type!r}"
            )
        category = self.event_type.split(".", 1)[0]
        if category not in {c.value for c in EventCategory}:
            raise ValueError(
                f"event_type {self.event_type!r} uses unknown category {category!r}"
            )
        if not self.subsystem:
            raise ValueError("subsystem must be non-empty")
        if not self.node:
            raise ValueError("node must be non-empty")
        if not self.reason_code:
            raise ValueError("reason_code must be non-empty")
        if self.confidence_score is not None and not 0.0 <= self.confidence_score <= 1.0:
            raise ValueError("confidence_score must be in [0.0, 1.0] when set")

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.wall,
            "sim_time_ns": self.timestamp.sim_time_ns,
            "run_id": str(self.run_id),
            "scenario_id": str(self.scenario_id),
            "event_id": str(self.event_id),
            "event_type": self.event_type,
            "severity": self.severity.value,
            "subsystem": self.subsystem,
            "node": self.node,
            "lifecycle_state": self.lifecycle_state.value,
            "safety_state": self.safety_state.value,
            "source_topic": self.source_topic,
            "confidence_score": self.confidence_score,
            "requested_motion": self.requested_motion.to_dict() if self.requested_motion else None,
            "final_motion": self.final_motion.to_dict() if self.final_motion else None,
            "reason_code": self.reason_code,
            "message": self.message,
            "correlation_id": self.correlation_id,
            "parent_event_id": str(self.parent_event_id) if self.parent_event_id else None,
            "tags": list(self.tags),
            "attributes": dict(self.attributes),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), separators=(",", ":"), sort_keys=True)


class EventBuilder:
    """Helper that fills in the fields the producer rarely changes.

    Subsystems hold an :class:`EventBuilder` per node; when emitting they
    call :meth:`build` with only the fields that vary per event.
    """

    def __init__(
        self,
        *,
        run_id: RunId,
        scenario_id: ScenarioId,
        clock: SimulationClock,
        id_generator: IdGenerator,
        subsystem: str,
        node: str,
        lifecycle_state: LifecycleState = LifecycleState.ACTIVE,
        safety_state: SafetyState = SafetyState.BOOT,
    ) -> None:
        self._run_id = run_id
        self._scenario_id = scenario_id
        self._clock = clock
        self._ids = id_generator
        self._subsystem = subsystem
        self._node = node
        self._lifecycle_state = lifecycle_state
        self._safety_state = safety_state

    def update_safety_state(self, state: SafetyState) -> None:
        self._safety_state = state

    def update_lifecycle(self, state: LifecycleState) -> None:
        self._lifecycle_state = state

    @property
    def safety_state(self) -> SafetyState:
        return self._safety_state

    def build(
        self,
        *,
        event_type: str,
        severity: EventSeverity,
        reason_code: str,
        message: str,
        source_topic: Optional[str] = None,
        confidence_score: Optional[float] = None,
        requested_motion: Optional[RequestedMotionCommand] = None,
        final_motion: Optional[AuthorizedMotionCommand] = None,
        correlation_id: Optional[str] = None,
        parent_event_id: Optional[EventId] = None,
        tags: tuple[str, ...] = (),
        attributes: Optional[dict[str, Any]] = None,
        safety_state: Optional[SafetyState] = None,
        lifecycle_state: Optional[LifecycleState] = None,
    ) -> Event:
        return Event(
            timestamp=self._clock.stamp(),
            run_id=self._run_id,
            scenario_id=self._scenario_id,
            event_id=self._ids.event_id(),
            event_type=event_type,
            severity=severity,
            subsystem=self._subsystem,
            node=self._node,
            lifecycle_state=lifecycle_state if lifecycle_state is not None else self._lifecycle_state,
            safety_state=safety_state if safety_state is not None else self._safety_state,
            reason_code=reason_code,
            message=message,
            source_topic=source_topic,
            confidence_score=confidence_score,
            requested_motion=requested_motion,
            final_motion=final_motion,
            correlation_id=correlation_id,
            parent_event_id=parent_event_id,
            tags=tuple(tags),
            attributes=dict(attributes or {}),
        )


def default_id_generator() -> IdGenerator:
    """Return a UUID-based generator. Tests should pass their own generator."""
    return UuidIdGenerator()
