"""Integrity verification of registered artefacts."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .deterministic_hash import hash_file, hashes_match
from .models import (
    INTEGRITY_FAILED,
    INTEGRITY_MISSING,
    INTEGRITY_PARTIAL,
    INTEGRITY_PASSED,
    INTEGRITY_UNVERIFIED,
    ArtifactFile,
    ArtifactRecord,
    ArtifactRegistry,
)


def verify_artifact(
    record: ArtifactRecord, *, artefact_root: Path
) -> tuple[str, dict[str, str], list[str]]:
    """Return ``(integrity, computed_hashes, drift_messages)``.

    ``computed_hashes`` is keyed by relative path and contains the
    sha256 hex computed from disk; missing files produce empty
    strings. ``drift_messages`` enumerates per-file mismatches /
    missing files.
    """

    computed: dict[str, str] = {}
    drift: list[str] = []
    missing = 0
    mismatched = 0
    for f in record.files:
        on_disk = Path(artefact_root) / f.relative_path
        digest = hash_file(on_disk)
        computed[f.relative_path] = digest
        if not digest:
            missing += 1
            drift.append(f"missing file: {f.relative_path}")
            continue
        if not hashes_match(f.expected_hash, digest):
            mismatched += 1
            drift.append(
                f"hash mismatch: {f.relative_path} expected="
                f"{f.expected_hash[:12]} computed={digest[:12]}"
            )

    if not record.files:
        return (INTEGRITY_UNVERIFIED, computed, drift)
    if missing == len(record.files):
        return (INTEGRITY_MISSING, computed, drift)
    if missing == 0 and mismatched == 0:
        return (INTEGRITY_PASSED, computed, drift)
    if mismatched == 0:
        return (INTEGRITY_PARTIAL, computed, drift)
    return (INTEGRITY_FAILED, computed, drift)


def verify_registry(
    registry: ArtifactRegistry, *, artefact_root: Path
) -> dict[str, tuple[str, dict[str, str], list[str]]]:
    """Verify every record. Returns a dict keyed by ``run_id``."""

    out: dict[str, tuple[str, dict[str, str], list[str]]] = {}
    for r in registry.records:
        out[r.run_id] = verify_artifact(r, artefact_root=Path(artefact_root))
    return out


def aggregate_integrity(integrities: Iterable[str]) -> str:
    """Roll up many per-record integrities into one repo-level value."""

    values = list(integrities)
    if not values:
        return INTEGRITY_UNVERIFIED
    if all(v == INTEGRITY_PASSED for v in values):
        return INTEGRITY_PASSED
    if any(v == INTEGRITY_FAILED for v in values):
        return INTEGRITY_FAILED
    if all(v == INTEGRITY_MISSING for v in values):
        return INTEGRITY_MISSING
    return INTEGRITY_PARTIAL


__all__ = [
    "aggregate_integrity",
    "verify_artifact",
    "verify_registry",
]
