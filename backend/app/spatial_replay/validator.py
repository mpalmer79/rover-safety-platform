"""Validation of an assembled spatial-replay artefact.

The validator's job is to *describe*, never to upgrade. It reads
the assembled :class:`SpatialReplay` and emits a
:class:`SpatialValidation` that an operator can read alongside the
artefact JSON.
"""

from __future__ import annotations

from typing import Iterable

from .models import (
    DERIVATION_BAG_BACKED,
    DERIVATION_FIXTURE,
    DERIVATION_BOUNDED_INPUTS,
    DERIVATION_TOPOLOGY_ONLY,
    DERIVATION_UNAVAILABLE,
    PREFERRED_POSE_TOPICS,
    TRAJECTORY_STATUS_COMPLETE,
    TRAJECTORY_STATUS_MISSING,
    TRAJECTORY_STATUS_PARTIAL,
    VALIDATION_STATUS_FAILED,
    VALIDATION_STATUS_NOT_EXECUTED,
    VALIDATION_STATUS_PARTIAL,
    VALIDATION_STATUS_PASSED,
    PoseSample,
    SpatialReplay,
    SpatialValidation,
)


def compute_missing_topics(
    samples: Iterable[PoseSample],
    expected_topics: tuple[str, ...] = (),
) -> tuple[str, ...]:
    have = {s.source_topic for s in samples if s.source_topic}
    return tuple(t for t in expected_topics if t not in have)


def validate_spatial_replay(
    replay: SpatialReplay,
    *,
    expected_topics: tuple[str, ...] = (),
    bag_validation_warnings: tuple[str, ...] = (),
) -> SpatialValidation:
    """Return a :class:`SpatialValidation` for an assembled replay."""

    warnings: list[str] = []

    # Honesty rule #1: bag_backed cannot be claimed without samples.
    if replay.derivation_source == DERIVATION_BAG_BACKED and not replay.samples:
        warnings.append(
            "derivation_source=bag_backed requires at least one pose sample"
        )

    # Honesty rule #2: fixture cannot be claimed without samples.
    if replay.derivation_source == DERIVATION_FIXTURE and not replay.samples:
        warnings.append(
            "derivation_source=fixture requires at least one pose sample"
        )

    # Honesty rule #3: unavailable must have zero samples + zero segments.
    if replay.derivation_source == DERIVATION_UNAVAILABLE and (
        replay.samples or replay.segments
    ):
        warnings.append(
            "derivation_source=unavailable contradicts non-empty samples/segments"
        )

    # Honesty rule #4: bounded_inputs / topology_only never has samples.
    if (
        replay.derivation_source in (DERIVATION_BOUNDED_INPUTS, DERIVATION_TOPOLOGY_ONLY)
        and replay.samples
    ):
        warnings.append(
            f"derivation_source={replay.derivation_source!r} contradicts pose samples"
        )

    missing = compute_missing_topics(replay.samples, expected_topics)
    if missing:
        warnings.append(
            f"missing expected pose topics: {', '.join(sorted(missing))}"
        )

    # Determine status.
    if replay.derivation_source == DERIVATION_UNAVAILABLE:
        status = VALIDATION_STATUS_NOT_EXECUTED
    elif warnings:
        # Bag-validation failures are FAILED; alignment/topic gaps are PARTIAL.
        critical = any("requires at least one pose sample" in w for w in warnings)
        critical = critical or any(
            "contradicts" in w for w in warnings
        )
        if critical:
            status = VALIDATION_STATUS_FAILED
        else:
            status = VALIDATION_STATUS_PARTIAL
    else:
        status = VALIDATION_STATUS_PASSED

    return SpatialValidation(
        status=status,
        warnings=tuple(warnings),
        missing_topics=tuple(sorted(missing)),
        topic_sources=replay.topic_sources,
        sample_count=len(replay.samples),
        bag_validation_warnings=bag_validation_warnings,
    )


def is_honestly_bag_backed(replay: SpatialReplay) -> bool:
    """Return True iff the replay's bag-backed claim is honest.

    This is the single function the frontend can call to recheck a
    bag-backed badge before rendering. Any drift here causes the UI
    to fall back to ``bounded_inputs``.
    """

    if replay.derivation_source != DERIVATION_BAG_BACKED:
        return False
    if not replay.samples:
        return False
    if replay.bag_status != "bag_backed":
        return False
    return True


__all__ = [
    "compute_missing_topics",
    "is_honestly_bag_backed",
    "validate_spatial_replay",
]
