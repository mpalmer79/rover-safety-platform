"""Phase 18 artifact-governance package.

The platform is **not safety-certified.** This package owns the
canonical lifecycle of every committed replay artefact: discovery,
deterministic hashing, integrity verification, hydration, and
honest reporting of missing or out-of-date assets.
"""

from __future__ import annotations

from .deterministic_hash import (
    HASH_PREFIX_LENGTH,
    hash_bytes,
    hash_file,
    hashes_match,
    short_hash,
)
from .hydration import hydrate_registry, hydration_report_to_dict
from .lifecycle import (
    can_promote,
    is_authoritative,
    is_deprecated,
    lifecycle_for_integrity,
)
from .manifest import (
    REGISTRY_RELATIVE_PATH,
    REGISTRY_SCHEMA_VERSION,
    default_registry_path,
    file_to_dict,
    load_registry,
    record_to_dict,
    registry_from_dict,
    registry_to_dict,
    write_registry,
)
from .models import (
    ARTIFACT_GOVERNANCE_DISCLAIMER,
    ARTIFACT_KIND_SPATIAL_REPLAY,
    ARTIFACT_KINDS,
    INTEGRITY_FAILED,
    INTEGRITY_MISSING,
    INTEGRITY_PARTIAL,
    INTEGRITY_PASSED,
    INTEGRITY_STATES,
    INTEGRITY_UNVERIFIED,
    LIFECYCLE_CANONICAL,
    LIFECYCLE_COMMITTED,
    LIFECYCLE_DEPRECATED,
    LIFECYCLE_GENERATED,
    LIFECYCLE_HYDRATED,
    LIFECYCLE_STATES,
    LIFECYCLE_VERIFIED,
    ArtifactFile,
    ArtifactRecord,
    ArtifactRegistry,
    HydrationOutcome,
    HydrationReport,
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
    "ARTIFACT_GOVERNANCE_DISCLAIMER",
    "ARTIFACT_KIND_SPATIAL_REPLAY",
    "ARTIFACT_KINDS",
    "HASH_PREFIX_LENGTH",
    "INTEGRITY_FAILED",
    "INTEGRITY_MISSING",
    "INTEGRITY_PARTIAL",
    "INTEGRITY_PASSED",
    "INTEGRITY_STATES",
    "INTEGRITY_UNVERIFIED",
    "LIFECYCLE_CANONICAL",
    "LIFECYCLE_COMMITTED",
    "LIFECYCLE_DEPRECATED",
    "LIFECYCLE_GENERATED",
    "LIFECYCLE_HYDRATED",
    "LIFECYCLE_STATES",
    "LIFECYCLE_VERIFIED",
    "REGISTRY_RELATIVE_PATH",
    "REGISTRY_SCHEMA_VERSION",
    "ArtifactFile",
    "ArtifactRecord",
    "ArtifactRegistry",
    "HydrationOutcome",
    "HydrationReport",
    "aggregate_integrity",
    "can_promote",
    "default_registry_path",
    "discover_run_files",
    "file_to_dict",
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
    "record_to_dict",
    "registry_from_dict",
    "registry_to_dict",
    "render_hydration_markdown",
    "render_registry_markdown",
    "short_hash",
    "verify_artifact",
    "verify_registry",
    "write_registry",
]
