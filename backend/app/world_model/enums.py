"""Controlled vocabularies used by the world model."""

from __future__ import annotations

from enum import Enum


class ZoneKind(str, Enum):
    """Type of declared region within the operational area."""

    KEEPOUT = "keepout"
    RESTRICTED_SPEED = "restricted_speed"
    OPERATIONAL_BOUNDARY = "operational_boundary"


class HazardKind(str, Enum):
    """Stable vocabulary for hazards reported by the world model.

    These are operational hazards observable to the deterministic
    runtime — not perception-level objects. Each value has a stable
    ``reason_code`` companion in :mod:`app.world_model.world_model`.
    """

    KEEPOUT_PENDING = "keepout_pending"
    KEEPOUT_VIOLATION = "keepout_violation"
    RESTRICTED_SPEED_VIOLATION = "restricted_speed_violation"
    OPERATIONAL_BOUNDARY_VIOLATION = "operational_boundary_violation"
    OBSTACLE_NEAR = "obstacle_near"
    OBSTACLE_BLOCKING = "obstacle_blocking"
