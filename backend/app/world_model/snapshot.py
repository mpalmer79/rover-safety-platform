"""Replay-friendly serialisation of the world model state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class WorldModelSnapshot:
    """A single tick's world-model state, serialisable to JSON.

    Snapshots are recorded to ``runs/<run_id>/world_model_snapshots.jsonl``
    every recording tick. The schema is intentionally flat so replay
    tools can index it without parsing nested objects.
    """

    sim_time_ns: int
    pose_x: float
    pose_y: float
    heading_rad: float
    occupancy_min_range_m: float
    occupancy_mean_range_m: float
    forward_sector_clear: bool
    forward_clearance_m: float
    inside_keepout: tuple[str, ...] = field(default_factory=tuple)
    near_keepout: tuple[str, ...] = field(default_factory=tuple)
    inside_restricted: tuple[str, ...] = field(default_factory=tuple)
    boundary_violations: tuple[str, ...] = field(default_factory=tuple)
    speed_limit_linear: float | None = None
    speed_limit_angular: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "sim_time_ns": self.sim_time_ns,
            "pose_x": self.pose_x,
            "pose_y": self.pose_y,
            "heading_rad": self.heading_rad,
            "occupancy_min_range_m": self.occupancy_min_range_m,
            "occupancy_mean_range_m": self.occupancy_mean_range_m,
            "forward_sector_clear": self.forward_sector_clear,
            "forward_clearance_m": self.forward_clearance_m,
            "inside_keepout": list(self.inside_keepout),
            "near_keepout": list(self.near_keepout),
            "inside_restricted": list(self.inside_restricted),
            "boundary_violations": list(self.boundary_violations),
            "speed_limit_linear": self.speed_limit_linear,
            "speed_limit_angular": self.speed_limit_angular,
        }
