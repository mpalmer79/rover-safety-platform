"""Waypoint primitives.

Waypoints are declarative goals supplied by the mission plan. The
orchestrator dequeues them in order and asks the
:class:`WaypointController` to generate motion toward the head of the
queue. Completion is determined by Euclidean position tolerance and
heading tolerance; timeouts force a recovery attempt.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from typing import Any, Optional

from app.mission.enums import WaypointStatus


@dataclass(frozen=True)
class Waypoint:
    """Declarative waypoint goal."""

    waypoint_id: str
    pose_x: float
    pose_y: float
    heading_rad: float
    position_tolerance: float
    heading_tolerance: float
    timeout_seconds: float

    def __post_init__(self) -> None:
        if not self.waypoint_id:
            raise ValueError("waypoint_id must be non-empty")
        for name in ("pose_x", "pose_y", "heading_rad"):
            if not math.isfinite(getattr(self, name)):
                raise ValueError(f"Waypoint.{name} must be finite")
        if self.position_tolerance <= 0:
            raise ValueError("position_tolerance must be positive")
        if self.heading_tolerance <= 0:
            raise ValueError("heading_tolerance must be positive")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

    def to_dict(self) -> dict[str, Any]:
        return {
            "waypoint_id": self.waypoint_id,
            "pose_x": self.pose_x,
            "pose_y": self.pose_y,
            "heading_rad": self.heading_rad,
            "position_tolerance": self.position_tolerance,
            "heading_tolerance": self.heading_tolerance,
            "timeout_seconds": self.timeout_seconds,
        }


@dataclass(frozen=True)
class WaypointProgress:
    """Snapshot of progress toward the active waypoint."""

    waypoint: Waypoint
    status: WaypointStatus
    started_at_ms: int
    completed_at_ms: Optional[int] = None
    distance_to_goal_m: float = 0.0
    heading_error_rad: float = 0.0
    elapsed_ms: int = 0
    timed_out: bool = False
    aborted: bool = False
    notes: tuple[str, ...] = field(default_factory=tuple)

    def with_status(self, status: WaypointStatus, *, now_ms: int, **kwargs: Any) -> "WaypointProgress":
        completed = (
            now_ms
            if status in {WaypointStatus.COMPLETED, WaypointStatus.TIMED_OUT, WaypointStatus.ABORTED}
            else self.completed_at_ms
        )
        return replace(
            self,
            status=status,
            completed_at_ms=completed,
            **kwargs,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "waypoint": self.waypoint.to_dict(),
            "status": self.status.value,
            "started_at_ms": self.started_at_ms,
            "completed_at_ms": self.completed_at_ms,
            "distance_to_goal_m": self.distance_to_goal_m,
            "heading_error_rad": self.heading_error_rad,
            "elapsed_ms": self.elapsed_ms,
            "timed_out": self.timed_out,
            "aborted": self.aborted,
            "notes": list(self.notes),
        }


class WaypointQueue:
    """Mutable FIFO queue of waypoints with iteration helpers.

    The queue is the only mutable piece of the mission runtime that
    holds per-mission state directly. Pure-logic transitions read it
    via :meth:`peek` and :meth:`pop`; the :class:`MissionOrchestrator`
    drives the lifecycle.
    """

    def __init__(self, waypoints: tuple[Waypoint, ...]) -> None:
        self._all: tuple[Waypoint, ...] = tuple(waypoints)
        self._remaining: list[Waypoint] = list(waypoints)
        self._completed: list[Waypoint] = []
        self._timed_out: list[Waypoint] = []
        self._aborted: list[Waypoint] = []

    @property
    def total(self) -> int:
        return len(self._all)

    @property
    def remaining(self) -> int:
        return len(self._remaining)

    @property
    def completed_count(self) -> int:
        return len(self._completed)

    @property
    def timed_out_count(self) -> int:
        return len(self._timed_out)

    @property
    def aborted_count(self) -> int:
        return len(self._aborted)

    @property
    def is_empty(self) -> bool:
        return not self._remaining

    def peek(self) -> Optional[Waypoint]:
        return self._remaining[0] if self._remaining else None

    def pop_completed(self) -> Optional[Waypoint]:
        if not self._remaining:
            return None
        wp = self._remaining.pop(0)
        self._completed.append(wp)
        return wp

    def pop_timed_out(self) -> Optional[Waypoint]:
        if not self._remaining:
            return None
        wp = self._remaining.pop(0)
        self._timed_out.append(wp)
        return wp

    def abort_remaining(self) -> tuple[Waypoint, ...]:
        aborted = tuple(self._remaining)
        self._aborted.extend(self._remaining)
        self._remaining.clear()
        return aborted

    def progress_fraction(self) -> float:
        if self.total == 0:
            return 1.0
        finished = self.completed_count + self.timed_out_count + self.aborted_count
        return finished / self.total
