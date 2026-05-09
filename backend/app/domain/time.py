"""Time abstractions used by the simulation core.

Two clocks matter to us:

* The wall clock, used purely for human-readable timestamps.
* The simulation clock, the authoritative timeline for the run.

Both are exposed through small interfaces so tests can drive them
deterministically. The simulation engine never reads ``time.time()``
directly.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol


@dataclass(frozen=True, slots=True)
class Timestamp:
    """A pair of (wall-clock RFC 3339 string, sim-time nanoseconds).

    ``wall`` is set per the producer's wall clock for operator-friendly
    display. ``sim_time_ns`` is the authoritative timeline for replay,
    matching docs/EVENT_MODEL.md section 9.
    """

    wall: str
    sim_time_ns: int

    def __post_init__(self) -> None:
        if self.sim_time_ns < 0:
            raise ValueError("sim_time_ns must be non-negative")

    @classmethod
    def from_datetime(cls, dt: datetime, sim_time_ns: int) -> "Timestamp":
        if dt.tzinfo is None:
            raise ValueError("Timestamp.from_datetime requires a timezone-aware datetime")
        return cls(wall=dt.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z"), sim_time_ns=sim_time_ns)


class SimulationClock(Protocol):
    """The simulation timeline."""

    def now_ns(self) -> int: ...

    def now_ms(self) -> int: ...

    def advance_ms(self, delta_ms: int) -> None: ...

    def stamp(self) -> Timestamp: ...


class ManualClock:
    """Hand-driven clock for deterministic tests and scenario runs.

    The wall clock is also synthetic and advances proportionally to the
    simulation clock so that test outputs are entirely reproducible.
    """

    def __init__(
        self,
        *,
        start_ns: int = 0,
        wall_start: datetime | None = None,
    ) -> None:
        self._sim_ns = int(start_ns)
        self._wall_start = (
            wall_start
            if wall_start is not None
            else datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        )

    def now_ns(self) -> int:
        return self._sim_ns

    def now_ms(self) -> int:
        return self._sim_ns // 1_000_000

    def advance_ms(self, delta_ms: int) -> None:
        if delta_ms < 0:
            raise ValueError("delta_ms must be non-negative")
        self._sim_ns += int(delta_ms) * 1_000_000

    def advance_ns(self, delta_ns: int) -> None:
        if delta_ns < 0:
            raise ValueError("delta_ns must be non-negative")
        self._sim_ns += int(delta_ns)

    def stamp(self) -> Timestamp:
        wall = self._wall_start.timestamp() + self._sim_ns / 1_000_000_000
        dt = datetime.fromtimestamp(wall, tz=timezone.utc)
        return Timestamp.from_datetime(dt, self._sim_ns)


class MonotonicClock:
    """Wall-driven clock for live processes.

    Not used by the deterministic simulation engine, but provided so that
    optional future bridges (live ROS 2 nodes) can share the
    :class:`SimulationClock` interface.
    """

    def __init__(self) -> None:
        self._origin_ns = time.monotonic_ns()

    def now_ns(self) -> int:
        return time.monotonic_ns() - self._origin_ns

    def now_ms(self) -> int:
        return self.now_ns() // 1_000_000

    def advance_ms(self, delta_ms: int) -> None:  # pragma: no cover - n/a for monotonic
        raise RuntimeError("Cannot advance a monotonic clock")

    def stamp(self) -> Timestamp:
        dt = datetime.now(tz=timezone.utc)
        return Timestamp.from_datetime(dt, self.now_ns())
