"""A small deterministic differential-drive integration model.

The model integrates an authorized command into a new
:class:`RoverState`. It is intentionally minimal: physics fidelity is not
the goal here, repeatability and explainability are.
"""

from __future__ import annotations

import math

from app.domain.motion import AuthorizedMotionCommand
from app.domain.rover_state import RoverState


class DifferentialDriveModel:
    """Two-wheel differential drive with no slip or compliance.

    The supervisor's authorized linear and angular velocities are
    applied as the rover's instantaneous velocities for the duration of
    the tick. The pose updates by the resulting motion.
    """

    def __init__(
        self,
        *,
        wheel_separation_m: float = 0.30,
        wheel_radius_m: float = 0.05,
        slip_factor: float = 0.0,
    ) -> None:
        if wheel_separation_m <= 0:
            raise ValueError("wheel_separation_m must be positive")
        if wheel_radius_m <= 0:
            raise ValueError("wheel_radius_m must be positive")
        self._wheel_separation_m = wheel_separation_m
        self._wheel_radius_m = wheel_radius_m
        self._slip_factor = slip_factor

    @property
    def wheel_separation_m(self) -> float:
        return self._wheel_separation_m

    @property
    def wheel_radius_m(self) -> float:
        return self._wheel_radius_m

    def step(
        self,
        *,
        state: RoverState,
        authorized: AuthorizedMotionCommand,
        dt_ms: int,
        now_ms: int,
        slip_factor: float | None = None,
    ) -> RoverState:
        if dt_ms <= 0:
            raise ValueError("dt_ms must be positive")
        dt = dt_ms / 1000.0
        slip = float(slip_factor if slip_factor is not None else self._slip_factor)
        slip = max(0.0, min(1.0, slip))
        actual_linear = authorized.linear_velocity * (1.0 - slip)
        actual_angular = authorized.angular_velocity * (1.0 - slip)

        # Heading update at midpoint for slightly better integration.
        new_heading = state.heading_rad + actual_angular * dt
        avg_heading = (state.heading_rad + new_heading) * 0.5
        dx = actual_linear * math.cos(avg_heading) * dt
        dy = actual_linear * math.sin(avg_heading) * dt

        new_pose_x = state.pose_x + dx
        new_pose_y = state.pose_y + dy
        new_distance = state.distance_traveled_m + abs(actual_linear) * dt

        return state.with_updates(
            pose_x=new_pose_x,
            pose_y=new_pose_y,
            heading_rad=_wrap_angle(new_heading),
            linear_velocity=actual_linear,
            angular_velocity=actual_angular,
            last_update_ms=now_ms,
            distance_traveled_m=new_distance,
        )

    def wheel_speeds(self, *, linear: float, angular: float) -> tuple[float, float]:
        """Translate body-frame velocities to (left, right) angular wheel speeds."""

        v_left = (linear - angular * self._wheel_separation_m * 0.5) / self._wheel_radius_m
        v_right = (linear + angular * self._wheel_separation_m * 0.5) / self._wheel_radius_m
        return v_left, v_right


def _wrap_angle(theta: float) -> float:
    """Wrap an angle into [-pi, pi]."""

    return ((theta + math.pi) % (2 * math.pi)) - math.pi
