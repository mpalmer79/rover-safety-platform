"""Bridge from rehearsal runtime to the replay-review artefact shape.

The rehearsal produces a *simulated* event stream. The replay
bundle records that origin explicitly. No bag-backed claims are
made; the ``bag_backed`` flag is always ``False`` for a rehearsal
replay.
"""

from __future__ import annotations

from typing import Iterable, Mapping

from .models import (
    MissionRehearsalEvent,
    MissionRehearsalPlan,
    MissionRehearsalReplayBundle,
    MissionRehearsalRuntime,
    RehearsalEventType,
    RehearsalEvidenceStatus,
    RehearsalStatus,
)
from .rehearsal_events import deterministic_hash


def _build_markers(
    events: Iterable[MissionRehearsalEvent],
) -> tuple[Mapping[str, object], ...]:
    markers: list[Mapping[str, object]] = []
    for event in events:
        if event.event_type in {
            RehearsalEventType.MISSION.value,
            RehearsalEventType.MOTION.value,
            RehearsalEventType.SAFETY.value,
            RehearsalEventType.SUPERVISOR.value,
        }:
            markers.append(
                {
                    "marker_id": event.event_id,
                    "type": event.event_type,
                    "subtype": event.event_subtype,
                    "time_ns": event.event_time_ns,
                    "deterministic_hash": event.deterministic_hash,
                    "description": event.description,
                }
            )
    return tuple(markers)


def render_replay_review_markdown(
    *,
    bundle: MissionRehearsalReplayBundle,
    plan: MissionRehearsalPlan,
    runtime: MissionRehearsalRuntime,
) -> str:
    lines: list[str] = []
    lines.append(f"# Rehearsal replay review: {plan.mission_id}")
    lines.append("")
    lines.append("_Simulation-only. No bag artefacts exist for this rehearsal._")
    lines.append("")
    lines.append(f"- **Mission id:** `{plan.mission_id}`")
    lines.append(f"- **Plan hash:** `{plan.deterministic_hash}`")
    lines.append(f"- **Runtime hash:** `{runtime.deterministic_hash}`")
    lines.append(f"- **Evidence status:** `{bundle.evidence_status}`")
    lines.append(f"- **Bag-backed:** {bundle.bag_backed}")
    lines.append(f"- **Final status:** `{runtime.final_status}`")
    lines.append(f"- **Review status:** `{bundle.review_status}`")
    lines.append(f"- **Markers recorded:** {len(bundle.replay_markers)}")
    lines.append("")
    if bundle.notes:
        lines.append("## Notes")
        for note in bundle.notes:
            lines.append(f"- {note}")
        lines.append("")
    lines.append("## Authority statement")
    lines.append("")
    lines.append(
        "This replay review is generated from a simulation-only "
        "rehearsal. No live bag exists. The runtime safety supervisor "
        "remains authoritative for any future real run."
    )
    lines.append("")
    return "\n".join(lines)


def build_replay_bundle(
    *,
    plan: MissionRehearsalPlan,
    runtime: MissionRehearsalRuntime,
) -> MissionRehearsalReplayBundle:
    review_status = "passed" if runtime.final_status == RehearsalStatus.COMPLETED.value else "partial"
    if runtime.final_status in {RehearsalStatus.REJECTED.value, RehearsalStatus.ABORTED.value}:
        review_status = "rejected"
    markers = _build_markers(runtime.events)
    notes = [
        "Rehearsal evidence is simulation-only; no rosbag exists.",
        f"Plan deterministic hash: {plan.deterministic_hash}",
        f"Runtime deterministic hash: {runtime.deterministic_hash}",
    ]
    bundle_hash_payload = {
        "mission_id": plan.mission_id,
        "plan_hash": plan.deterministic_hash,
        "runtime_hash": runtime.deterministic_hash,
        "review_status": review_status,
        "markers": [m["deterministic_hash"] for m in markers],
    }
    bundle = MissionRehearsalReplayBundle(
        mission_id=plan.mission_id,
        evidence_status=RehearsalEvidenceStatus.SIMULATED.value,
        bag_backed=False,
        replay_markers=markers,
        review_status=review_status,
        rendered_markdown="",
        deterministic_hash=deterministic_hash(bundle_hash_payload),
        notes=tuple(notes),
    )
    rendered = render_replay_review_markdown(
        bundle=bundle, plan=plan, runtime=runtime
    )
    # The dataclass is frozen; reconstruct with the rendered text.
    return MissionRehearsalReplayBundle(
        mission_id=bundle.mission_id,
        evidence_status=bundle.evidence_status,
        bag_backed=bundle.bag_backed,
        replay_markers=bundle.replay_markers,
        review_status=bundle.review_status,
        rendered_markdown=rendered,
        deterministic_hash=bundle.deterministic_hash,
        notes=bundle.notes,
    )
