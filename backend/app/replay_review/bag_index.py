"""Bag artefact indexer.

Inspects candidate bag directories for rosbag2 / MCAP files and the
accompanying ``metadata.yaml``. The indexer never opens a bag file
itself — it only reads filesystem metadata and (optionally) the YAML
manifest. Reading the YAML happens via :mod:`yaml` so it requires no
ROS dependency.

When a bag directory is missing or empty the indexer returns a
:class:`BagIndex` with status ``missing_bag`` plus a structured note.
It never invents topic inventory; if topics cannot be read from the
metadata, the inventory is empty and the report flags the gap.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

from app.replay_review.models import (
    BagArtifact,
    BagIndex,
    is_bag_file,
)


_DEFAULT_BAG_DIR_NAMES: tuple[str, ...] = ("bags", "bag", "rosbag")


def candidate_bag_roots(
    *,
    incident_dir: Optional[Path] = None,
    runtime_run_dir: Optional[Path] = None,
    runs_root: Optional[Path] = None,
    run_id: Optional[str] = None,
) -> list[Path]:
    """Return the documented locations to look for bag artefacts.

    The order mirrors the runbook: incident bundle first, then
    runtime evidence, then the gitignored ``runs/<run_id>/bags/``.
    Caller decides what to do if multiple candidates exist (the
    indexer returns one :class:`BagIndex` per candidate that exists).
    """

    candidates: list[Path] = []
    if incident_dir is not None:
        for name in _DEFAULT_BAG_DIR_NAMES:
            candidates.append(incident_dir / name)
    if runtime_run_dir is not None:
        for name in _DEFAULT_BAG_DIR_NAMES:
            candidates.append(runtime_run_dir / name)
    if runs_root is not None and run_id:
        for name in _DEFAULT_BAG_DIR_NAMES:
            candidates.append(runs_root / run_id / name)
    return candidates


def index_bag_directory(bag_root: Path) -> BagIndex:
    """Inspect ``bag_root`` and return a :class:`BagIndex`.

    The directory is treated as missing if it does not exist or is
    not a directory. Missing-bag is *not* a failure — the caller
    decides whether the absence is acceptable for the review (e.g.
    static-only incidents do not need a bag).
    """

    bag_root = Path(bag_root)
    index = BagIndex(bag_root=bag_root)
    if not bag_root.exists():
        index.notes.append(f"bag directory does not exist: {bag_root}")
        return index
    if not bag_root.is_dir():
        index.notes.append(f"expected a directory: {bag_root}")
        return index

    # Walk the directory and classify each file.
    for path in sorted(bag_root.rglob("*")):
        if not path.is_file():
            continue
        if path.name == "metadata.yaml":
            index.metadata_path = path
            try:
                size = path.stat().st_size
            except OSError:
                size = -1
            index.artifacts.append(
                BagArtifact(
                    path=path,
                    kind="metadata",
                    size_bytes=size,
                )
            )
            continue
        if is_bag_file(path):
            kind = path.suffix.lower().lstrip(".")
            try:
                size = path.stat().st_size
            except OSError:
                size = -1
            index.artifacts.append(
                BagArtifact(
                    path=path,
                    kind=kind,
                    size_bytes=size,
                )
            )

    if not index.artifacts:
        index.notes.append(
            f"no bag chunks or metadata.yaml found under {bag_root}"
        )

    if index.metadata_path is not None:
        _read_metadata(index)

    return index


def _read_metadata(index: BagIndex) -> None:
    """Best-effort read of the rosbag2 ``metadata.yaml``.

    The standard rosbag2 layout is:

        rosbag2_bagfile_information:
          starting_time:
            nanoseconds_since_epoch: <int>
          duration:
            nanoseconds: <int>
          topics_with_message_count:
            - topic_metadata:
                name: <topic>
              message_count: <int>

    We extract the topic inventory + per-topic counts when available;
    missing fields become indexer notes, not exceptions.
    """

    try:
        import yaml  # noqa: F401  (intentional)
    except ImportError:  # pragma: no cover - PyYAML is a hard dep
        index.notes.append("PyYAML not importable; metadata not parsed")
        return
    try:
        text = index.metadata_path.read_text(encoding="utf-8")
        import yaml

        data = yaml.safe_load(text)
    except (OSError, yaml.YAMLError) as exc:  # pragma: no cover
        index.notes.append(f"metadata.yaml did not parse: {exc}")
        return

    if not isinstance(data, dict):
        index.notes.append("metadata.yaml has unexpected shape")
        return
    info = data.get("rosbag2_bagfile_information") or data
    if not isinstance(info, dict):
        index.notes.append("metadata.yaml lacks rosbag2_bagfile_information")
        return

    starting = info.get("starting_time") or {}
    if isinstance(starting, dict):
        ns = starting.get("nanoseconds_since_epoch")
        if isinstance(ns, (int, float)):
            index.start_time_ns = int(ns)

    duration = info.get("duration") or {}
    if isinstance(duration, dict) and index.start_time_ns is not None:
        ns = duration.get("nanoseconds")
        if isinstance(ns, (int, float)):
            index.end_time_ns = int(index.start_time_ns + ns)

    topics: list[str] = []
    counts: dict[str, int] = {}
    for entry in info.get("topics_with_message_count", []) or []:
        if not isinstance(entry, dict):
            continue
        meta = entry.get("topic_metadata") or {}
        if not isinstance(meta, dict):
            continue
        name = meta.get("name")
        if not isinstance(name, str):
            continue
        topics.append(name)
        count = entry.get("message_count")
        if isinstance(count, (int, float)):
            counts[name] = int(count)
    index.inventory_topics = tuple(topics)
    index.message_counts = counts


def index_bag_candidates(candidates: Iterable[Path]) -> list[BagIndex]:
    """Convenience: index each candidate path and return the list.

    Empty / nonexistent paths still produce a :class:`BagIndex` with
    a structured note so the manifest can show which locations were
    inspected.
    """

    out: list[BagIndex] = []
    seen: set[Path] = set()
    for path in candidates:
        path = Path(path).resolve()
        if path in seen:
            continue
        seen.add(path)
        out.append(index_bag_directory(path))
    return out


def merge_inventory(indices: Iterable[BagIndex]) -> tuple[str, ...]:
    """Combine the topic inventory from every populated bag index."""

    out: list[str] = []
    seen: set[str] = set()
    for index in indices:
        for topic in index.inventory_topics:
            if topic in seen:
                continue
            seen.add(topic)
            out.append(topic)
    return tuple(out)
