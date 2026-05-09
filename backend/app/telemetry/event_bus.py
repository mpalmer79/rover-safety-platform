"""Synchronous in-process event bus.

The bus accepts events from any subsystem and broadcasts them to
registered subscribers. It is intentionally synchronous: deterministic
simulation requires that subscribers see events in the exact order
they are emitted.
"""

from __future__ import annotations

from typing import Callable, Protocol

from app.domain.events import Event


class EventSubscriber(Protocol):
    def __call__(self, event: Event) -> None: ...


class EventBus:
    def __init__(self) -> None:
        self._subscribers: list[EventSubscriber] = []

    def subscribe(self, subscriber: EventSubscriber) -> Callable[[], None]:
        """Register a subscriber and return a callable that unsubscribes."""

        self._subscribers.append(subscriber)

        def unsubscribe() -> None:
            try:
                self._subscribers.remove(subscriber)
            except ValueError:
                pass

        return unsubscribe

    def publish(self, event: Event) -> None:
        for sub in list(self._subscribers):
            sub(event)

    def publish_many(self, events: list[Event]) -> None:
        for evt in events:
            self.publish(evt)

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)
