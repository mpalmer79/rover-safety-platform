"""Trajectory construction from ordered pose samples.

The builder is deterministic and idempotent: the same input samples
produce a byte-identical output. It never resamples, never smooths,
and never interpolates between distinct ``source_topic`` values.
"""

from __future__ import annotations

import math
from typing import Iterable

from .models import (
    TRAJECTORY_STATUS_COMPLETE,
    TRAJECTORY_STATUS_MISSING,
    TRAJECTORY_STATUS_PARTIAL,
    PoseSample,
    TrajectorySegment,
)


# Minimum samples to form at least one segment.
_MIN_SAMPLES_FOR_TRAJECTORY: int = 2


def build_segments(
    samples: Iterable[PoseSample],
) -> tuple[TrajectorySegment, ...]:
    """Connect consecutive samples into trajectory segments.

    The segment list mirrors the sample order. Distance is the
    Euclidean distance between samples in metres; duration is the
    time delta in nanoseconds. The function does not deduplicate
    samples with identical positions — these still produce a
    zero-distance segment, which the UI can choose to skip.
    """

    sorted_samples = sorted(samples, key=lambda s: (s.time_ns, s.sample_id))
    segments: list[TrajectorySegment] = []
    for prev, curr in zip(sorted_samples, sorted_samples[1:]):
        dx = curr.x_m - prev.x_m
        dy = curr.y_m - prev.y_m
        distance = math.hypot(dx, dy)
        duration = max(0, curr.time_ns - prev.time_ns)
        segments.append(
            TrajectorySegment(
                from_sample_id=prev.sample_id,
                to_sample_id=curr.sample_id,
                distance_m=distance,
                duration_ns=duration,
            )
        )
    return tuple(segments)


def classify_trajectory(
    samples: tuple[PoseSample, ...],
    *,
    expected_topics: tuple[str, ...] = (),
) -> str:
    """Return one of :data:`TRAJECTORY_STATUS_*` for the given samples.

    A trajectory is ``complete`` when it has at least two samples and
    samples cover every expected topic. ``partial`` when at least one
    sample exists but coverage is incomplete. ``missing`` otherwise.
    """

    if len(samples) < _MIN_SAMPLES_FOR_TRAJECTORY:
        if not samples:
            return TRAJECTORY_STATUS_MISSING
        return TRAJECTORY_STATUS_PARTIAL
    if not expected_topics:
        return TRAJECTORY_STATUS_COMPLETE
    have = {s.source_topic for s in samples if s.source_topic}
    missing = [t for t in expected_topics if t not in have]
    if missing:
        return TRAJECTORY_STATUS_PARTIAL
    return TRAJECTORY_STATUS_COMPLETE


def topic_sources(samples: tuple[PoseSample, ...]) -> tuple[str, ...]:
    """Return the sorted unique source topics used in the trajectory."""

    seen = {s.source_topic for s in samples if s.source_topic}
    return tuple(sorted(seen))


def bounding_box(
    samples: tuple[PoseSample, ...],
) -> tuple[tuple[float, float], tuple[float, float]] | None:
    """Return ``((min_x, min_y), (max_x, max_y))`` or ``None`` if empty."""

    if not samples:
        return None
    xs = [s.x_m for s in samples]
    ys = [s.y_m for s in samples]
    return ((min(xs), min(ys)), (max(xs), max(ys)))


__all__ = [
    "TRAJECTORY_STATUS_COMPLETE",
    "TRAJECTORY_STATUS_PARTIAL",
    "TRAJECTORY_STATUS_MISSING",
    "build_segments",
    "bounding_box",
    "classify_trajectory",
    "topic_sources",
]
