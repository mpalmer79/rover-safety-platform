"""Typed models for the Phase 18 artifact-governance layer.

The platform is **not safety-certified.** This package owns the
canonical lifecycle of every committed replay artefact: discovery,
deterministic hashing, integrity verification, hydration, and
honest reporting of missing or out-of-date assets.

The Phase 17C CI failure highlighted that the frontend assumed
artefacts existed on disk while the CI runner could be invoked in
states where they did not. The artefact registry is the single
source of truth that fixes that gap.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


ARTIFACT_GOVERNANCE_DISCLAIMER: str = (
    "This project is not safety-certified. The artifact-registry "
    "layer is read-only with respect to runtime evidence; it indexes "
    "and verifies committed artefacts and never invents replay data."
)


# Lifecycle vocabulary. Adding a new value requires updating the
# validator + the docs.
LIFECYCLE_GENERATED: str = "generated"
LIFECYCLE_HYDRATED: str = "hydrated"
LIFECYCLE_COMMITTED: str = "committed"
LIFECYCLE_VERIFIED: str = "verified"
LIFECYCLE_CANONICAL: str = "canonical"
LIFECYCLE_DEPRECATED: str = "deprecated"

LIFECYCLE_STATES: tuple[str, ...] = (
    LIFECYCLE_GENERATED,
    LIFECYCLE_HYDRATED,
    LIFECYCLE_COMMITTED,
    LIFECYCLE_VERIFIED,
    LIFECYCLE_CANONICAL,
    LIFECYCLE_DEPRECATED,
)


# Artefact-kind vocabulary. Phase 18 ships with one kind
# (``spatial_replay``); future phases may add more.
ARTIFACT_KIND_SPATIAL_REPLAY: str = "spatial_replay"

ARTIFACT_KINDS: tuple[str, ...] = (ARTIFACT_KIND_SPATIAL_REPLAY,)


# Integrity-status vocabulary.
INTEGRITY_PASSED: str = "passed"
INTEGRITY_PARTIAL: str = "partial"
INTEGRITY_FAILED: str = "failed"
INTEGRITY_MISSING: str = "missing"
INTEGRITY_UNVERIFIED: str = "unverified"

INTEGRITY_STATES: tuple[str, ...] = (
    INTEGRITY_PASSED,
    INTEGRITY_PARTIAL,
    INTEGRITY_FAILED,
    INTEGRITY_MISSING,
    INTEGRITY_UNVERIFIED,
)


@dataclass(frozen=True)
class ArtifactFile:
    """A single file inside a registered artefact.

    The deterministic hash is the sha256 of the canonical bytes on
    disk; the registry stores both the expected hash (committed) and
    the computed hash (recomputed at hydration time). A mismatch
    flags a deterministic regression.
    """

    relative_path: str
    expected_hash: str
    size_bytes: int
    description: str = ""


@dataclass(frozen=True)
class ArtifactRecord:
    """One entry in the canonical-artifacts registry.

    ``run_id`` is the directory under
    ``spatial-replay/runs/<run_id>/`` (or future artefact roots).
    ``derivation_source`` mirrors the spatial-replay artefact's own
    derivation source — the registry never overrides it.
    """

    run_id: str
    kind: str
    derivation_source: str
    bag_status: str
    lifecycle: str
    integrity: str
    files: tuple[ArtifactFile, ...]
    related_mission_id: str = ""
    related_scenario_id: str = ""
    notes: tuple[str, ...] = ()
    generated_at_utc: str = ""


@dataclass(frozen=True)
class ArtifactRegistry:
    """The canonical registry of all committed replay artefacts."""

    generated_at_utc: str
    schema_version: str
    artefact_root: str
    records: tuple[ArtifactRecord, ...]
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class HydrationOutcome:
    """Outcome of a single hydration pass on one artefact."""

    run_id: str
    rebuilt: bool
    integrity: str
    expected_hashes: Mapping[str, str]
    computed_hashes: Mapping[str, str]
    drift: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class HydrationReport:
    """Aggregate report of a hydration run."""

    generated_at_utc: str
    registry_path: str
    artefact_root: str
    outcomes: tuple[HydrationOutcome, ...]
    overall_integrity: str
    notes: tuple[str, ...] = ()


__all__ = [
    "ARTIFACT_GOVERNANCE_DISCLAIMER",
    "LIFECYCLE_GENERATED",
    "LIFECYCLE_HYDRATED",
    "LIFECYCLE_COMMITTED",
    "LIFECYCLE_VERIFIED",
    "LIFECYCLE_CANONICAL",
    "LIFECYCLE_DEPRECATED",
    "LIFECYCLE_STATES",
    "ARTIFACT_KIND_SPATIAL_REPLAY",
    "ARTIFACT_KINDS",
    "INTEGRITY_PASSED",
    "INTEGRITY_PARTIAL",
    "INTEGRITY_FAILED",
    "INTEGRITY_MISSING",
    "INTEGRITY_UNVERIFIED",
    "INTEGRITY_STATES",
    "ArtifactFile",
    "ArtifactRecord",
    "ArtifactRegistry",
    "HydrationOutcome",
    "HydrationReport",
]
