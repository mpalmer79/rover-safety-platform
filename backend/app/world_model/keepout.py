"""Keepout and restricted-speed zone primitives.

Zones are axis-aligned rectangles (the simplest representation that
covers the cases this platform validates). They are declarative — a
zone is loaded from a scenario, not learned, perceived, or estimated.

Zone evaluation is a pure function: given a 2D pose, return whether
the rover is inside or near the zone, and what the implied speed
limit is. The orchestrator uses the result to constrain its
:class:`RequestedMotionCommand`; the supervisor's ``MotionArbiter``
then clamps as a backstop.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable, Optional

from app.world_model.enums import ZoneKind


@dataclass(frozen=True)
class KeepoutZone:
    """An axis-aligned rectangle the rover must not enter."""

    zone_id: str
    min_x: float
    min_y: float
    max_x: float
    max_y: float
    margin_m: float = 0.30
    """Buffer distance the orchestrator treats as ``KEEPOUT_PENDING``.

    When the rover is within ``margin_m`` of the zone but not yet
    inside, the orchestrator should reduce velocity and/or steer away.
    """

    def __post_init__(self) -> None:
        if not self.zone_id:
            raise ValueError("zone_id must be non-empty")
        if self.max_x <= self.min_x or self.max_y <= self.min_y:
            raise ValueError(
                f"keepout zone {self.zone_id!r} has invalid extent"
            )
        if self.margin_m < 0:
            raise ValueError("margin_m must be non-negative")

    @property
    def kind(self) -> ZoneKind:
        return ZoneKind.KEEPOUT

    def contains(self, x: float, y: float) -> bool:
        return self.min_x <= x <= self.max_x and self.min_y <= y <= self.max_y

    def signed_distance(self, x: float, y: float) -> float:
        """Negative when inside, positive when outside.

        For an axis-aligned box the canonical SDF is
        ``max(min(dx, 0), min(dy, 0)) + length(max(d, 0))``. We use the
        common simplification that is exact for outside points and a
        conservative inside estimate.
        """

        dx = max(self.min_x - x, x - self.max_x, 0.0)
        dy = max(self.min_y - y, y - self.max_y, 0.0)
        outside = math.hypot(dx, dy)
        if outside > 0:
            return outside
        # Inside: distance to nearest edge, returned as negative.
        ix = min(x - self.min_x, self.max_x - x)
        iy = min(y - self.min_y, self.max_y - y)
        return -min(ix, iy)


@dataclass(frozen=True)
class RestrictedZone:
    """An axis-aligned rectangle that imposes a reduced speed limit."""

    zone_id: str
    min_x: float
    min_y: float
    max_x: float
    max_y: float
    max_linear_velocity: float
    max_angular_velocity: float

    def __post_init__(self) -> None:
        if not self.zone_id:
            raise ValueError("zone_id must be non-empty")
        if self.max_x <= self.min_x or self.max_y <= self.min_y:
            raise ValueError(
                f"restricted zone {self.zone_id!r} has invalid extent"
            )
        if self.max_linear_velocity < 0 or self.max_angular_velocity < 0:
            raise ValueError("restricted zone speed limits must be non-negative")

    @property
    def kind(self) -> ZoneKind:
        return ZoneKind.RESTRICTED_SPEED

    def contains(self, x: float, y: float) -> bool:
        return self.min_x <= x <= self.max_x and self.min_y <= y <= self.max_y


@dataclass(frozen=True)
class ZoneCheckResult:
    """Outcome of evaluating a pose against a set of zones."""

    inside_keepout: tuple[str, ...] = ()
    near_keepout: tuple[str, ...] = ()
    inside_restricted: tuple[str, ...] = ()
    nearest_keepout_distance_m: Optional[float] = None
    speed_limit_linear: Optional[float] = None
    speed_limit_angular: Optional[float] = None

    @property
    def has_violation(self) -> bool:
        return bool(self.inside_keepout)

    def is_pending(self) -> bool:
        return bool(self.near_keepout) and not self.inside_keepout


def evaluate_zones(
    *,
    pose_x: float,
    pose_y: float,
    keepouts: Iterable[KeepoutZone],
    restricted: Iterable[RestrictedZone],
) -> ZoneCheckResult:
    """Pure-function pose-against-zones evaluation."""

    inside_keepout: list[str] = []
    near_keepout: list[str] = []
    nearest: Optional[float] = None
    for zone in keepouts:
        sdf = zone.signed_distance(pose_x, pose_y)
        if nearest is None or abs(sdf) < abs(nearest) or (sdf < 0 and (nearest is None or nearest > 0)):
            nearest = sdf
        if sdf <= 0:
            inside_keepout.append(zone.zone_id)
        elif sdf <= zone.margin_m:
            near_keepout.append(zone.zone_id)

    inside_restricted: list[str] = []
    speed_lin: Optional[float] = None
    speed_ang: Optional[float] = None
    for zone in restricted:
        if zone.contains(pose_x, pose_y):
            inside_restricted.append(zone.zone_id)
            if speed_lin is None or zone.max_linear_velocity < speed_lin:
                speed_lin = zone.max_linear_velocity
            if speed_ang is None or zone.max_angular_velocity < speed_ang:
                speed_ang = zone.max_angular_velocity

    return ZoneCheckResult(
        inside_keepout=tuple(inside_keepout),
        near_keepout=tuple(near_keepout),
        inside_restricted=tuple(inside_restricted),
        nearest_keepout_distance_m=nearest,
        speed_limit_linear=speed_lin,
        speed_limit_angular=speed_ang,
    )
