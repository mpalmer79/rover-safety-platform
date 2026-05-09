"""Bounded world model.

A deterministic, replayable approximation of the rover's operational
context. The world model intentionally does NOT implement SLAM,
probabilistic mapping, or full perception. It maintains:

* a small set of declared keepout zones,
* a small set of declared restricted-speed zones,
* a small set of declared operational boundaries,
* a coarse occupancy summary derived from LiDAR statistics,
* a list of currently asserted hazards.

Snapshots are emitted periodically and recorded to
``world_model_snapshots.jsonl`` for replay parity.

The world model is consumed by:

* the mission orchestrator (for keepout / restricted-zone awareness),
* the recovery framework (to decide between back-up vs wait-for-sensor),
* the mission diagnostics surface (for operator visibility).

It does NOT own safety state. The supervisor in :mod:`app.safety`
remains the only authority over ``/safety/state``.
"""

from app.world_model.boundaries import (
    BoundaryViolation,
    OperationalBoundary,
)
from app.world_model.enums import HazardKind, ZoneKind
from app.world_model.keepout import (
    KeepoutZone,
    RestrictedZone,
    ZoneCheckResult,
    evaluate_zones,
)
from app.world_model.occupancy import (
    OccupancySummary,
    summarise_lidar,
)
from app.world_model.snapshot import WorldModelSnapshot
from app.world_model.world_model import (
    HazardReport,
    WorldModel,
    WorldModelInputs,
)

__all__ = [
    "BoundaryViolation",
    "HazardKind",
    "HazardReport",
    "KeepoutZone",
    "OccupancySummary",
    "OperationalBoundary",
    "RestrictedZone",
    "WorldModel",
    "WorldModelInputs",
    "WorldModelSnapshot",
    "ZoneCheckResult",
    "ZoneKind",
    "evaluate_zones",
    "summarise_lidar",
]
