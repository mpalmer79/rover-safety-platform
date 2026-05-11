"""Serialise and render spatial-replay artefacts.

The reporter writes three files per run:

* ``spatial-replay.json`` — frontend-consumable artefact.
* ``trajectory.jsonl`` — one pose sample per line, sorted by time.
* ``event-alignment.json`` — event → sample alignments.
* ``spatial-validation.json`` — validation summary.
* ``spatial-replay-report.md`` — human-readable report.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .models import (
    DERIVATION_BAG_BACKED,
    DERIVATION_FIXTURE,
    DERIVATION_UNAVAILABLE,
    EventAlignment,
    PoseSample,
    SpatialReplay,
    SpatialValidation,
    TrajectorySegment,
)


def pose_sample_to_dict(sample: PoseSample) -> dict[str, object]:
    return {
        "sample_id": sample.sample_id,
        "time_ns": sample.time_ns,
        "x_m": sample.x_m,
        "y_m": sample.y_m,
        "theta_rad": sample.theta_rad,
        "source_topic": sample.source_topic,
        "confidence": sample.confidence,
        "event_refs": list(sample.event_refs),
    }


def trajectory_segment_to_dict(segment: TrajectorySegment) -> dict[str, object]:
    return {
        "from_sample_id": segment.from_sample_id,
        "to_sample_id": segment.to_sample_id,
        "distance_m": segment.distance_m,
        "duration_ns": segment.duration_ns,
    }


def event_alignment_to_dict(alignment: EventAlignment) -> dict[str, object]:
    return {
        "event_id": alignment.event_id,
        "deterministic_hash": alignment.deterministic_hash,
        "matched_sample_id": alignment.matched_sample_id,
        "spatial_position": (
            list(alignment.spatial_position)
            if alignment.spatial_position is not None
            else None
        ),
        "delta_time_ns": alignment.delta_time_ns,
        "confidence": alignment.confidence,
    }


def spatial_replay_to_dict(replay: SpatialReplay) -> dict[str, object]:
    return {
        "run_id": replay.run_id,
        "scenario_id": replay.scenario_id,
        "mission_id": replay.mission_id,
        "evidence_origin": replay.evidence_origin,
        "bag_status": replay.bag_status,
        "derivation_source": replay.derivation_source,
        "trajectory_status": replay.trajectory_status,
        "validation_status": replay.validation_status,
        "sample_count": len(replay.samples),
        "segment_count": len(replay.segments),
        "topic_sources": list(replay.topic_sources),
        "missing_topics": list(replay.missing_topics),
        "known_limitations": list(replay.known_limitations),
        "generated_at_utc": replay.generated_at_utc,
        "note": replay.note,
        "samples": [pose_sample_to_dict(s) for s in replay.samples],
        "segments": [trajectory_segment_to_dict(s) for s in replay.segments],
        "event_alignments": [
            event_alignment_to_dict(a) for a in replay.event_alignments
        ],
    }


def spatial_validation_to_dict(validation: SpatialValidation) -> dict[str, object]:
    return {
        "status": validation.status,
        "warnings": list(validation.warnings),
        "missing_topics": list(validation.missing_topics),
        "topic_sources": list(validation.topic_sources),
        "sample_count": validation.sample_count,
        "bag_validation_warnings": list(validation.bag_validation_warnings),
    }


def write_spatial_replay_artefacts(
    replay: SpatialReplay,
    validation: SpatialValidation,
    out_dir: Path,
) -> dict[str, Path]:
    """Write the four JSON/JSONL files. Returns the resolved paths."""

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    paths = {
        "spatial_replay_json": out_dir / "spatial-replay.json",
        "trajectory_jsonl": out_dir / "trajectory.jsonl",
        "event_alignment_json": out_dir / "event-alignment.json",
        "spatial_validation_json": out_dir / "spatial-validation.json",
        "report_md": out_dir / "spatial-replay-report.md",
    }

    paths["spatial_replay_json"].write_text(
        json.dumps(spatial_replay_to_dict(replay), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with paths["trajectory_jsonl"].open("w", encoding="utf-8") as fh:
        for sample in replay.samples:
            fh.write(json.dumps(pose_sample_to_dict(sample), sort_keys=True) + "\n")

    paths["event_alignment_json"].write_text(
        json.dumps(
            {
                "run_id": replay.run_id,
                "alignments": [
                    event_alignment_to_dict(a) for a in replay.event_alignments
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    paths["spatial_validation_json"].write_text(
        json.dumps(spatial_validation_to_dict(validation), indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )

    paths["report_md"].write_text(render_report_markdown(replay, validation), encoding="utf-8")

    return paths


def render_report_markdown(
    replay: SpatialReplay, validation: SpatialValidation
) -> str:
    """Human-readable report. Honesty rules baked into the prose."""

    lines: list[str] = []
    lines.append(f"# Spatial replay report — {replay.run_id}")
    lines.append("")
    lines.append(
        "The platform is **not safety-certified.** This report describes "
        "the spatial-replay artefact for one run; it never asserts that "
        "real telemetry was captured unless the derivation source is "
        "`bag_backed`."
    )
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Run:** `{replay.run_id}`")
    lines.append(f"- **Scenario:** `{replay.scenario_id}`")
    lines.append(f"- **Mission:** `{replay.mission_id}`")
    lines.append(f"- **Derivation source:** `{replay.derivation_source}`")
    lines.append(f"- **Bag status:** `{replay.bag_status}`")
    lines.append(f"- **Trajectory status:** `{replay.trajectory_status}`")
    lines.append(f"- **Validation status:** `{replay.validation_status}`")
    lines.append(f"- **Sample count:** {len(replay.samples)}")
    lines.append(f"- **Segment count:** {len(replay.segments)}")
    lines.append("")

    if replay.derivation_source == DERIVATION_BAG_BACKED:
        lines.append(
            "Spatial samples were extracted from real bag-backed evidence. "
            "Operators may overlay these on the mission map and use the "
            "playback scrubber to step through the run."
        )
    elif replay.derivation_source == DERIVATION_FIXTURE:
        lines.append(
            "Spatial samples are derived from a committed fixture. "
            "**These are not bag-backed evidence.** They exist to "
            "regression-test the trajectory + alignment code paths."
        )
    elif replay.derivation_source == DERIVATION_UNAVAILABLE:
        lines.append(
            "No spatial samples were available. The frontend will "
            "fall back to bounded-inputs derivation or the topology-only "
            "view."
        )
    lines.append("")

    if replay.missing_topics:
        lines.append("## Missing topics")
        lines.append("")
        for t in replay.missing_topics:
            lines.append(f"- `{t}`")
        lines.append("")

    if validation.warnings:
        lines.append("## Validation warnings")
        lines.append("")
        for w in validation.warnings:
            lines.append(f"- {w}")
        lines.append("")

    if replay.known_limitations:
        lines.append("## Known limitations")
        lines.append("")
        for limitation in replay.known_limitations:
            lines.append(f"- {limitation}")
        lines.append("")

    lines.append("## Next step")
    lines.append("")
    if replay.derivation_source == DERIVATION_BAG_BACKED:
        lines.append(
            "Replay the run from the mission detail page; confirm the "
            "event timeline aligns with the spatial trajectory."
        )
    elif replay.derivation_source == DERIVATION_FIXTURE:
        lines.append(
            "Produce a real bag-backed run on a qualified self-hosted "
            "runner. Once the bag manifest validates, this run will be "
            "labelled `bag_backed` automatically."
        )
    else:
        lines.append(
            "Produce a pose-samples fixture or a real bag-backed run "
            "before the mission map will show a trajectory."
        )
    lines.append("")
    return "\n".join(lines)


def runs_dir(spatial_root: Path) -> Path:
    return Path(spatial_root) / "runs"


def run_output_dir(spatial_root: Path, run_id: str) -> Path:
    return runs_dir(spatial_root) / run_id


__all__ = [
    "event_alignment_to_dict",
    "pose_sample_to_dict",
    "render_report_markdown",
    "run_output_dir",
    "runs_dir",
    "spatial_replay_to_dict",
    "spatial_validation_to_dict",
    "trajectory_segment_to_dict",
    "write_spatial_replay_artefacts",
]
