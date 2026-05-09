"""Identifier types and generators.

Identifiers are wrapped in dedicated types so that mixing run / scenario /
event IDs at call sites is a static error. Generators are injectable so
tests can produce deterministic identifiers without monkey-patching uuid.
"""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class _IdBase:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError(f"{type(self).__name__} value must be non-empty")

    def __str__(self) -> str:
        return self.value


class RunId(_IdBase):
    """Unique identifier for one operational run."""


class ScenarioId(_IdBase):
    """Identifier for a scenario template (stable across runs)."""


class EventId(_IdBase):
    """Unique identifier for a single event."""


class IdGenerator(Protocol):
    """Pluggable identifier source. Implementations must be thread-safe."""

    def run_id(self) -> RunId: ...
    def event_id(self) -> EventId: ...


class UuidIdGenerator:
    """Default generator backed by :mod:`uuid`."""

    def run_id(self) -> RunId:
        return RunId(str(uuid.uuid4()))

    def event_id(self) -> EventId:
        return EventId(str(uuid.uuid4()))


class SequentialIdGenerator:
    """Deterministic generator for tests and reproducible scenarios.

    Produces zero-padded sequential values prefixed by the kind, e.g.
    ``run-0000000001`` and ``evt-0000000042``.
    """

    def __init__(self, *, run_prefix: str = "run", event_prefix: str = "evt") -> None:
        self._run_prefix = run_prefix
        self._event_prefix = event_prefix
        self._run_counter = 0
        self._event_counter = 0
        self._lock = threading.Lock()

    def run_id(self) -> RunId:
        with self._lock:
            self._run_counter += 1
            return RunId(f"{self._run_prefix}-{self._run_counter:010d}")

    def event_id(self) -> EventId:
        with self._lock:
            self._event_counter += 1
            return EventId(f"{self._event_prefix}-{self._event_counter:010d}")

    def reset(self) -> None:
        with self._lock:
            self._run_counter = 0
            self._event_counter = 0
