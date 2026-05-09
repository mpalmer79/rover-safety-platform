"""Watchdog registry.

A watchdog has a name, a deadline (ms), and a configured action. The
supervisor pets registered watchdogs based on observed inputs (LiDAR
freshness, encoder freshness, gateway heartbeat, etc.). The registry
itself is passive: it only reports which watchdogs have expired.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Optional

from app.domain.enums import SafetyState


@dataclass(frozen=True, slots=True)
class WatchdogConfig:
    """Configuration for a single watchdog.

    ``escalation_state`` is the state the supervisor should transition to
    when this watchdog expires. ``reason_code`` is the stable string
    written into emitted events.
    """

    name: str
    deadline_ms: int
    escalation_state: SafetyState
    reason_code: str

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Watchdog name must be non-empty")
        if self.deadline_ms <= 0:
            raise ValueError("Watchdog deadline must be positive")


@dataclass(frozen=True, slots=True)
class Watchdog:
    """Live runtime view of a watchdog."""

    config: WatchdogConfig
    last_pet_ms: int
    expired: bool = False

    def with_pet(self, *, now_ms: int) -> "Watchdog":
        return replace(self, last_pet_ms=now_ms, expired=False)

    def with_expiration(self) -> "Watchdog":
        return replace(self, expired=True)

    def is_expired_at(self, *, now_ms: int) -> bool:
        return now_ms - self.last_pet_ms > self.config.deadline_ms

    def time_until_expiration_ms(self, *, now_ms: int) -> int:
        return max(0, self.config.deadline_ms - (now_ms - self.last_pet_ms))


@dataclass(frozen=True, slots=True)
class WatchdogReport:
    """Summary of all watchdog states at a single tick."""

    expired: tuple[Watchdog, ...] = field(default_factory=tuple)
    healthy: tuple[Watchdog, ...] = field(default_factory=tuple)

    @property
    def any_expired(self) -> bool:
        return bool(self.expired)

    def expired_reason_codes(self) -> tuple[str, ...]:
        return tuple(w.config.reason_code for w in self.expired)

    def highest_escalation(self) -> Optional[SafetyState]:
        if not self.expired:
            return None
        # Pick the most restrictive escalation among expired watchdogs.
        states = [w.config.escalation_state for w in self.expired]
        return max(states, key=lambda s: s.value if False else _ESCALATION_RANK[s])


_ESCALATION_RANK: dict[SafetyState, int] = {
    SafetyState.ACTIVE_RESTRICTED: 1,
    SafetyState.ACTIVE_DEGRADED: 2,
    SafetyState.SAFE_STOP: 3,
    SafetyState.E_STOP_LATCHED: 4,
    SafetyState.RECOVERY: 0,
    SafetyState.ACTIVE_NORMAL: 0,
    SafetyState.BOOT: 0,
    SafetyState.INACTIVE: 0,
}


class WatchdogRegistry:
    """Mutable registry of watchdogs.

    The registry is the only mutable piece of the safety subsystem.
    Mutations are scoped to ``register``, ``pet``, and ``evaluate``.
    """

    def __init__(self) -> None:
        self._watchdogs: dict[str, Watchdog] = {}

    def register(self, config: WatchdogConfig, *, now_ms: int) -> None:
        if config.name in self._watchdogs:
            raise ValueError(f"Watchdog already registered: {config.name}")
        self._watchdogs[config.name] = Watchdog(config=config, last_pet_ms=now_ms)

    def pet(self, name: str, *, now_ms: int) -> None:
        wd = self._watchdogs.get(name)
        if wd is None:
            raise KeyError(f"No watchdog registered with name {name!r}")
        self._watchdogs[name] = wd.with_pet(now_ms=now_ms)

    def evaluate(self, *, now_ms: int) -> WatchdogReport:
        expired: list[Watchdog] = []
        healthy: list[Watchdog] = []
        for name, wd in list(self._watchdogs.items()):
            if wd.is_expired_at(now_ms=now_ms):
                wd_expired = wd.with_expiration()
                self._watchdogs[name] = wd_expired
                expired.append(wd_expired)
            else:
                healthy.append(wd)
        return WatchdogReport(expired=tuple(expired), healthy=tuple(healthy))

    def __contains__(self, name: str) -> bool:
        return name in self._watchdogs

    def names(self) -> tuple[str, ...]:
        return tuple(self._watchdogs.keys())

    def get(self, name: str) -> Optional[Watchdog]:
        return self._watchdogs.get(name)
