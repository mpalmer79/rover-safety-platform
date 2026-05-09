"""Coarse occupancy summary derived from LiDAR statistics.

The deterministic engine does not maintain a full 2D occupancy grid;
that would be a perception-stack feature out of scope for Phase 2.
Instead the world model carries a compact summary derived from a
:class:`LiDARReading`: minimum range, mean range, and a coarse
"occupancy belief" that downstream code uses to decide whether the
forward sector looks clear.

The summary is intentionally simple: it captures enough signal to
support recovery decisions and operator visibility without committing
to a perception stack.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from app.domain.sensors import LiDARReading


@dataclass(frozen=True)
class OccupancySummary:
    """Summary derived from one LiDAR reading."""

    sequence_number: int
    min_range_m: float
    mean_range_m: float
    point_count: int
    forward_sector_clear: bool
    forward_clearance_m: float
    """Conservative forward clearance estimate, in metres."""

    @classmethod
    def empty(cls) -> "OccupancySummary":
        return cls(
            sequence_number=0,
            min_range_m=float("inf"),
            mean_range_m=0.0,
            point_count=0,
            forward_sector_clear=False,
            forward_clearance_m=0.0,
        )


def summarise_lidar(
    reading: Optional[LiDARReading],
    *,
    forward_clear_threshold_m: float = 0.6,
) -> OccupancySummary:
    """Reduce a LiDAR reading to an occupancy summary.

    The simulation core's :class:`LiDARReading` carries summary
    statistics, not raw ranges, so this is essentially a 1-1 mapping
    plus a heuristic for ``forward_sector_clear``: if ``min_range_m``
    exceeds the threshold and the point count is non-zero, the forward
    sector is reported as clear.
    """

    if reading is None or reading.point_count == 0:
        return OccupancySummary.empty()
    forward_clearance = max(0.0, reading.min_range_m)
    return OccupancySummary(
        sequence_number=reading.sequence_number,
        min_range_m=reading.min_range_m,
        mean_range_m=reading.mean_range_m,
        point_count=reading.point_count,
        forward_sector_clear=forward_clearance >= forward_clear_threshold_m,
        forward_clearance_m=forward_clearance,
    )
