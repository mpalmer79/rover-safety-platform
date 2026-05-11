"""Event capture helpers.

The runtime already produces a frozen event stream; this module
exposes a small helper that re-orders / filters / counts events for
the downstream replay + analytics bridges. It does NOT mutate the
runtime output.
"""

from __future__ import annotations

from typing import Iterable, Mapping

from .models import MissionRehearsalEvent, RehearsalEventType


def capture_events(
    events: Iterable[MissionRehearsalEvent],
    *,
    event_types: Iterable[str] | None = None,
) -> tuple[MissionRehearsalEvent, ...]:
    allowed = (
        set(event_types) if event_types is not None else set(e.value for e in RehearsalEventType)
    )
    return tuple(e for e in events if e.event_type in allowed)


def count_by_type(events: Iterable[MissionRehearsalEvent]) -> dict[str, int]:
    out: dict[str, int] = {}
    for event in events:
        out[event.event_type] = out.get(event.event_type, 0) + 1
    return out


def count_by_severity(events: Iterable[MissionRehearsalEvent]) -> dict[str, int]:
    out: dict[str, int] = {}
    for event in events:
        out[event.severity] = out.get(event.severity, 0) + 1
    return out


def safety_escalation_count(events: Iterable[MissionRehearsalEvent]) -> int:
    return sum(
        1
        for event in events
        if event.event_type == RehearsalEventType.SAFETY.value
        and event.severity == "rejection"
    )
