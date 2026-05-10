"""Bag-manifest construction + validation.

The platform is **not safety-certified**. A bag manifest records
what was (or was not) recorded during a live qualification run.
The honesty rules: ``bag_backed`` requires real artefacts on disk;
``not_executed`` requires an explicit reason.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping

from .models import (
    BAG_STATUS_BAG_BACKED,
    BAG_STATUS_INVALID,
    BAG_STATUS_MISSING_BAG,
    BAG_STATUS_NOT_EXECUTED,
    BAG_STATUS_PARTIAL,
    BAG_STATUSES,
    BagManifest,
)


REQUIRED_FIELDS: tuple[str, ...] = (
    "run_id",
    "scenario_id",
    "bag_status",
    "bag_format",
    "bag_paths",
    "metadata_yaml_path",
    "topic_inventory",
    "message_counts",
    "start_time",
    "end_time",
    "duration_seconds",
    "missing_required_topics",
    "validation_status",
)


def bag_manifest_from_dict(payload: Mapping[str, Any]) -> BagManifest:
    return BagManifest(
        run_id=str(payload.get("run_id", "")),
        scenario_id=str(payload.get("scenario_id", "")),
        bag_status=str(payload.get("bag_status", "")),
        bag_format=str(payload.get("bag_format", "")),
        bag_paths=tuple(str(x) for x in payload.get("bag_paths", ())),
        metadata_yaml_path=str(payload.get("metadata_yaml_path", "")),
        topic_inventory=tuple(str(x) for x in payload.get("topic_inventory", ())),
        message_counts={
            str(k): int(v) for k, v in dict(payload.get("message_counts", {})).items()
        },
        start_time=str(payload.get("start_time", "")),
        end_time=str(payload.get("end_time", "")),
        duration_seconds=float(payload.get("duration_seconds", 0.0) or 0.0),
        missing_required_topics=tuple(
            str(x) for x in payload.get("missing_required_topics", ())
        ),
        validation_status=str(payload.get("validation_status", "")),
        known_limitations=tuple(
            str(x) for x in payload.get("known_limitations", ())
        ),
        not_executed_reason=str(payload.get("not_executed_reason", "")),
    )


def bag_manifest_to_dict(manifest: BagManifest) -> dict[str, Any]:
    out = asdict(manifest)
    out["bag_paths"] = list(manifest.bag_paths)
    out["topic_inventory"] = list(manifest.topic_inventory)
    out["missing_required_topics"] = list(manifest.missing_required_topics)
    out["known_limitations"] = list(manifest.known_limitations)
    out["message_counts"] = dict(manifest.message_counts)
    return out


def write_bag_manifest(manifest: BagManifest, path: Path) -> None:
    Path(path).write_text(
        json.dumps(bag_manifest_to_dict(manifest), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_bag_manifest(path: Path) -> BagManifest | None:
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError:
        return None
    if not text.strip():
        return None
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return bag_manifest_from_dict(payload)


def build_not_executed_manifest(
    *, run_id: str, scenario_id: str, reason: str
) -> BagManifest:
    """Return a manifest representing an honest 'live execution did not occur' result."""

    return BagManifest(
        run_id=run_id,
        scenario_id=scenario_id,
        bag_status=BAG_STATUS_NOT_EXECUTED,
        bag_format="",
        bag_paths=(),
        metadata_yaml_path="",
        topic_inventory=(),
        message_counts={},
        start_time="",
        end_time="",
        duration_seconds=0.0,
        missing_required_topics=(),
        validation_status="not_executed",
        known_limitations=(),
        not_executed_reason=reason or "live execution did not occur",
    )


def validate_bag_manifest(
    manifest: BagManifest | None,
    *,
    bundle_root: Path | None = None,
    required_topics: tuple[str, ...] = (),
) -> tuple[str, ...]:
    """Return a tuple of human-readable validation warnings.

    The validator is *honest*: it never silently upgrades a status,
    and it never accepts ``bag_backed`` without artefact evidence.
    """

    if manifest is None:
        return ("bag manifest missing or unparseable",)
    warnings: list[str] = []
    if manifest.bag_status not in BAG_STATUSES:
        warnings.append(
            f"bag_status {manifest.bag_status!r} not in {sorted(BAG_STATUSES)!r}"
        )
        return tuple(warnings)
    if not manifest.run_id:
        warnings.append("missing run_id")
    if not manifest.scenario_id:
        warnings.append("missing scenario_id")

    if manifest.bag_status == BAG_STATUS_NOT_EXECUTED:
        if not manifest.not_executed_reason.strip():
            warnings.append("bag_status=not_executed requires not_executed_reason")
        # No artefact checks expected.
        return tuple(warnings)

    if manifest.bag_status == BAG_STATUS_INVALID:
        # invalid is allowed; nothing else to check.
        return tuple(warnings)

    # For bag_backed / partial / missing_bag we expect topic info.
    if manifest.bag_status == BAG_STATUS_BAG_BACKED:
        if not manifest.bag_paths:
            warnings.append("bag_status=bag_backed requires at least one bag path")
        if not manifest.metadata_yaml_path:
            warnings.append("bag_status=bag_backed requires metadata_yaml_path")
        if bundle_root is not None:
            for raw in manifest.bag_paths:
                p = (bundle_root / raw).resolve() if not Path(raw).is_absolute() else Path(raw)
                if not p.exists():
                    warnings.append(f"bag_status=bag_backed but bag path missing: {raw}")
            if manifest.metadata_yaml_path:
                m = (
                    (bundle_root / manifest.metadata_yaml_path).resolve()
                    if not Path(manifest.metadata_yaml_path).is_absolute()
                    else Path(manifest.metadata_yaml_path)
                )
                if not m.exists():
                    warnings.append(
                        f"bag_status=bag_backed but metadata yaml missing: "
                        f"{manifest.metadata_yaml_path}"
                    )

    if manifest.bag_status == BAG_STATUS_MISSING_BAG and manifest.bag_paths:
        warnings.append(
            "bag_status=missing_bag is inconsistent with non-empty bag_paths"
        )

    # Required-topic check.
    if required_topics:
        have = set(manifest.topic_inventory)
        missing = tuple(t for t in required_topics if t not in have)
        for t in missing:
            warnings.append(f"required topic missing from inventory: {t}")
        if (
            manifest.bag_status == BAG_STATUS_BAG_BACKED
            and missing
            and missing != tuple(manifest.missing_required_topics)
        ):
            warnings.append(
                "bag_status=bag_backed but missing_required_topics does not "
                "match required_topics minus inventory"
            )

    return tuple(warnings)


def bag_manifest_is_bag_backed(manifest: BagManifest | None) -> bool:
    """True iff the manifest *honestly* claims bag_backed status."""

    if manifest is None:
        return False
    return manifest.bag_status == BAG_STATUS_BAG_BACKED and bool(manifest.bag_paths)


def degrade_to_partial_if_missing(
    manifest: BagManifest, required_topics: tuple[str, ...]
) -> BagManifest:
    """If a bag_backed manifest is missing required topics, downgrade to partial."""

    if manifest.bag_status != BAG_STATUS_BAG_BACKED:
        return manifest
    have = set(manifest.topic_inventory)
    missing = tuple(t for t in required_topics if t not in have)
    if not missing:
        return manifest
    from dataclasses import replace as _replace

    return _replace(
        manifest,
        bag_status=BAG_STATUS_PARTIAL,
        missing_required_topics=missing,
        validation_status="partial",
    )


__all__ = [
    "REQUIRED_FIELDS",
    "bag_manifest_from_dict",
    "bag_manifest_to_dict",
    "write_bag_manifest",
    "load_bag_manifest",
    "build_not_executed_manifest",
    "validate_bag_manifest",
    "bag_manifest_is_bag_backed",
    "degrade_to_partial_if_missing",
]
