"""Mission plan: declarative description of a mission run.

A mission plan combines a set of waypoints, an operational constraint
envelope, and the world-model zone declarations the orchestrator
should observe. Plans are loaded from scenario files; the
deterministic engine and the ROS 2 mission node share this type.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.mission.constraints import MissionConstraints
from app.mission.waypoints import Waypoint
from app.world_model.boundaries import OperationalBoundary
from app.world_model.keepout import KeepoutZone, RestrictedZone


@dataclass(frozen=True)
class MissionPlan:
    """Declarative mission plan."""

    mission_id: str
    waypoints: tuple[Waypoint, ...]
    constraints: MissionConstraints = field(default_factory=MissionConstraints)
    keepouts: tuple[KeepoutZone, ...] = field(default_factory=tuple)
    restricted_zones: tuple[RestrictedZone, ...] = field(default_factory=tuple)
    boundaries: tuple[OperationalBoundary, ...] = field(default_factory=tuple)
    max_recovery_attempts: int = 3
    """Per-waypoint recovery attempt budget. Exceeding it transitions
    the orchestrator to ``MISSION_ABORTING``."""

    def __post_init__(self) -> None:
        if not self.mission_id:
            raise ValueError("mission_id must be non-empty")
        if not self.waypoints:
            raise ValueError("MissionPlan must contain at least one waypoint")
        if self.max_recovery_attempts < 0:
            raise ValueError("max_recovery_attempts must be non-negative")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MissionPlan":
        if "mission_id" not in data:
            raise ValueError("mission plan requires mission_id")
        if "waypoints" not in data:
            raise ValueError("mission plan requires waypoints")
        waypoints = tuple(
            Waypoint(
                waypoint_id=str(w["waypoint_id"]),
                pose_x=float(w["pose_x"]),
                pose_y=float(w["pose_y"]),
                heading_rad=float(w.get("heading_rad", 0.0)),
                position_tolerance=float(w.get("position_tolerance", 0.20)),
                heading_tolerance=float(w.get("heading_tolerance", 0.40)),
                timeout_seconds=float(w.get("timeout_seconds", 30.0)),
            )
            for w in data["waypoints"]
        )
        constraints_data = data.get("constraints") or {}
        constraints = MissionConstraints(
            max_linear_velocity=float(constraints_data.get("max_linear_velocity", 0.5)),
            max_angular_velocity=float(
                constraints_data.get("max_angular_velocity", 0.8)
            ),
            minimum_confidence_for_motion=float(
                constraints_data.get("minimum_confidence_for_motion", 0.5)
            ),
            maximum_allowed_drift_m=float(
                constraints_data.get("maximum_allowed_drift_m", 1.0)
            ),
            minimum_forward_clearance_m=float(
                constraints_data.get("minimum_forward_clearance_m", 0.30)
            ),
            minimum_sensor_health=int(
                constraints_data.get("minimum_sensor_health", 3)
            ),
        )

        keepouts = tuple(
            KeepoutZone(
                zone_id=str(z["zone_id"]),
                min_x=float(z["min_x"]),
                min_y=float(z["min_y"]),
                max_x=float(z["max_x"]),
                max_y=float(z["max_y"]),
                margin_m=float(z.get("margin_m", 0.30)),
            )
            for z in data.get("keepout_zones", [])
        )
        restricted = tuple(
            RestrictedZone(
                zone_id=str(z["zone_id"]),
                min_x=float(z["min_x"]),
                min_y=float(z["min_y"]),
                max_x=float(z["max_x"]),
                max_y=float(z["max_y"]),
                max_linear_velocity=float(z["max_linear_velocity"]),
                max_angular_velocity=float(z["max_angular_velocity"]),
            )
            for z in data.get("restricted_zones", [])
        )
        boundaries = tuple(
            OperationalBoundary(
                boundary_id=str(b["boundary_id"]),
                min_x=float(b["min_x"]),
                min_y=float(b["min_y"]),
                max_x=float(b["max_x"]),
                max_y=float(b["max_y"]),
            )
            for b in data.get("operational_boundaries", [])
        )
        return cls(
            mission_id=str(data["mission_id"]),
            waypoints=waypoints,
            constraints=constraints,
            keepouts=keepouts,
            restricted_zones=restricted,
            boundaries=boundaries,
            max_recovery_attempts=int(data.get("max_recovery_attempts", 3)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "waypoints": [w.to_dict() for w in self.waypoints],
            "constraints": {
                "max_linear_velocity": self.constraints.max_linear_velocity,
                "max_angular_velocity": self.constraints.max_angular_velocity,
                "minimum_confidence_for_motion": self.constraints.minimum_confidence_for_motion,
                "maximum_allowed_drift_m": self.constraints.maximum_allowed_drift_m,
                "minimum_forward_clearance_m": self.constraints.minimum_forward_clearance_m,
                "minimum_sensor_health": self.constraints.minimum_sensor_health,
            },
            "keepout_zones": [
                {
                    "zone_id": z.zone_id,
                    "min_x": z.min_x,
                    "min_y": z.min_y,
                    "max_x": z.max_x,
                    "max_y": z.max_y,
                    "margin_m": z.margin_m,
                }
                for z in self.keepouts
            ],
            "restricted_zones": [
                {
                    "zone_id": z.zone_id,
                    "min_x": z.min_x,
                    "min_y": z.min_y,
                    "max_x": z.max_x,
                    "max_y": z.max_y,
                    "max_linear_velocity": z.max_linear_velocity,
                    "max_angular_velocity": z.max_angular_velocity,
                }
                for z in self.restricted_zones
            ],
            "operational_boundaries": [
                {
                    "boundary_id": b.boundary_id,
                    "min_x": b.min_x,
                    "min_y": b.min_y,
                    "max_x": b.max_x,
                    "max_y": b.max_y,
                }
                for b in self.boundaries
            ],
            "max_recovery_attempts": self.max_recovery_attempts,
        }
