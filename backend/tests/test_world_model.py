"""Tests for the bounded world model."""

from __future__ import annotations

import pytest

from app.domain.enums import SensorStatus, SensorType
from app.domain.sensors import LiDARReading, SensorFrame
from app.world_model.boundaries import OperationalBoundary, BoundaryViolation
from app.world_model.enums import HazardKind
from app.world_model.keepout import (
    KeepoutZone,
    RestrictedZone,
    evaluate_zones,
)
from app.world_model.world_model import WorldModel, WorldModelInputs


def _frame(min_range: float = 2.0, points: int = 720) -> SensorFrame:
    if points == 0:
        return SensorFrame()
    return SensorFrame(
        lidar=LiDARReading(
            sensor_id="r/lidar",
            sensor_type=SensorType.LIDAR,
            timestamp_ms=0,
            status=SensorStatus.HEALTHY,
            confidence=0.9,
            source="t",
            sequence_number=1,
            min_range_m=min_range,
            max_range_m=10.0,
            mean_range_m=5.0,
            point_count=points,
        )
    )


def test_keepout_zone_validates_extent() -> None:
    with pytest.raises(ValueError):
        KeepoutZone(zone_id="kz", min_x=0.0, min_y=0.0, max_x=-1.0, max_y=1.0)
    with pytest.raises(ValueError):
        KeepoutZone(zone_id="", min_x=0.0, min_y=0.0, max_x=1.0, max_y=1.0)


def test_evaluate_zones_finds_inside_violation() -> None:
    keepout = KeepoutZone(zone_id="kz", min_x=0.0, min_y=0.0, max_x=1.0, max_y=1.0)
    result = evaluate_zones(
        pose_x=0.5, pose_y=0.5, keepouts=[keepout], restricted=[]
    )
    assert result.has_violation
    assert "kz" in result.inside_keepout


def test_evaluate_zones_finds_pending() -> None:
    keepout = KeepoutZone(
        zone_id="kz",
        min_x=0.0,
        min_y=0.0,
        max_x=1.0,
        max_y=1.0,
        margin_m=0.40,
    )
    result = evaluate_zones(
        pose_x=-0.20, pose_y=0.5, keepouts=[keepout], restricted=[]
    )
    assert "kz" in result.near_keepout
    assert result.is_pending()
    assert not result.has_violation


def test_evaluate_zones_clamps_to_minimum_speed_limit() -> None:
    rz = RestrictedZone(
        zone_id="rz",
        min_x=0.0,
        min_y=0.0,
        max_x=2.0,
        max_y=2.0,
        max_linear_velocity=0.15,
        max_angular_velocity=0.3,
    )
    result = evaluate_zones(pose_x=1.0, pose_y=1.0, keepouts=[], restricted=[rz])
    assert "rz" in result.inside_restricted
    assert result.speed_limit_linear == 0.15
    assert result.speed_limit_angular == 0.3


def test_boundary_violation_classifies_minor_vs_major() -> None:
    boundary = OperationalBoundary(
        boundary_id="b", min_x=-5.0, min_y=-5.0, max_x=5.0, max_y=5.0
    )
    minor = BoundaryViolation.from_pose(boundary=boundary, pose_x=5.10, pose_y=0.0)
    major = BoundaryViolation.from_pose(boundary=boundary, pose_x=6.0, pose_y=0.0)
    inside = BoundaryViolation.from_pose(boundary=boundary, pose_x=0.0, pose_y=0.0)
    assert minor is not None and minor.severity == "minor"
    assert major is not None and major.severity == "major"
    assert inside is None


def test_world_model_emits_keepout_violation_hazard() -> None:
    model = WorldModel(
        keepouts=(KeepoutZone(zone_id="kz", min_x=0.0, min_y=0.0, max_x=1.0, max_y=1.0),)
    )
    snap = model.update(
        WorldModelInputs(
            pose_x=0.5, pose_y=0.5, heading_rad=0.0, sim_time_ns=0, sensor_frame=_frame()
        )
    )
    assert "kz" in snap.inside_keepout
    kinds = {h.kind for h in model.latest_hazards}
    assert HazardKind.KEEPOUT_VIOLATION in kinds


def test_world_model_emits_obstacle_blocking_hazard() -> None:
    model = WorldModel()
    snap = model.update(
        WorldModelInputs(
            pose_x=0.0,
            pose_y=0.0,
            heading_rad=0.0,
            sim_time_ns=0,
            sensor_frame=_frame(min_range=0.10),
        )
    )
    assert not snap.forward_sector_clear
    kinds = {h.kind for h in model.latest_hazards}
    assert HazardKind.OBSTACLE_BLOCKING in kinds


def test_world_model_emits_no_hazards_when_healthy() -> None:
    model = WorldModel(boundaries=(OperationalBoundary("b", -5.0, -5.0, 5.0, 5.0),))
    snap = model.update(
        WorldModelInputs(
            pose_x=0.0, pose_y=0.0, heading_rad=0.0, sim_time_ns=0, sensor_frame=_frame()
        )
    )
    assert not snap.boundary_violations
    assert not model.latest_hazards


def test_world_model_emits_boundary_violation_hazard() -> None:
    model = WorldModel(
        boundaries=(OperationalBoundary("b", -5.0, -5.0, 5.0, 5.0),)
    )
    model.update(
        WorldModelInputs(
            pose_x=10.0, pose_y=0.0, heading_rad=0.0, sim_time_ns=0, sensor_frame=_frame()
        )
    )
    kinds = {h.kind for h in model.latest_hazards}
    assert HazardKind.OPERATIONAL_BOUNDARY_VIOLATION in kinds
