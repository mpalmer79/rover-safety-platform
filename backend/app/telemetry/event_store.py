"""In-memory event store used by tests and the API."""

from __future__ import annotations

from typing import Iterator, Optional

from app.domain.enums import EventSeverity, SafetyState
from app.domain.events import Event
from app.domain.identifiers import RunId


class EventStore:
    """Thread-unsafe in-memory store of events grouped by run.

    The store is small on purpose: it exists to make tests assert on
    structured outcomes, and to back lightweight API queries.
    """

    def __init__(self) -> None:
        self._events: list[Event] = []

    def append(self, event: Event) -> None:
        self._events.append(event)

    def extend(self, events: list[Event]) -> None:
        self._events.extend(events)

    def __len__(self) -> int:
        return len(self._events)

    def __iter__(self) -> Iterator[Event]:
        return iter(self._events)

    def all(self) -> tuple[Event, ...]:
        return tuple(self._events)

    def by_run(self, run_id: RunId) -> tuple[Event, ...]:
        return tuple(e for e in self._events if e.run_id == run_id)

    def by_event_type(self, event_type: str) -> tuple[Event, ...]:
        return tuple(e for e in self._events if e.event_type == event_type)

    def by_severity(self, severity: EventSeverity) -> tuple[Event, ...]:
        return tuple(e for e in self._events if e.severity == severity)

    def by_safety_state(self, state: SafetyState) -> tuple[Event, ...]:
        return tuple(e for e in self._events if e.safety_state == state)

    def by_correlation(self, correlation_id: str) -> tuple[Event, ...]:
        return tuple(e for e in self._events if e.correlation_id == correlation_id)

    def first_with_reason(self, reason_code: str) -> Optional[Event]:
        for e in self._events:
            if e.reason_code == reason_code:
                return e
        return None

    def transitions(self) -> tuple[Event, ...]:
        return tuple(e for e in self._events if e.event_type.startswith("safety_transition."))

    def clear(self) -> None:
        self._events.clear()
