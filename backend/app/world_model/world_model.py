"""World model: bounded environment awareness.

The world model is fed pose, sensor frames, and (declarative) zone
definitions. It produces a snapshot per evaluation tick plus a list of
hazards to surface to the orchestrator.

The world model does not own safety state and never produces motion
commands. Its outputs are read-only summaries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Optional

from app.domain.sensors import SensorFrame
from app.world_model.boundaries import (
    BoundaryViolation,
    OperationalBoundary,
)
from app.world_model.enums import HazardKind
from app.world_model.keepout import (
    KeepoutZone,
    RestrictedZone,
    ZoneCheckResult,
    evaluate_zones,
)
from app.world_model.occupancy import OccupancySummary, summarise_lidar
from app.world_model.snapshot import WorldModelSnapshot


@dataclass(frozen=True)
class HazardReport:
    """A single hazard observation."""

    kind: HazardKind
    reason_code: str
    severity: str
    summary: str
    attributes: dict = field(default_factory=dict)


@dataclass(frozen=True)
class WorldModelInputs:
    """Inputs presented to the world model for one tick."""

    pose_x: float
    pose_y: float
    heading_rad: float
    sim_time_ns: int
    sensor_frame: Optional[SensorFrame] = None


_REASON_CODES: dict[HazardKind, str] = {
    HazardKind.KEEPOUT_PENDING: "keepout_pending",
    HazardKind.KEEPOUT_VIOLATION: "keepout_violation",
    HazardKind.RESTRICTED_SPEED_VIOLATION: "restricted_speed_violation",
    HazardKind.OPERATIONAL_BOUNDARY_VIOLATION: "operational_boundary_violation",
    HazardKind.OBSTACLE_NEAR: "obstacle_near",
    HazardKind.OBSTACLE_BLOCKING: "obstacle_blocking",
}


class WorldModel:
    """Stateful aggregator of pose, occupancy, and zone evaluations."""

    def __init__(
        self,
        *,
        keepouts: Iterable[KeepoutZone] = (),
        restricted: Iterable[RestrictedZone] = (),
        boundaries: Iterable[OperationalBoundary] = (),
        forward_clear_threshold_m: float = 0.6,
        forward_blocking_threshold_m: float = 0.30,
    ) -> None:
        self._keepouts: tuple[KeepoutZone, ...] = tuple(keepouts)
        self._restricted: tuple[RestrictedZone, ...] = tuple(restricted)
        self._boundaries: tuple[OperationalBoundary, ...] = tuple(boundaries)
        self._forward_clear = forward_clear_threshold_m
        self._forward_blocking = forward_blocking_threshold_m
        self._latest_snapshot: Optional[WorldModelSnapshot] = None
        self._latest_hazards: tuple[HazardReport, ...] = ()
        self._latest_zone_check: Optional[ZoneCheckResult] = None
        self._violation_streak: int = 0

    @property
    def keepouts(self) -> tuple[KeepoutZone, ...]:
        return self._keepouts

    @property
    def restricted_zones(self) -> tuple[RestrictedZone, ...]:
        return self._restricted

    @property
    def boundaries(self) -> tuple[OperationalBoundary, ...]:
        return self._boundaries

    @property
    def latest_snapshot(self) -> Optional[WorldModelSnapshot]:
        return self._latest_snapshot

    @property
    def latest_hazards(self) -> tuple[HazardReport, ...]:
        return self._latest_hazards

    @property
    def latest_zone_check(self) -> Optional[ZoneCheckResult]:
        return self._latest_zone_check

    def update(self, inputs: WorldModelInputs) -> WorldModelSnapshot:
        occupancy = summarise_lidar(
            inputs.sensor_frame.lidar if inputs.sensor_frame else None,
            forward_clear_threshold_m=self._forward_clear,
        )
        zone_check = evaluate_zones(
            pose_x=inputs.pose_x,
            pose_y=inputs.pose_y,
            keepouts=self._keepouts,
            restricted=self._restricted,
        )
        boundary_violations = tuple(
            v
            for v in (
                BoundaryViolation.from_pose(boundary=b, pose_x=inputs.pose_x, pose_y=inputs.pose_y)
                for b in self._boundaries
            )
            if v is not None
        )
        hazards = self._build_hazards(zone_check, occupancy, boundary_violations)

        snapshot = WorldModelSnapshot(
            sim_time_ns=inputs.sim_time_ns,
            pose_x=inputs.pose_x,
            pose_y=inputs.pose_y,
            heading_rad=inputs.heading_rad,
            occupancy_min_range_m=occupancy.min_range_m if occupancy.point_count else 0.0,
            occupancy_mean_range_m=occupancy.mean_range_m,
            forward_sector_clear=occupancy.forward_sector_clear,
            forward_clearance_m=occupancy.forward_clearance_m,
            inside_keepout=zone_check.inside_keepout,
            near_keepout=zone_check.near_keepout,
            inside_restricted=zone_check.inside_restricted,
            boundary_violations=tuple(v.boundary_id for v in boundary_violations),
            speed_limit_linear=zone_check.speed_limit_linear,
            speed_limit_angular=zone_check.speed_limit_angular,
        )

        if zone_check.has_violation:
            self._violation_streak += 1
        else:
            self._violation_streak = 0

        self._latest_snapshot = snapshot
        self._latest_hazards = hazards
        self._latest_zone_check = zone_check
        return snapshot

    @property
    def keepout_violation_streak(self) -> int:
        return self._violation_streak

    def _build_hazards(
        self,
        zone_check: ZoneCheckResult,
        occupancy: OccupancySummary,
        boundary_violations: tuple[BoundaryViolation, ...],
    ) -> tuple[HazardReport, ...]:
        out: list[HazardReport] = []
        for zone_id in zone_check.inside_keepout:
            out.append(
                HazardReport(
                    kind=HazardKind.KEEPOUT_VIOLATION,
                    reason_code=_REASON_CODES[HazardKind.KEEPOUT_VIOLATION],
                    severity="ERROR",
                    summary=f"keepout zone violated: {zone_id}",
                    attributes={"zone_id": zone_id},
                )
            )
        for zone_id in zone_check.near_keepout:
            out.append(
                HazardReport(
                    kind=HazardKind.KEEPOUT_PENDING,
                    reason_code=_REASON_CODES[HazardKind.KEEPOUT_PENDING],
                    severity="WARNING",
                    summary=f"approaching keepout zone: {zone_id}",
                    attributes={"zone_id": zone_id},
                )
            )
        for zone_id in zone_check.inside_restricted:
            out.append(
                HazardReport(
                    kind=HazardKind.RESTRICTED_SPEED_VIOLATION,
                    reason_code=_REASON_CODES[HazardKind.RESTRICTED_SPEED_VIOLATION],
                    severity="NOTICE",
                    summary=f"inside restricted-speed zone: {zone_id}",
                    attributes={
                        "zone_id": zone_id,
                        "speed_limit_linear": zone_check.speed_limit_linear,
                        "speed_limit_angular": zone_check.speed_limit_angular,
                    },
                )
            )
        for violation in boundary_violations:
            out.append(
                HazardReport(
                    kind=HazardKind.OPERATIONAL_BOUNDARY_VIOLATION,
                    reason_code=_REASON_CODES[
                        HazardKind.OPERATIONAL_BOUNDARY_VIOLATION
                    ],
                    severity="ERROR" if violation.severity == "major" else "WARNING",
                    summary=f"operational boundary violated: {violation.boundary_id}",
                    attributes={
                        "boundary_id": violation.boundary_id,
                        "distance_outside_m": violation.distance_outside_m,
                        "severity": violation.severity,
                    },
                )
            )
        if (
            occupancy.point_count > 0
            and occupancy.forward_clearance_m < self._forward_blocking
        ):
            out.append(
                HazardReport(
                    kind=HazardKind.OBSTACLE_BLOCKING,
                    reason_code=_REASON_CODES[HazardKind.OBSTACLE_BLOCKING],
                    severity="ERROR",
                    summary=f"forward obstacle within {occupancy.forward_clearance_m:.2f} m",
                    attributes={"clearance_m": occupancy.forward_clearance_m},
                )
            )
        elif (
            occupancy.point_count > 0
            and not occupancy.forward_sector_clear
        ):
            out.append(
                HazardReport(
                    kind=HazardKind.OBSTACLE_NEAR,
                    reason_code=_REASON_CODES[HazardKind.OBSTACLE_NEAR],
                    severity="WARNING",
                    summary=f"forward obstacle within {occupancy.forward_clearance_m:.2f} m",
                    attributes={"clearance_m": occupancy.forward_clearance_m},
                )
            )
        return tuple(out)
