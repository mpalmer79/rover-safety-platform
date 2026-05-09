"""Operational boundary primitives.

A boundary is the outer extent of the operational area. Crossing a
boundary is treated as a hard violation that the orchestrator
escalates to ``MISSION_DEGRADED`` and, on persistent violation,
``MISSION_ABORTING``.

Boundaries are axis-aligned rectangles. The default boundary used by
the deterministic engine is the validation world (10 m x 10 m centred
on the origin).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class OperationalBoundary:
    """The outer extent of the operational area."""

    boundary_id: str
    min_x: float
    min_y: float
    max_x: float
    max_y: float

    def __post_init__(self) -> None:
        if not self.boundary_id:
            raise ValueError("boundary_id must be non-empty")
        if self.max_x <= self.min_x or self.max_y <= self.min_y:
            raise ValueError(
                f"operational boundary {self.boundary_id!r} has invalid extent"
            )

    def contains(self, x: float, y: float) -> bool:
        return self.min_x <= x <= self.max_x and self.min_y <= y <= self.max_y

    def signed_distance_outside(self, x: float, y: float) -> float:
        """Distance the rover is outside the boundary; 0 if inside.

        Used to decide whether a violation is recoverable (small
        excursion) or hard (large excursion).
        """

        dx = max(self.min_x - x, x - self.max_x, 0.0)
        dy = max(self.min_y - y, y - self.max_y, 0.0)
        if dx == 0.0 and dy == 0.0:
            return 0.0
        return (dx ** 2 + dy ** 2) ** 0.5


@dataclass(frozen=True)
class BoundaryViolation:
    """A single boundary breach observed at a given pose."""

    boundary_id: str
    pose_x: float
    pose_y: float
    distance_outside_m: float
    severity: str  # "minor" | "major"

    @classmethod
    def from_pose(
        cls, *, boundary: OperationalBoundary, pose_x: float, pose_y: float
    ) -> Optional["BoundaryViolation"]:
        d = boundary.signed_distance_outside(pose_x, pose_y)
        if d <= 0.0:
            return None
        severity = "minor" if d < 0.5 else "major"
        return cls(
            boundary_id=boundary.boundary_id,
            pose_x=pose_x,
            pose_y=pose_y,
            distance_outside_m=d,
            severity=severity,
        )
