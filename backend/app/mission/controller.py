"""Pure-pursuit-style waypoint controller.

Given the rover's pose and the active waypoint, produces a (linear,
angular) target velocity that the orchestrator wraps into a
:class:`RequestedMotionCommand`. The controller is intentionally
simple — it is a deterministic geometric controller, not a planner —
because the platform's value comes from architectural discipline
rather than control sophistication. Nav2 will replace this layer in a
later phase if needed; the interface stays narrow so the swap is
local.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from app.mission.waypoints import Waypoint


@dataclass(frozen=True)
class WaypointSteering:
    """Per-tick steering command produced by the controller."""

    linear_velocity: float
    angular_velocity: float
    distance_to_goal_m: float
    heading_error_rad: float
    in_position: bool
    in_heading: bool

    @property
    def is_reached(self) -> bool:
        return self.in_position and self.in_heading


class WaypointController:
    """Geometric pure-pursuit-like controller.

    The controller is a single class so callers can swap it out (e.g.
    for a Nav2-driven controller) without touching the orchestrator.
    """

    def __init__(
        self,
        *,
        approach_distance_m: float = 0.40,
        kp_angular: float = 1.2,
        deceleration_floor: float = 0.5,
    ) -> None:
        """Constructs the controller.

        Above ``approach_distance_m`` the rover drives at the
        configured ``max_linear``. Between the waypoint's
        ``position_tolerance`` and ``approach_distance_m`` the linear
        velocity decays linearly from ``max_linear`` to
        ``deceleration_floor * max_linear``, ensuring the rover always
        carries enough momentum to cross the tolerance circle.
        """

        self._approach = approach_distance_m
        self._kp_angular = kp_angular
        self._deceleration_floor = max(0.0, min(1.0, deceleration_floor))

    def steer(
        self,
        *,
        waypoint: Waypoint,
        pose_x: float,
        pose_y: float,
        heading_rad: float,
        max_linear: float,
        max_angular: float,
    ) -> WaypointSteering:
        dx = waypoint.pose_x - pose_x
        dy = waypoint.pose_y - pose_y
        distance = math.hypot(dx, dy)

        in_position = distance <= waypoint.position_tolerance
        if in_position:
            heading_error = _wrap_angle(waypoint.heading_rad - heading_rad)
            in_heading = abs(heading_error) <= waypoint.heading_tolerance
            if in_heading:
                return WaypointSteering(
                    linear_velocity=0.0,
                    angular_velocity=0.0,
                    distance_to_goal_m=distance,
                    heading_error_rad=heading_error,
                    in_position=True,
                    in_heading=True,
                )
            angular = _bounded(self._kp_angular * heading_error, max_angular)
            return WaypointSteering(
                linear_velocity=0.0,
                angular_velocity=angular,
                distance_to_goal_m=distance,
                heading_error_rad=heading_error,
                in_position=True,
                in_heading=False,
            )

        # Heading toward the goal. Use atan2 once and steer toward it.
        heading_to_goal = math.atan2(dy, dx)
        heading_error = _wrap_angle(heading_to_goal - heading_rad)
        in_heading = abs(heading_error) <= waypoint.heading_tolerance

        # Linear velocity profile: full speed beyond ``approach``,
        # linear decay between ``position_tolerance`` and ``approach``,
        # bounded below by ``deceleration_floor * max_linear`` so the
        # rover always crosses the tolerance circle. If heading error
        # is large the linear command shrinks via cos() so the rover
        # turns in place rather than arcing into the goal.
        if distance >= self._approach:
            speed_scale = 1.0
        else:
            decel_span = max(1e-6, self._approach - waypoint.position_tolerance)
            decel_progress = max(
                0.0,
                (distance - waypoint.position_tolerance) / decel_span,
            )
            speed_scale = self._deceleration_floor + (
                1.0 - self._deceleration_floor
            ) * decel_progress
        heading_scale = max(0.0, math.cos(heading_error))
        linear = _bounded(max_linear * speed_scale * heading_scale, max_linear)
        angular = _bounded(self._kp_angular * heading_error, max_angular)

        return WaypointSteering(
            linear_velocity=linear,
            angular_velocity=angular,
            distance_to_goal_m=distance,
            heading_error_rad=heading_error,
            in_position=False,
            in_heading=in_heading,
        )


def _wrap_angle(theta: float) -> float:
    return ((theta + math.pi) % (2 * math.pi)) - math.pi


def _bounded(value: float, limit: float) -> float:
    if limit < 0:
        return 0.0
    if value > limit:
        return limit
    if value < -limit:
        return -limit
    return value
