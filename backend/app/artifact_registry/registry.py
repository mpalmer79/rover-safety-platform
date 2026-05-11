"""High-level registry helpers used by the CLI and frontend tests."""

from __future__ import annotations

from pathlib import Path

from .deterministic_hash import hash_file
from .lifecycle import is_authoritative, is_deprecated
from .manifest import default_registry_path, load_registry
from .models import (
    ARTIFACT_KIND_SPATIAL_REPLAY,
    INTEGRITY_PASSED,
    ArtifactFile,
    ArtifactRecord,
    ArtifactRegistry,
)


def list_authoritative_records(
    registry: ArtifactRegistry,
) -> tuple[ArtifactRecord, ...]:
    """Return records the UI is allowed to render."""

    return tuple(
        r
        for r in registry.records
        if is_authoritative(r.lifecycle) and not is_deprecated(r.lifecycle)
    )


def find_record(
    registry: ArtifactRegistry, run_id: str
) -> ArtifactRecord | None:
    for r in registry.records:
        if r.run_id == run_id:
            return r
    return None


def discover_run_files(run_dir: Path) -> tuple[ArtifactFile, ...]:
    """Walk a ``spatial-replay/runs/<run_id>/`` directory and return
    one :class:`ArtifactFile` per regular file, sorted by path.

    The returned files have empty ``expected_hash`` — callers fill
    that in by computing the hash. The function never recurses into
    hidden or backup files.
    """

    files: list[ArtifactFile] = []
    base = Path(run_dir)
    if not base.exists():
        return ()
    for path in sorted(base.rglob("*")):
        if not path.is_file():
            continue
        if path.name.startswith(".") or path.name.endswith("~"):
            continue
        rel = path.relative_to(base.parent.parent)  # spatial-replay-rooted
        files.append(
            ArtifactFile(
                relative_path=str(rel),
                expected_hash="",
                size_bytes=path.stat().st_size,
                description="",
            )
        )
    return tuple(files)


def integrity_for_run_id(
    registry: ArtifactRegistry, run_id: str, *, artefact_root: Path
) -> str:
    """Return the integrity string for the named record.

    Returns ``"missing"`` when the run isn't registered.
    """

    record = find_record(registry, run_id)
    if record is None:
        return "missing"
    # Recompute on disk to avoid trusting a stale registry value.
    fail = False
    miss = False
    if not record.files:
        return record.integrity
    for f in record.files:
        on_disk = Path(artefact_root) / f.relative_path
        digest = hash_file(on_disk)
        if not digest:
            miss = True
            continue
        if digest.lower() != f.expected_hash.lower():
            fail = True
    if fail:
        return "failed"
    if miss:
        return "partial"
    return INTEGRITY_PASSED


def load_registry_or_empty(repo_root: Path) -> ArtifactRegistry:
    """Convenience helper for callers that prefer a non-null result."""

    reg = load_registry(default_registry_path(repo_root))
    if reg is not None:
        return reg
    return ArtifactRegistry(
        generated_at_utc="",
        schema_version="phase18-1",
        artefact_root="spatial-replay",
        records=(),
    )


__all__ = [
    "ARTIFACT_KIND_SPATIAL_REPLAY",
    "default_registry_path",
    "discover_run_files",
    "find_record",
    "integrity_for_run_id",
    "list_authoritative_records",
    "load_registry_or_empty",
]
