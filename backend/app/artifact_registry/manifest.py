"""Read + write the canonical artefacts registry JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .models import (
    ArtifactFile,
    ArtifactRecord,
    ArtifactRegistry,
)


REGISTRY_RELATIVE_PATH: str = "spatial-replay/registry/canonical-artifacts.json"
REGISTRY_SCHEMA_VERSION: str = "phase18-1"


def _coerce_file(raw: Mapping[str, Any]) -> ArtifactFile:
    return ArtifactFile(
        relative_path=str(raw.get("relative_path") or ""),
        expected_hash=str(raw.get("expected_hash") or ""),
        size_bytes=int(raw.get("size_bytes") or 0),
        description=str(raw.get("description") or ""),
    )


def _coerce_record(raw: Mapping[str, Any]) -> ArtifactRecord:
    files = tuple(_coerce_file(f) for f in raw.get("files", []) if isinstance(f, dict))
    notes = tuple(str(n) for n in raw.get("notes", ()))
    return ArtifactRecord(
        run_id=str(raw.get("run_id") or ""),
        kind=str(raw.get("kind") or ""),
        derivation_source=str(raw.get("derivation_source") or ""),
        bag_status=str(raw.get("bag_status") or ""),
        lifecycle=str(raw.get("lifecycle") or ""),
        integrity=str(raw.get("integrity") or "unverified"),
        files=files,
        related_mission_id=str(raw.get("related_mission_id") or ""),
        related_scenario_id=str(raw.get("related_scenario_id") or ""),
        notes=notes,
        generated_at_utc=str(raw.get("generated_at_utc") or ""),
    )


def registry_from_dict(payload: Mapping[str, Any]) -> ArtifactRegistry:
    records = tuple(
        _coerce_record(r) for r in payload.get("records", []) if isinstance(r, dict)
    )
    return ArtifactRegistry(
        generated_at_utc=str(payload.get("generated_at_utc") or ""),
        schema_version=str(payload.get("schema_version") or REGISTRY_SCHEMA_VERSION),
        artefact_root=str(payload.get("artefact_root") or "spatial-replay"),
        records=records,
        notes=tuple(str(n) for n in payload.get("notes", ())),
    )


def file_to_dict(file: ArtifactFile) -> dict[str, Any]:
    return {
        "relative_path": file.relative_path,
        "expected_hash": file.expected_hash,
        "size_bytes": file.size_bytes,
        "description": file.description,
    }


def record_to_dict(record: ArtifactRecord) -> dict[str, Any]:
    return {
        "run_id": record.run_id,
        "kind": record.kind,
        "derivation_source": record.derivation_source,
        "bag_status": record.bag_status,
        "lifecycle": record.lifecycle,
        "integrity": record.integrity,
        "related_mission_id": record.related_mission_id,
        "related_scenario_id": record.related_scenario_id,
        "notes": list(record.notes),
        "generated_at_utc": record.generated_at_utc,
        "files": [file_to_dict(f) for f in record.files],
    }


def registry_to_dict(registry: ArtifactRegistry) -> dict[str, Any]:
    return {
        "generated_at_utc": registry.generated_at_utc,
        "schema_version": registry.schema_version,
        "artefact_root": registry.artefact_root,
        "notes": list(registry.notes),
        "records": [record_to_dict(r) for r in registry.records],
    }


def load_registry(path: Path) -> ArtifactRegistry | None:
    """Read the registry JSON. Returns ``None`` when missing/invalid."""

    p = Path(path)
    if not p.exists():
        return None
    try:
        payload = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return registry_from_dict(payload)


def write_registry(registry: ArtifactRegistry, path: Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps(registry_to_dict(registry), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def default_registry_path(repo_root: Path) -> Path:
    return Path(repo_root) / REGISTRY_RELATIVE_PATH


__all__ = [
    "REGISTRY_RELATIVE_PATH",
    "REGISTRY_SCHEMA_VERSION",
    "default_registry_path",
    "file_to_dict",
    "load_registry",
    "record_to_dict",
    "registry_from_dict",
    "registry_to_dict",
    "write_registry",
]
