"""Replay manifest generator.

Produces the per-incident ``replay-review-manifest.json`` (and an
accompanying Markdown summary). The manifest records:

* incident id, run id, scenario id;
* the Phase 6 ``evidence_status`` (so replay never overrides it);
* the bag-status aggregate from :mod:`bag_index`;
* the expected vs available topics;
* a pointer to the Foxglove layout + session;
* a count of timeline markers;
* the operator review steps;
* the canonical known-limitations callout.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

from app.replay_review.models import (
    BagIndex,
    ReplayExecutionStatus,
    ReplayReviewManifest,
    ReplayTopic,
    EXPECTED_REPLAY_TOPICS,
)


_DEFAULT_REVIEW_STEPS: tuple[str, ...] = (
    "Open Foxglove Studio.",
    "Layout -> Import from file -> select foxglove/layouts/incident-review-layout.json.",
    "Data source -> Open local file -> select the bag listed in bag_indices[].path (when present).",
    "Use the timeline_markers list to scrub the playhead to first_fault, first_safety_transition, "
    "first_command_intervention, and the terminal entry.",
    "Cross-reference the safety state plot, the cmd_vel plot, and the safety-events log against "
    "the incident report's claims.",
    "Record any discrepancy in a separate document; do not mutate the incident bundle.",
)

_DEFAULT_KNOWN_LIMITATIONS: tuple[str, ...] = (
    "The platform is **not** safety-certified. This replay review is "
    "engineering analysis material.",
    "Live bag replay requires Foxglove Studio + a recorded bag on a "
    "ROS 2 Jazzy host. CI runs do not exercise live replay.",
    "When the bag directory is missing the manifest reports "
    "`bag_status=missing_bag`; the review remains valid as a static "
    "incident report but the visual playback step cannot be performed.",
    "Markers without `sim_time_ns` are aligned to relative time only; "
    "the Foxglove playhead must be aligned manually using the surrounding "
    "context.",
)


def default_replay_topics() -> tuple[ReplayTopic, ...]:
    """Default set of topics every replay review session expects."""

    purposes = {
        "/clock": "ROS time reference",
        "/scan": "LiDAR sensor stream",
        "/imu": "IMU sensor stream",
        "/odom": "Wheel odometry",
        "/tf": "Dynamic transforms",
        "/tf_static": "Static transforms",
        "/cmd_vel_requested": "Mission / Nav2 motion request",
        "/cmd_vel_authorized": "Safety supervisor authorised motion",
        "/safety/state": "Safety supervisor state",
        "/safety/events": "Safety supervisor event stream",
        "/system/health": "Aggregate diagnostics",
        "/mission/state": "Mission state",
        "/mission/events": "Mission event stream",
        "/mission/progress": "Waypoint progress",
        "/world_model/state": "World model snapshot",
    }
    out: list[ReplayTopic] = []
    for name in EXPECTED_REPLAY_TOPICS:
        out.append(
            ReplayTopic(
                name=name,
                purpose=purposes.get(name, ""),
                required=name
                in {
                    "/safety/state",
                    "/safety/events",
                    "/cmd_vel_authorized",
                    "/cmd_vel_requested",
                    "/system/health",
                    "/clock",
                },
            )
        )
    return tuple(out)


def build_manifest(
    *,
    incident: dict,
    bag_indices: Iterable[BagIndex],
    foxglove_layout_path: str,
    foxglove_session_path: str,
    timeline_marker_count: int,
    review_steps: Iterable[str] = _DEFAULT_REVIEW_STEPS,
    known_limitations: Iterable[str] = _DEFAULT_KNOWN_LIMITATIONS,
) -> ReplayReviewManifest:
    """Compose a :class:`ReplayReviewManifest` from the inputs."""

    bag_indices = tuple(bag_indices)
    expected = default_replay_topics()
    available = set()
    inventory_observed = False
    for bag in bag_indices:
        if bag.inventory_topics:
            inventory_observed = True
        for topic in bag.inventory_topics:
            available.add(topic)
    available_tuple = tuple(sorted(available))
    # ``missing_topics`` is only meaningful when at least one bag's
    # inventory was readable. Without an inventory we cannot say a
    # topic is missing from a bag — only that no bag was inspected.
    if inventory_observed:
        expected_required = {t.name for t in expected if t.required}
        missing_required = tuple(sorted(expected_required - available))
    else:
        missing_required = ()

    bag_status = _aggregate_bag_status(bag_indices, incident=incident)

    return ReplayReviewManifest(
        incident_id=incident.get("incident_id", ""),
        run_id=incident.get("run_id"),
        scenario_id=incident.get("scenario_id"),
        evidence_status=str(incident.get("evidence_status", "")),
        bag_status=bag_status,
        bag_indices=bag_indices,
        expected_topics=expected,
        available_topics=available_tuple,
        missing_topics=missing_required,
        foxglove_layout_path=foxglove_layout_path,
        foxglove_session_path=foxglove_session_path,
        timeline_marker_count=timeline_marker_count,
        review_steps=tuple(review_steps),
        known_limitations=tuple(known_limitations),
        generated_at_utc=datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
    )


def _aggregate_bag_status(
    bag_indices: tuple[BagIndex, ...], *, incident: dict
) -> ReplayExecutionStatus:
    """Decide the manifest-level bag status.

    Rules:

    * If the incident's evidence_status is ``static_only`` and no bag
      chunks were detected, the manifest reports ``static_only``
      (a static incident does not need a bag and is not a
      missing-bag failure).
    * Otherwise, if any candidate has bag chunks **and** metadata,
      report ``ready``.
    * If any candidate has chunks or metadata but not both, report
      ``partial``.
    * Otherwise report ``missing_bag``.
    """

    has_chunks = any(b.has_bag_chunks for b in bag_indices)
    has_metadata = any(b.has_metadata for b in bag_indices)
    evidence_status = incident.get("evidence_status", "")

    if has_chunks and has_metadata:
        return ReplayExecutionStatus.READY
    if evidence_status == "static_only" and not has_chunks and not has_metadata:
        return ReplayExecutionStatus.STATIC_ONLY
    if has_chunks or has_metadata:
        return ReplayExecutionStatus.PARTIAL
    return ReplayExecutionStatus.MISSING_BAG


def render_manifest_md(manifest: ReplayReviewManifest) -> str:
    lines: list[str] = []
    lines.append(f"# Replay Review Manifest — `{manifest.incident_id}`")
    lines.append("")
    lines.append(
        "_Generated by `rover_ws/tools/build_replay_review_bundle.py`. "
        "The platform is **not safety-certified**; this manifest is "
        "engineering analysis material._"
    )
    lines.append("")
    lines.append(f"- **Run id:** `{manifest.run_id or '-'}`")
    lines.append(f"- **Scenario id:** `{manifest.scenario_id or '-'}`")
    lines.append(f"- **Evidence status (Phase 6):** `{manifest.evidence_status}`")
    lines.append(f"- **Bag status (Phase 7):** `{manifest.bag_status.value}`")
    lines.append(f"- **Foxglove layout:** `{manifest.foxglove_layout_path}`")
    lines.append(f"- **Foxglove session:** `{manifest.foxglove_session_path}`")
    lines.append(f"- **Timeline markers:** {manifest.timeline_marker_count}")
    lines.append(f"- **Generated:** {manifest.generated_at_utc}")
    lines.append("")
    lines.append("## Bag artefacts")
    lines.append("")
    if not manifest.bag_indices:
        lines.append("_No bag candidates inspected._")
    else:
        for index in manifest.bag_indices:
            lines.append(
                f"- `{index.bag_root}` -> "
                f"`{index.status.value}` "
                f"({len(index.artifacts)} file(s), "
                f"{len(index.inventory_topics)} topic(s))"
            )
            for note in index.notes:
                lines.append(f"  - _{note}_")
    lines.append("")
    lines.append("## Expected topics")
    lines.append("")
    lines.append("| Topic | Purpose | Required |")
    lines.append("|---|---|---|")
    for topic in manifest.expected_topics:
        lines.append(
            f"| `{topic.name}` | {topic.purpose or '-'} | "
            f"{'yes' if topic.required else 'no'} |"
        )
    lines.append("")
    if manifest.missing_topics:
        lines.append("## Missing required topics")
        lines.append("")
        for name in manifest.missing_topics:
            lines.append(f"- `{name}`")
        lines.append("")
    lines.append("## Review steps")
    lines.append("")
    for step in manifest.review_steps:
        lines.append(f"- {step}")
    lines.append("")
    lines.append("## Known limitations")
    lines.append("")
    for line in manifest.known_limitations:
        lines.append(f"- {line}")
    lines.append("")
    return "\n".join(lines)
