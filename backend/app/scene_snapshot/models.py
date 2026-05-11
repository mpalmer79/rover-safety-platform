"""Typed models for the Phase 19 reviewer scene-snapshot layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


SNAPSHOT_DISCLAIMER: str = (
    "This project is not safety-certified. Reviewer scene snapshots "
    "are deterministic metadata, never live telemetry. A bag-backed "
    "snapshot requires real bag-backed spatial replay artefacts."
)


SNAPSHOT_STATUS_BAG_BACKED: str = "bag_backed"
SNAPSHOT_STATUS_FIXTURE: str = "fixture"
SNAPSHOT_STATUS_NOT_EXECUTED: str = "not_executed"
SNAPSHOT_STATUS_UNAVAILABLE: str = "unavailable"


SNAPSHOT_STATUSES: tuple[str, ...] = (
    SNAPSHOT_STATUS_BAG_BACKED,
    SNAPSHOT_STATUS_FIXTURE,
    SNAPSHOT_STATUS_NOT_EXECUTED,
    SNAPSHOT_STATUS_UNAVAILABLE,
)


@dataclass(frozen=True)
class SceneSnapshotEligibility:
    """Outcome of the snapshot eligibility check for one run."""

    run_id: str
    status: str  # SNAPSHOT_STATUS_*
    eligible_for_bag_backed_snapshot: bool
    derivation_source: str
    bag_status: str
    integrity: str
    missing_inputs: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class SceneSnapshot:
    """A reviewer scene-snapshot description.

    The platform never generates a screenshot binary. The snapshot
    is a description of what a reviewer would render, plus links
    into the registry + spatial-replay + bag-manifest.
    """

    run_id: str
    status: str
    scene_source: str
    derivation_source: str
    bag_status: str
    integrity: str
    artifact_registry_entry: str
    spatial_replay_path: str
    artifact_hash_chain: tuple[Mapping[str, str], ...] = ()
    missing_inputs: tuple[str, ...] = ()
    reviewer_export_ready: bool = False
    generated_at_utc: str = ""
    notes: tuple[str, ...] = ()
