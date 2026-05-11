"""Assemble a :class:`SpatialReplay` artefact from on-disk inputs.

The builder chooses the highest-honesty derivation source the
inputs support:

#. ``bag_backed`` — bag manifest validates + runtime pose samples
   exist on disk and pass eligibility checks.
#. ``fixture`` — committed pose-samples fixture exists, but no
   bag-backed manifest is in effect.
#. ``bounded_inputs`` — no samples, but the mission plan has
   non-zero bounded distance/angle (handled by the frontend
   adapter).
#. ``topology_only`` — plan has waypoints but no bounded motion.
#. ``unavailable`` — no plan, no samples.

The frontend adapter handles the ``bounded_inputs`` and
``topology_only`` paths; the backend builder writes a frontend
artefact ONLY when samples exist (i.e. ``bag_backed`` or
``fixture``). Otherwise it returns ``None`` and the frontend falls
back to its in-process derivation.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Iterable, Mapping

from .event_aligner import align_events
from .manifest_loader import (
    evaluate_bag_eligibility,
    load_run_manifest,
    manifest_bag_status,
    runtime_run_dir,
)
from .models import (
    DERIVATION_BAG_BACKED,
    DERIVATION_FIXTURE,
    DERIVATION_UNAVAILABLE,
    SpatialReplay,
)
from .pose_extractor import extract_pose_samples
from .trajectory_builder import (
    build_segments,
    classify_trajectory,
    topic_sources,
)
from .validator import validate_spatial_replay


def build_spatial_replay(
    *,
    run_id: str,
    scenario_id: str,
    mission_id: str,
    evidence_root: Path | None,
    fixtures_root: Path | None,
    events: Iterable[Mapping[str, object]] = (),
    expected_topics: tuple[str, ...] = (),
    generated_at_utc: str = "",
) -> SpatialReplay:
    """Assemble the spatial-replay artefact for one run.

    The function never raises. If no samples are available the
    return value is a ``unavailable``-derived replay; the frontend
    adapter then handles the bounded-inputs / topology-only fallback.
    """

    samples, source_kind = extract_pose_samples(
        evidence_root=evidence_root,
        fixtures_root=fixtures_root,
        run_id=run_id,
    )

    manifest = (
        load_run_manifest(evidence_root, run_id) if evidence_root is not None else None
    )
    bag_status = manifest_bag_status(manifest)

    # The manifest path is only valid when evidence_root is supplied.
    bundle_root = (
        runtime_run_dir(evidence_root, run_id) if evidence_root is not None else None
    )

    eligibility = evaluate_bag_eligibility(
        manifest,
        bundle_root=bundle_root,
        has_pose_samples=bool(samples) and source_kind == "runtime",
    )

    # Choose derivation source.
    if eligibility.is_bag_backed:
        derivation_source = DERIVATION_BAG_BACKED
        note = (
            "Spatial route derived from bag-backed runtime pose samples. "
            f"manifest at {bundle_root}; samples loaded from "
            f"{bundle_root}/pose-samples.jsonl."
        )
        known_limitations: tuple[str, ...] = ()
    elif samples:
        derivation_source = DERIVATION_FIXTURE
        note = (
            "Spatial route derived from committed fixture pose samples. "
            "Not bag-backed evidence."
        )
        known_limitations = tuple(
            ("fixture-derived spatial samples; not bag-backed evidence",)
            + tuple(eligibility.reasons)
        )
    else:
        derivation_source = DERIVATION_UNAVAILABLE
        note = "No spatial samples available; frontend will fall back to bounded inputs."
        known_limitations = eligibility.reasons

    segments = build_segments(samples)
    trajectory_status = classify_trajectory(
        samples, expected_topics=expected_topics
    )
    topics = topic_sources(samples)
    missing_topics = tuple(t for t in expected_topics if t not in set(topics))

    alignments = align_events(events, samples)

    replay = SpatialReplay(
        run_id=run_id,
        scenario_id=scenario_id,
        mission_id=mission_id,
        evidence_origin=source_kind,
        bag_status=bag_status,
        derivation_source=derivation_source,
        trajectory_status=trajectory_status,
        validation_status="not_executed",  # filled in below
        samples=samples,
        segments=segments,
        event_alignments=alignments,
        topic_sources=topics,
        missing_topics=missing_topics,
        known_limitations=known_limitations,
        generated_at_utc=generated_at_utc,
        note=note,
    )

    validation = validate_spatial_replay(
        replay,
        expected_topics=expected_topics,
        bag_validation_warnings=eligibility.reasons,
    )
    return replace(replay, validation_status=validation.status)


__all__ = [
    "build_spatial_replay",
]
