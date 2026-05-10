"""Foxglove replay hint generator.

Foxglove is a separate runtime; this module emits *metadata* — topic
suggestions, timeline markers, layout pointer — so an operator can
open the underlying recording with the right context. Tests do not
require Foxglove to be installed; the artefacts are JSON.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from app.incident_analysis.models import (
    FoxgloveReplayHint,
    IncidentTimeline,
)


_DEFAULT_RECOMMENDED_TOPICS: tuple[str, ...] = (
    "/safety/state",
    "/safety/events",
    "/cmd_vel_requested",
    "/cmd_vel_authorized",
    "/scan",
    "/imu",
    "/odom",
    "/tf",
    "/tf_static",
    "/system/health",
    "/diagnostics/runtime_summary",
    "/mission/state",
    "/mission/events",
    "/mission/progress",
    "/world_model/state",
    "/replay/markers",
)

_DEFAULT_COMMAND_TOPICS: tuple[str, ...] = (
    "/cmd_vel_requested",
    "/cmd_vel_authorized",
)

_DEFAULT_FAULT_TOPICS: tuple[str, ...] = (
    "/safety/events",
    "/fault_injection/events",
)

_DEFAULT_DIAGNOSTIC_TOPICS: tuple[str, ...] = (
    "/system/health",
    "/diagnostics/runtime_summary",
    "/diagnostics/topic_freshness",
    "/diagnostics/bridge_health",
)

_DEFAULT_LAYOUT_PATH: str = "foxglove/layouts/incident-review-layout.json"


def build_foxglove_hint(
    *,
    timeline: IncidentTimeline,
    layout_path: str = _DEFAULT_LAYOUT_PATH,
) -> FoxgloveReplayHint:
    markers = _markers_for(timeline)
    return FoxgloveReplayHint(
        recommended_topics=_DEFAULT_RECOMMENDED_TOPICS,
        timeline_markers=markers,
        safety_state_topic="/safety/state",
        mission_state_topic="/mission/state",
        command_topics=_DEFAULT_COMMAND_TOPICS,
        fault_topics=_DEFAULT_FAULT_TOPICS,
        diagnostic_topics=_DEFAULT_DIAGNOSTIC_TOPICS,
        layout_path=layout_path,
        notes=(
            "Open the recorded bag in Foxglove and load the layout from "
            "the path above. Markers correspond to first-fault, first-"
            "safety-transition, first-command-intervention, and the "
            "terminal entry on the timeline. Each marker carries the "
            "underlying sim_time_ns when available."
        ),
    )


def _markers_for(timeline: IncidentTimeline) -> tuple[dict, ...]:
    """Three-to-four marker dicts for the key indices."""

    out: list[dict] = []
    for label, idx, category in (
        ("first_fault", timeline.first_fault_index, "fault_injection"),
        ("first_safety_transition", timeline.first_safety_transition_index, "safety_transition"),
        (
            "first_command_intervention",
            timeline.first_command_intervention_index,
            "motion_arbitration",
        ),
        ("terminal", timeline.terminal_index, "terminal"),
    ):
        if idx is None or idx >= len(timeline.entries):
            continue
        entry = timeline.entries[idx]
        out.append(
            {
                "label": label,
                "category": category,
                "sequence_index": entry.sequence_index,
                "sim_time_ns": entry.sim_time_ns,
                "relative_time_ms": entry.relative_time_ms,
                "event_type": entry.event_type,
                "message": entry.message,
            }
        )
    return tuple(out)


# ---------------------------------------------------------------------------
# Layout file accessor.
# ---------------------------------------------------------------------------


DEFAULT_LAYOUT: dict = {
    "configById": {
        "Plot!safety": {
            "title": "Safety state",
            "paths": [
                {
                    "value": "/safety/state.state",
                    "label": "safety state",
                }
            ],
        },
        "Plot!cmd_vel": {
            "title": "Authorised vs requested cmd_vel",
            "paths": [
                {"value": "/cmd_vel_requested.linear.x", "label": "requested linear"},
                {"value": "/cmd_vel_authorized.linear.x", "label": "authorised linear"},
            ],
        },
        "DiagnosticSummary!system": {
            "title": "System health",
            "topic": "/system/health",
        },
        "Log!safety_events": {
            "title": "Safety events",
            "topic": "/safety/events",
        },
        "Log!mission_events": {
            "title": "Mission events",
            "topic": "/mission/events",
        },
    },
    "globalVariables": {
        "incident_review_layout_version": "1.0.0",
    },
    "layout": {
        "first": "Plot!safety",
        "second": {
            "first": "Plot!cmd_vel",
            "second": {
                "first": "DiagnosticSummary!system",
                "second": {
                    "first": "Log!safety_events",
                    "second": "Log!mission_events",
                    "direction": "row",
                },
                "direction": "row",
            },
            "direction": "row",
        },
        "direction": "column",
    },
}


def write_default_layout(path: Path) -> None:
    """Write the canonical Foxglove layout JSON if it doesn't exist.

    The layout is committed under ``foxglove/layouts/`` so reviewers
    can load it without the analysis layer.
    """

    import json

    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(DEFAULT_LAYOUT, indent=2, sort_keys=True), encoding="utf-8")
