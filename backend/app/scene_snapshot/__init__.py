"""Phase 19 reviewer scene-snapshot readiness layer.

The platform is **not safety-certified.** This package does NOT
render screenshots. It builds deterministic, evidence-backed
metadata that describes whether a reviewer-grade scene snapshot
COULD be produced — and, when one exists on disk, links to it.

The snapshot is the immersive operator scene captured at a
specific scrubber index in a specific playback mode. Today the
only `derivation_source` that qualifies for a bag-backed snapshot
is `bag_backed`; a fixture-derived run produces an honest
``not_executed`` outcome with the exact missing inputs listed.
"""

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
