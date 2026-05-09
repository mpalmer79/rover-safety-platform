"""Canonical rover state.

A single dataclass that travels through the engine each tick. All
mutations go through :meth:`RoverState.with_updates` to keep the value
object immutable in spirit.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from typing import Any

from app.domain.enums import LifecycleState, SafetyState


@dataclass(frozen=True, slots=True)
class RoverState:
    """Pose, motion, and lifecycle/safety summary at a point in time.

    The simulation engine tracks a rover state per tick. This struct is
    serialized to ``states.jsonl`` for replay.
    """

    pose_x: float = 0.0
    pose_y: float = 0.0
    heading_rad: float = 0.0
    linear_velocity: float = 0.0
    angular_velocity: float = 0.0
    safety_state: SafetyState = SafetyState.BOOT
    lifecycle_state: LifecycleState = LifecycleState.UNCONFIGURED
    last_update_ms: int = 0
    distance_traveled_m: float = 0.0
    notes: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        for name in (
            "pose_x",
            "pose_y",
            "heading_rad",
            "linear_velocity",
            "angular_velocity",
            "distance_traveled_m",
        ):
            value = getattr(self, name)
            if not math.isfinite(value):
                raise ValueError(f"RoverState.{name} must be finite, got {value!r}")
        if self.last_update_ms < 0:
            raise ValueError("last_update_ms must be non-negative")

    def with_updates(self, **kwargs: Any) -> "RoverState":
        return replace(self, **kwargs)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pose_x": self.pose_x,
            "pose_y": self.pose_y,
            "heading_rad": self.heading_rad,
            "linear_velocity": self.linear_velocity,
            "angular_velocity": self.angular_velocity,
            "safety_state": self.safety_state.value,
            "lifecycle_state": self.lifecycle_state.value,
            "last_update_ms": self.last_update_ms,
            "distance_traveled_m": self.distance_traveled_m,
            "notes": list(self.notes),
        }

    @classmethod
    def initial(
        cls,
        *,
        pose_x: float = 0.0,
        pose_y: float = 0.0,
        heading_rad: float = 0.0,
    ) -> "RoverState":
        return cls(
            pose_x=pose_x,
            pose_y=pose_y,
            heading_rad=heading_rad,
            linear_velocity=0.0,
            angular_velocity=0.0,
            safety_state=SafetyState.BOOT,
            lifecycle_state=LifecycleState.UNCONFIGURED,
            last_update_ms=0,
            distance_traveled_m=0.0,
            notes=(),
        )
