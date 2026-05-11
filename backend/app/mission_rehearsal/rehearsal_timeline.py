"""Timeline renderer (Markdown + Mermaid + JSON)."""

from __future__ import annotations

from typing import Iterable

from .models import (
    MissionRehearsalEvent,
    MissionRehearsalTimeline,
)


def render_timeline_markdown(
    *,
    mission_id: str,
    transitions: Iterable[tuple[str, str, str]],
    events: Iterable[MissionRehearsalEvent],
) -> str:
    lines: list[str] = [f"# Mission rehearsal timeline: {mission_id}", ""]
    lines.append("## State transitions")
    lines.append("")
    for src, dst, reason in transitions:
        lines.append(f"- `{src}` → `{dst}` — _{reason}_")
    lines.append("")
    lines.append("## Event stream")
    lines.append("")
    for event in events:
        lines.append(
            f"- {event.event_time_ns / 1_000_000_000:.1f}s "
            f"[{event.event_type}/{event.event_subtype}] "
            f"({event.severity}) `{event.event_id}` — {event.description}"
        )
    lines.append("")
    return "\n".join(lines)


def render_timeline_mermaid(
    transitions: Iterable[tuple[str, str, str]],
) -> str:
    lines: list[str] = ["flowchart TD"]
    seen: set[str] = set()
    transitions_list = list(transitions)
    for src, dst, _reason in transitions_list:
        for node in (src, dst):
            if node not in seen:
                lines.append(f"    {node}([{node}])")
                seen.add(node)
    for src, dst, reason in transitions_list:
        lines.append(f"    {src} -->|{reason}| {dst}")
    return "\n".join(lines)


def build_timeline(
    *,
    mission_id: str,
    transitions: tuple[tuple[str, str, str], ...],
    events: tuple[MissionRehearsalEvent, ...],
) -> MissionRehearsalTimeline:
    return MissionRehearsalTimeline(
        mission_id=mission_id,
        transitions=transitions,
        events=events,
        rendered_markdown=render_timeline_markdown(
            mission_id=mission_id, transitions=transitions, events=events
        ),
        rendered_mermaid=render_timeline_mermaid(transitions),
    )
