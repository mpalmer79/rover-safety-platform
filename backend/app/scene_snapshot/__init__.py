"""Scene-snapshot eligibility metadata (does not render screenshots)."""

from __future__ import annotations

from .models import (
    SNAPSHOT_DISCLAIMER,
    SNAPSHOT_STATUS_BAG_BACKED,
    SNAPSHOT_STATUS_FIXTURE,
    SNAPSHOT_STATUS_NOT_EXECUTED,
    SNAPSHOT_STATUS_UNAVAILABLE,
    SNAPSHOT_STATUSES,
    SceneSnapshot,
    SceneSnapshotEligibility,
)
from .pipeline import (
    build_snapshot_for_run,
    evaluate_eligibility,
    snapshot_eligibility_to_dict,
    snapshot_to_dict,
    write_snapshot_artefacts,
)


__all__ = [
    "SNAPSHOT_DISCLAIMER",
    "SNAPSHOT_STATUS_BAG_BACKED",
    "SNAPSHOT_STATUS_FIXTURE",
    "SNAPSHOT_STATUS_NOT_EXECUTED",
    "SNAPSHOT_STATUS_UNAVAILABLE",
    "SNAPSHOT_STATUSES",
    "SceneSnapshot",
    "SceneSnapshotEligibility",
    "build_snapshot_for_run",
    "evaluate_eligibility",
    "snapshot_eligibility_to_dict",
    "snapshot_to_dict",
    "write_snapshot_artefacts",
]
