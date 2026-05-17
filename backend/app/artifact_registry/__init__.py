"""Deterministic artifact registry: hashes, lifecycle, hydration."""

from __future__ import annotations

from .deterministic_hash import (
    hash_bytes,
    hash_file,
    hashes_match,
    short_hash,
)
from .hydration import (
    hydrate_registry,
    hydration_report_to_dict,
)
from .lifecycle import (
    can_promote,
    is_authoritative,
    is_deprecated,
    lifecycle_for_integrity,
)
from .manifest import (
    REGISTRY_RELATIVE_PATH,
    default_registry_path,
    load_registry,
    registry_from_dict,
    registry_to_dict,
    write_registry,
)
from .models import (
    ARTIFACT_KIND_SPATIAL_REPLAY,
    ArtifactFile,
    ArtifactRecord,
    ArtifactRegistry,
    INTEGRITY_FAILED,
    INTEGRITY_MISSING,
    INTEGRITY_PARTIAL,
    INTEGRITY_PASSED,
    INTEGRITY_UNVERIFIED,
    LIFECYCLE_CANONICAL,
    LIFECYCLE_COMMITTED,
    LIFECYCLE_DEPRECATED,
    LIFECYCLE_GENERATED,
    LIFECYCLE_HYDRATED,
    LIFECYCLE_VERIFIED,
)
from .registry import (
    discover_run_files,
    find_record,
    integrity_for_run_id,
    list_authoritative_records,
    load_registry_or_empty,
)
from .reporter import (
    render_hydration_markdown,
    render_registry_markdown,
)
from .validation import (
    aggregate_integrity,
    verify_artifact,
    verify_registry,
)

__all__ = [
    "ARTIFACT_KIND_SPATIAL_REPLAY",
    "ArtifactFile",
    "ArtifactRecord",
    "ArtifactRegistry",
    "INTEGRITY_FAILED",
    "INTEGRITY_MISSING",
    "INTEGRITY_PARTIAL",
    "INTEGRITY_PASSED",
    "INTEGRITY_UNVERIFIED",
    "LIFECYCLE_CANONICAL",
    "LIFECYCLE_COMMITTED",
    "LIFECYCLE_DEPRECATED",
    "LIFECYCLE_GENERATED",
    "LIFECYCLE_HYDRATED",
    "LIFECYCLE_VERIFIED",
    "REGISTRY_RELATIVE_PATH",
    "aggregate_integrity",
    "can_promote",
    "default_registry_path",
    "discover_run_files",
    "find_record",
    "hash_bytes",
    "hash_file",
    "hashes_match",
    "hydrate_registry",
    "hydration_report_to_dict",
    "integrity_for_run_id",
    "is_authoritative",
    "is_deprecated",
    "lifecycle_for_integrity",
    "list_authoritative_records",
    "load_registry",
    "load_registry_or_empty",
    "registry_from_dict",
    "registry_to_dict",
    "render_hydration_markdown",
    "render_registry_markdown",
    "short_hash",
    "verify_artifact",
    "verify_registry",
    "write_registry",
]
