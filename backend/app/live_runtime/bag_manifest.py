"""Bag-backed evidence classification.

The single rule the rest of the live-runtime layer depends on:

    A run is ``bag_backed`` only when

    * ``bag_dir`` exists,
    * ``metadata.yaml`` exists inside it,
    * at least one ``.mcap`` or ``.db3`` chunk exists, and
    * the manifest's structural validation passes.

Any weaker shape produces ``partial``, ``invalid``, or
``missing_bag``. The classifier never reads bag contents — that is
left to ``ros2 bag info`` on the self-hosted runner — so it can run on
a GitHub-hosted CI runner without ROS installed and still hold the
honesty guardrails.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterable, Optional


_MCAP_EXT = ".mcap"
_DB3_EXT = ".db3"
_METADATA_NAME = "metadata.yaml"


class BagStatus(str, Enum):
    """Outcome of inspecting a candidate bag directory."""

    BAG_BACKED = "bag_backed"
    """Metadata + at least one chunk exist and validation passed."""

    PARTIAL = "partial"
    """Some required artefacts exist but the bag is incomplete."""

    INVALID = "invalid"
    """The directory exists but does not look like a bag at all."""

    MISSING_BAG = "missing_bag"
    """No bag directory was provided or it does not exist."""

    NOT_EXECUTED = "not_executed"
    """Bag inspection was deliberately skipped (e.g. dry run)."""


@dataclass(frozen=True)
class BagChunk:
    path: str
    format: str  # "mcap" or "db3"
    size_bytes: int

    def as_dict(self) -> dict:
        return {"path": self.path, "format": self.format, "size_bytes": self.size_bytes}


@dataclass(frozen=True)
class BagManifest:
    bag_dir: Optional[str]
    status: BagStatus
    reason: str
    metadata_present: bool
    chunks: tuple[BagChunk, ...]
    formats: tuple[str, ...]
    topic_inventory: tuple[str, ...] = ()
    scenario_id: Optional[str] = None
    run_id: Optional[str] = None
    notes: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "bag_dir": self.bag_dir,
            "status": self.status.value,
            "reason": self.reason,
            "metadata_present": self.metadata_present,
            "chunks": [c.as_dict() for c in self.chunks],
            "formats": list(self.formats),
            "topic_inventory": list(self.topic_inventory),
            "scenario_id": self.scenario_id,
            "run_id": self.run_id,
            "notes": list(self.notes),
        }

    @property
    def is_bag_backed(self) -> bool:
        return self.status is BagStatus.BAG_BACKED


def _scan_chunks(bag_dir: Path) -> list[BagChunk]:
    chunks: list[BagChunk] = []
    for entry in sorted(bag_dir.iterdir()):
        if not entry.is_file():
            continue
        suffix = entry.suffix.lower()
        if suffix == _MCAP_EXT:
            fmt = "mcap"
        elif suffix == _DB3_EXT:
            fmt = "db3"
        else:
            continue
        try:
            size = entry.stat().st_size
        except OSError:
            size = 0
        chunks.append(BagChunk(path=str(entry), format=fmt, size_bytes=size))
    return chunks


def _topic_inventory(metadata_path: Path) -> tuple[str, ...]:
    """Pull a best-effort topic list from rosbag2 metadata.yaml.

    Returns an empty tuple if PyYAML is unavailable or the metadata
    layout is not the standard rosbag2 shape. Bag classification does
    not depend on the inventory; it is informational only.
    """

    try:
        import yaml  # type: ignore[import-untyped]
    except Exception:  # pragma: no cover - PyYAML is a hard dep elsewhere
        return ()

    try:
        data = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))
    except Exception:
        return ()

    if not isinstance(data, dict):
        return ()
    info = data.get("rosbag2_bagfile_information")
    if not isinstance(info, dict):
        return ()
    topics_with_meta = info.get("topics_with_message_count")
    if not isinstance(topics_with_meta, list):
        return ()
    names: list[str] = []
    for entry in topics_with_meta:
        if not isinstance(entry, dict):
            continue
        topic_meta = entry.get("topic_metadata") or {}
        name = topic_meta.get("name") if isinstance(topic_meta, dict) else None
        if isinstance(name, str) and name:
            names.append(name)
    return tuple(names)


def inspect_bag_directory(
    bag_dir: Optional[Path],
    *,
    scenario_id: Optional[str] = None,
    run_id: Optional[str] = None,
) -> BagManifest:
    """Classify a candidate bag directory.

    The classifier never upgrades a weaker shape than ``bag_backed``.
    Callers that need to mark a bag as ``bag_backed`` after running
    ``ros2 bag info`` should construct a new manifest with the
    additional evidence; this function only sets ``BAG_BACKED`` when
    metadata + chunks are observed on disk.
    """

    if bag_dir is None:
        return BagManifest(
            bag_dir=None,
            status=BagStatus.MISSING_BAG,
            reason="no bag directory supplied",
            metadata_present=False,
            chunks=(),
            formats=(),
            scenario_id=scenario_id,
            run_id=run_id,
        )

    bag_dir = bag_dir.resolve() if bag_dir.exists() else bag_dir

    if not bag_dir.exists():
        return BagManifest(
            bag_dir=str(bag_dir),
            status=BagStatus.MISSING_BAG,
            reason=f"bag directory does not exist: {bag_dir}",
            metadata_present=False,
            chunks=(),
            formats=(),
            scenario_id=scenario_id,
            run_id=run_id,
        )

    if not bag_dir.is_dir():
        return BagManifest(
            bag_dir=str(bag_dir),
            status=BagStatus.INVALID,
            reason=f"bag path is not a directory: {bag_dir}",
            metadata_present=False,
            chunks=(),
            formats=(),
            scenario_id=scenario_id,
            run_id=run_id,
        )

    metadata_path = bag_dir / _METADATA_NAME
    metadata_present = metadata_path.is_file()
    chunks = _scan_chunks(bag_dir)
    formats = tuple(sorted({c.format for c in chunks}))

    if not metadata_present and not chunks:
        return BagManifest(
            bag_dir=str(bag_dir),
            status=BagStatus.MISSING_BAG,
            reason="no metadata.yaml and no .mcap/.db3 chunks found",
            metadata_present=False,
            chunks=(),
            formats=(),
            scenario_id=scenario_id,
            run_id=run_id,
        )

    if metadata_present and not chunks:
        return BagManifest(
            bag_dir=str(bag_dir),
            status=BagStatus.PARTIAL,
            reason="metadata.yaml present but no .mcap/.db3 chunks found",
            metadata_present=True,
            chunks=(),
            formats=(),
            topic_inventory=_topic_inventory(metadata_path),
            scenario_id=scenario_id,
            run_id=run_id,
        )

    if chunks and not metadata_present:
        return BagManifest(
            bag_dir=str(bag_dir),
            status=BagStatus.PARTIAL,
            reason=(
                "bag chunks present but metadata.yaml missing; "
                "rosbag2 cannot replay without metadata"
            ),
            metadata_present=False,
            chunks=tuple(chunks),
            formats=formats,
            scenario_id=scenario_id,
            run_id=run_id,
        )

    # Both present.
    notes: list[str] = []
    if all(chunk.size_bytes == 0 for chunk in chunks):
        notes.append("all bag chunks are zero bytes; runner did not write data")
        return BagManifest(
            bag_dir=str(bag_dir),
            status=BagStatus.PARTIAL,
            reason="bag chunks exist but contain no data",
            metadata_present=True,
            chunks=tuple(chunks),
            formats=formats,
            topic_inventory=_topic_inventory(metadata_path),
            scenario_id=scenario_id,
            run_id=run_id,
            notes=tuple(notes),
        )

    return BagManifest(
        bag_dir=str(bag_dir),
        status=BagStatus.BAG_BACKED,
        reason="metadata.yaml and at least one non-empty bag chunk present",
        metadata_present=True,
        chunks=tuple(chunks),
        formats=formats,
        topic_inventory=_topic_inventory(metadata_path),
        scenario_id=scenario_id,
        run_id=run_id,
    )


def summarise_topic_inventory(
    manifest: BagManifest, required_topics: Iterable[str]
) -> dict[str, list[str]]:
    """Return required vs missing topics for human-readable reports."""

    required = list(required_topics)
    inv = set(manifest.topic_inventory)
    missing = [t for t in required if t not in inv]
    return {
        "required": required,
        "observed": sorted(inv),
        "missing": missing,
    }
