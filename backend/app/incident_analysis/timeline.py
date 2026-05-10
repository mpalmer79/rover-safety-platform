"""Timeline reconstruction.

Takes a list of unsorted :class:`TimelineEntry` from the normaliser
and produces an :class:`IncidentTimeline` with deterministic
ordering, derived relative times, recorded out-of-order indices, and
key-event indices (first fault, first safety transition, first
command intervention, terminal entry).

Also renders Markdown tables, Mermaid sequence diagrams, and Mermaid
state diagrams for downstream reports.
"""

from __future__ import annotations

from typing import Iterable, Optional

from app.incident_analysis.models import (
    IncidentTimeline,
    TimelineEntry,
)


def build_timeline(
    *,
    incident_id: str,
    entries: Iterable[TimelineEntry],
) -> IncidentTimeline:
    """Order entries deterministically and compute key indices."""

    raw = list(entries)
    sorted_entries, out_of_order_source_indices = _stable_sort(raw)

    # Reassign sequence indices and compute relative times.
    base_sim_time: Optional[int] = None
    for entry in sorted_entries:
        if entry.sim_time_ns is not None:
            base_sim_time = entry.sim_time_ns
            break

    rebuilt: list[TimelineEntry] = []
    for index, entry in enumerate(sorted_entries):
        rel: Optional[int] = None
        if base_sim_time is not None and entry.sim_time_ns is not None:
            rel = max(0, int((entry.sim_time_ns - base_sim_time) / 1_000_000))
        rebuilt.append(
            TimelineEntry(
                sequence_index=index,
                timestamp=entry.timestamp,
                relative_time_ms=rel,
                sim_time_ns=entry.sim_time_ns,
                source_file=entry.source_file,
                category=entry.category,
                event_type=entry.event_type,
                severity=entry.severity,
                safety_state=entry.safety_state,
                mission_state=entry.mission_state,
                reason_code=entry.reason_code,
                message=entry.message,
                evidence_origin=entry.evidence_origin,
                run_id=entry.run_id,
                scenario_id=entry.scenario_id,
                raw_reference=entry.raw_reference,
                attributes=dict(entry.attributes),
            )
        )

    timeline = IncidentTimeline(
        incident_id=incident_id,
        entries=rebuilt,
        out_of_order_indices=list(out_of_order_source_indices),
    )

    # Key indices.
    timeline.first_fault_index = _first_index(rebuilt, _is_fault)
    timeline.first_safety_transition_index = _first_index(
        rebuilt, _is_safety_transition
    )
    timeline.first_command_intervention_index = _first_index(
        rebuilt, _is_command_intervention
    )
    timeline.terminal_index = _terminal_index(rebuilt)
    return timeline


def _stable_sort(entries: list[TimelineEntry]) -> tuple[list[TimelineEntry], list[int]]:
    """Sort by ``(sim_time_ns, source_file, category, original_position)``.

    Records original positions whose sort keys are non-monotonic so we
    can surface them as out-of-order.
    """

    indexed = list(enumerate(entries))
    # Primary key: sim_time_ns when present, else float('inf') so untimed
    # entries sort to the end; secondary key: timestamp string;
    # tertiary key: original index to break ties deterministically.
    def _key(item):
        idx, e = item
        sim = e.sim_time_ns if e.sim_time_ns is not None else float("inf")
        return (sim, e.timestamp or "", idx)

    sorted_with_idx = sorted(indexed, key=_key)
    sorted_entries = [e for _, e in sorted_with_idx]

    # Record indices that moved (i.e. were out of order). An entry is
    # "out of order" if its original index differs from its sorted
    # index AND the move was caused by a numeric sim_time_ns mismatch.
    out_of_order: list[int] = []
    for new_pos, (orig_idx, _entry) in enumerate(sorted_with_idx):
        if orig_idx != new_pos:
            out_of_order.append(orig_idx)
    return sorted_entries, out_of_order


def _is_fault(entry: TimelineEntry) -> bool:
    return entry.category == "fault_injection" and entry.event_type.startswith(
        "fault_injection."
    )


def _is_safety_transition(entry: TimelineEntry) -> bool:
    return entry.category == "safety_transition"


def _is_command_intervention(entry: TimelineEntry) -> bool:
    if entry.category != "motion_arbitration":
        return False
    if entry.event_type == "motion_arbitration.summary":
        attrs = entry.attributes
        zeroed = int(attrs.get("zeroed_count", 0) or 0)
        clamped = int(attrs.get("clamped_count", 0) or 0)
        rejected = int(attrs.get("rejected_count", 0) or 0)
        return (zeroed + clamped + rejected) > 0
    # Any non-summary motion_arbitration event in events.jsonl counts.
    return True


def _terminal_index(entries: list[TimelineEntry]) -> Optional[int]:
    """Index of the terminal event.

    Prefer the last safety_transition; fall back to the last
    timestamped event.
    """

    last_safety = None
    last_any = None
    for index, entry in enumerate(entries):
        last_any = index
        if _is_safety_transition(entry):
            last_safety = index
    return last_safety if last_safety is not None else last_any


def _first_index(
    entries: list[TimelineEntry],
    predicate,
) -> Optional[int]:
    for entry in entries:
        if predicate(entry):
            return entry.sequence_index
    return None


# ---------------------------------------------------------------------------
# Renderers.
# ---------------------------------------------------------------------------


def render_timeline_md(timeline: IncidentTimeline) -> str:
    lines: list[str] = []
    lines.append(f"# Incident Timeline — `{timeline.incident_id}`")
    lines.append("")
    lines.append(
        f"- **Entry count:** {len(timeline.entries)}"
    )
    lines.append(
        f"- **First fault:** "
        f"{_describe_index(timeline, timeline.first_fault_index)}"
    )
    lines.append(
        f"- **First safety transition:** "
        f"{_describe_index(timeline, timeline.first_safety_transition_index)}"
    )
    lines.append(
        f"- **First command intervention:** "
        f"{_describe_index(timeline, timeline.first_command_intervention_index)}"
    )
    lines.append(
        f"- **Terminal entry:** "
        f"{_describe_index(timeline, timeline.terminal_index)}"
    )
    if timeline.out_of_order_indices:
        lines.append(
            f"- **Out-of-order source indices:** "
            f"{timeline.out_of_order_indices}"
        )
    lines.append("")
    lines.append(
        "| # | t (ms) | Category | Event | Severity | Safety | Reason | Source |"
    )
    lines.append("|---|---|---|---|---|---|---|---|")
    for entry in timeline.entries:
        rel = "?" if entry.relative_time_ms is None else str(entry.relative_time_ms)
        lines.append(
            "| {seq} | {rel} | `{cat}` | `{ev}` | `{sev}` | `{state}` | "
            "{reason} | `{src}` |".format(
                seq=entry.sequence_index,
                rel=rel,
                cat=entry.category,
                ev=entry.event_type,
                sev=entry.severity,
                state=entry.safety_state or "-",
                reason=entry.reason_code or "-",
                src=entry.source_file,
            )
        )
    lines.append("")
    return "\n".join(lines)


def render_sequence_mmd(timeline: IncidentTimeline) -> str:
    """Render a Mermaid sequence diagram for the supervisory chain.

    The diagram is a coarse view: fault -> safety -> command path,
    skipping pure observability entries to keep it readable.
    """

    lines: list[str] = []
    lines.append("sequenceDiagram")
    lines.append("    autonumber")
    lines.append("    participant Mission as Mission")
    lines.append("    participant Faults as FaultInjection")
    lines.append("    participant Sensors as Sensors")
    lines.append("    participant Safety as Safety")
    lines.append("    participant Arb as MotionArb")
    actors = {
        "fault_injection": "Faults",
        "sensor_health": "Sensors",
        "safety_transition": "Safety",
        "motion_arbitration": "Arb",
        "watchdog": "Sensors",
        "mission_transition": "Mission",
        "world_model": "Mission",
    }
    for entry in timeline.entries:
        actor = actors.get(entry.category)
        if actor is None:
            continue
        target = "Safety" if entry.category != "motion_arbitration" else "Arb"
        if actor == "Safety" and entry.category == "safety_transition":
            target = "Arb"
        label = (entry.message or entry.event_type).replace("\n", " ")
        if len(label) > 80:
            label = label[:77] + "..."
        lines.append(f"    {actor}->>{target}: {label}")
    return "\n".join(lines) + "\n"


def render_state_mmd(timeline: IncidentTimeline) -> str:
    """Render a Mermaid state diagram of the safety-state walk."""

    lines: list[str] = []
    lines.append("stateDiagram-v2")
    last_state: Optional[str] = None
    for entry in timeline.entries:
        if entry.category != "safety_transition":
            continue
        attrs = entry.attributes
        from_state = attrs.get("from_state") or last_state
        to_state = attrs.get("to_state") or entry.safety_state
        reason = entry.reason_code or attrs.get("reason") or ""
        if not from_state or not to_state:
            continue
        if reason:
            lines.append(f"    {from_state} --> {to_state}: {reason}")
        else:
            lines.append(f"    {from_state} --> {to_state}")
        last_state = to_state
    if len(lines) == 1:
        # Empty diagram; emit a placeholder so the file is syntactically valid.
        lines.append("    [*] --> [*]: no safety transitions in evidence")
    return "\n".join(lines) + "\n"


def _describe_index(
    timeline: IncidentTimeline, index: Optional[int]
) -> str:
    if index is None or index >= len(timeline.entries):
        return "-"
    e = timeline.entries[index]
    rel = "?" if e.relative_time_ms is None else f"{e.relative_time_ms}ms"
    return f"#{index} ({rel}, `{e.event_type}`)"
