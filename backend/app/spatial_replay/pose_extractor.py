"""Pose-sample extraction.

Phase 17C does NOT bundle a rosbag2 parser. Two ingestion paths are
supported:

1. **Bag-backed** — when the bag manifest's ``topic_inventory``
   includes a preferred pose topic AND the run directory contains a
   committed ``pose-samples.jsonl`` file derived from the real bag.
   The committed file is the operator's responsibility to produce
   from the real run; this module never invents pose samples on the
   operator's behalf.

2. **Fixture** — when ``spatial-replay/fixtures/<run_id>/
   pose-samples.jsonl`` exists. Fixture samples are useful for
   regression testing the trajectory + alignment code, but they are
   never re-labelled bag-backed by this module.

Both paths emit identical :class:`PoseSample` tuples; the
:func:`extract_pose_samples` function reports which path it took.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Mapping

from .models import PREFERRED_POSE_TOPICS, PoseSample


POSE_SAMPLES_FILENAME: str = "pose-samples.jsonl"


def fixtures_run_dir(fixtures_root: Path, run_id: str) -> Path:
    """Resolve the fixture directory for a given run id."""

    return Path(fixtures_root) / run_id


def runtime_pose_samples_path(evidence_root: Path, run_id: str) -> Path:
    """Path to a runtime-derived pose-samples file (if any).

    Operators produce this file by post-processing a real bag with
    their own tooling. The platform never produces it on their
    behalf.
    """

    return Path(evidence_root) / "runtime" / run_id / POSE_SAMPLES_FILENAME


def fixture_pose_samples_path(fixtures_root: Path, run_id: str) -> Path:
    return fixtures_run_dir(fixtures_root, run_id) / POSE_SAMPLES_FILENAME


def _coerce_sample(raw: Mapping[str, object], idx: int) -> PoseSample | None:
    """Return a sample or ``None`` if the row is malformed."""

    try:
        sid = str(raw.get("sample_id") or f"s{idx:05d}")
        time_ns = int(raw.get("time_ns", 0) or 0)
        x = float(raw.get("x_m", 0.0) or 0.0)
        y = float(raw.get("y_m", 0.0) or 0.0)
        theta = float(raw.get("theta_rad", 0.0) or 0.0)
    except (TypeError, ValueError):
        return None
    source_topic = str(raw.get("source_topic") or "")
    if source_topic and source_topic not in PREFERRED_POSE_TOPICS:
        # Allow unknown topics through; the validator will warn.
        pass
    confidence = str(raw.get("confidence") or "unknown")
    refs_raw = raw.get("event_refs") or ()
    if isinstance(refs_raw, str):
        refs = (refs_raw,)
    else:
        refs = tuple(str(x) for x in refs_raw)  # type: ignore[arg-type]
    return PoseSample(
        sample_id=sid,
        time_ns=time_ns,
        x_m=x,
        y_m=y,
        theta_rad=theta,
        source_topic=source_topic,
        confidence=confidence,
        event_refs=refs,
    )


def read_pose_samples(path: Path) -> tuple[PoseSample, ...]:
    """Read a JSONL pose-samples file. Missing files yield ``()``."""

    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError:
        return ()
    out: list[PoseSample] = []
    for idx, line in enumerate(text.splitlines()):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            raw = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if not isinstance(raw, dict):
            continue
        sample = _coerce_sample(raw, idx)
        if sample is not None:
            out.append(sample)
    # Deterministic order: sort by (time_ns, sample_id).
    out.sort(key=lambda s: (s.time_ns, s.sample_id))
    return tuple(out)


def write_pose_samples(samples: Iterable[PoseSample], path: Path) -> None:
    """Write pose samples as JSONL (one object per line)."""

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", encoding="utf-8") as fh:
        for sample in samples:
            fh.write(
                json.dumps(
                    {
                        "sample_id": sample.sample_id,
                        "time_ns": sample.time_ns,
                        "x_m": sample.x_m,
                        "y_m": sample.y_m,
                        "theta_rad": sample.theta_rad,
                        "source_topic": sample.source_topic,
                        "confidence": sample.confidence,
                        "event_refs": list(sample.event_refs),
                    },
                    sort_keys=True,
                )
                + "\n"
            )


def extract_pose_samples(
    *,
    evidence_root: Path | None,
    fixtures_root: Path | None,
    run_id: str,
) -> tuple[tuple[PoseSample, ...], str]:
    """Return ``(samples, source_kind)``.

    ``source_kind`` is one of:

    * ``"runtime"`` — samples came from the live evidence directory.
    * ``"fixture"`` — samples came from a committed fixture.
    * ``"missing"`` — no samples were found.

    The function never reaches across the boundary: it does not
    invent samples or pull from a network resource.
    """

    if evidence_root is not None:
        runtime_path = runtime_pose_samples_path(evidence_root, run_id)
        runtime_samples = read_pose_samples(runtime_path)
        if runtime_samples:
            return runtime_samples, "runtime"
    if fixtures_root is not None:
        fixture_path = fixture_pose_samples_path(fixtures_root, run_id)
        fixture_samples = read_pose_samples(fixture_path)
        if fixture_samples:
            return fixture_samples, "fixture"
    return (), "missing"


__all__ = [
    "POSE_SAMPLES_FILENAME",
    "extract_pose_samples",
    "fixture_pose_samples_path",
    "fixtures_run_dir",
    "read_pose_samples",
    "runtime_pose_samples_path",
    "write_pose_samples",
]
