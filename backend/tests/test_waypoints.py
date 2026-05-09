"""Tests for waypoint primitives and queue."""

from __future__ import annotations

import pytest

from app.mission.enums import WaypointStatus
from app.mission.waypoints import Waypoint, WaypointProgress, WaypointQueue


def _wp(name: str = "w1", x: float = 1.0, y: float = 0.0) -> Waypoint:
    return Waypoint(
        waypoint_id=name,
        pose_x=x,
        pose_y=y,
        heading_rad=0.0,
        position_tolerance=0.20,
        heading_tolerance=0.40,
        timeout_seconds=10.0,
    )


def test_waypoint_validates_fields() -> None:
    with pytest.raises(ValueError):
        Waypoint(
            waypoint_id="",
            pose_x=0.0,
            pose_y=0.0,
            heading_rad=0.0,
            position_tolerance=0.10,
            heading_tolerance=0.10,
            timeout_seconds=1.0,
        )
    with pytest.raises(ValueError):
        Waypoint(
            waypoint_id="w",
            pose_x=0.0,
            pose_y=0.0,
            heading_rad=0.0,
            position_tolerance=0.0,
            heading_tolerance=0.10,
            timeout_seconds=1.0,
        )
    with pytest.raises(ValueError):
        Waypoint(
            waypoint_id="w",
            pose_x=0.0,
            pose_y=0.0,
            heading_rad=0.0,
            position_tolerance=0.10,
            heading_tolerance=0.10,
            timeout_seconds=0.0,
        )


def test_queue_iteration() -> None:
    q = WaypointQueue((_wp("w1"), _wp("w2", x=2.0)))
    assert q.total == 2
    assert q.remaining == 2
    assert q.peek().waypoint_id == "w1"
    q.pop_completed()
    assert q.completed_count == 1
    assert q.peek().waypoint_id == "w2"
    q.pop_timed_out()
    assert q.timed_out_count == 1
    assert q.is_empty
    assert q.progress_fraction() == 1.0


def test_queue_abort_remaining() -> None:
    q = WaypointQueue((_wp("w1"), _wp("w2"), _wp("w3")))
    q.pop_completed()
    aborted = q.abort_remaining()
    assert tuple(w.waypoint_id for w in aborted) == ("w2", "w3")
    assert q.aborted_count == 2
    assert q.is_empty


def test_progress_with_status() -> None:
    p = WaypointProgress(
        waypoint=_wp(),
        status=WaypointStatus.ACTIVE,
        started_at_ms=100,
    )
    completed = p.with_status(WaypointStatus.COMPLETED, now_ms=500)
    assert completed.status == WaypointStatus.COMPLETED
    assert completed.completed_at_ms == 500
    timed_out = p.with_status(WaypointStatus.TIMED_OUT, now_ms=900)
    assert timed_out.completed_at_ms == 900
