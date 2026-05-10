"""Foxglove session metadata generator.

The output is a plain JSON document the project uses internally to
record per-incident replay context (layout pointer, panel hints,
marker overlays, recommended data source). It is **not** an
official Foxglove session import format; the ``schema_version``
field makes that explicit.

The module performs no I/O on Foxglove; it produces a value object
that the caller persists.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from app.replay_review.models import (
    EXPECTED_REPLAY_TOPICS,
    FoxglovePanelHint,
    FoxgloveSession,
    ReplayMarker,
)


_DEFAULT_PANEL_HINTS: tuple[FoxglovePanelHint, ...] = (
    FoxglovePanelHint(
        panel_id="safety-state-plot",
        title="Safety state",
        topics=("/safety/state",),
        notes="Step-plot of the supervisor state across the run.",
    ),
    FoxglovePanelHint(
        panel_id="cmd-vel-plot",
        title="Requested vs authorised cmd_vel",
        topics=("/cmd_vel_requested", "/cmd_vel_authorized"),
        notes="Verify SAFE_STOP zeroing visually; authorised should never exceed requested in NORMAL.",
    ),
    FoxglovePanelHint(
        panel_id="system-health",
        title="System health",
        topics=("/system/health",),
        notes="Aggregate diagnostic; downgrades correlate with sensor faults.",
    ),
    FoxglovePanelHint(
        panel_id="safety-events",
        title="Safety events log",
        topics=("/safety/events",),
        notes="Cross-check against incident-report.md.",
    ),
    FoxglovePanelHint(
        panel_id="mission-events",
        title="Mission events log",
        topics=("/mission/events", "/mission/state", "/mission/progress"),
        notes="Correlate mission-side intent with safety response.",
    ),
)


_DEFAULT_REVIEW_NOTES: str = (
    "Open the canonical layout from foxglove/layouts/incident-review-layout.json "
    "(the path in layout_path). The marker_overlays list mirrors the "
    "incident timeline's first_fault, first_safety_transition, "
    "first_command_intervention, and terminal indices; use the "
    "sim_time_ns field (when present) to align the playhead. The "
    "schema_version is rover-replay-review/1 — this document is "
    "internal to the project and is NOT an official Foxglove import "
    "format."
)


def build_foxglove_session(
    *,
    incident_id: str,
    layout_path: str,
    recommended_data_source: str,
    markers: Iterable[ReplayMarker],
    panel_hints: tuple[FoxglovePanelHint, ...] = _DEFAULT_PANEL_HINTS,
    review_notes: str = _DEFAULT_REVIEW_NOTES,
    known_limitations: Iterable[str] = (),
) -> FoxgloveSession:
    overlays = tuple(
        {
            "marker_id": m.marker_id,
            "label": m.label,
            "sim_time_ns": m.sim_time_ns,
            "relative_time_ms": m.relative_time_ms,
            "timeline_index": m.timeline_index,
            "alignment": m.alignment,
            "evidence_origin": m.evidence_origin.value,
        }
        for m in markers
    )
    return FoxgloveSession(
        incident_id=incident_id,
        layout_path=layout_path,
        recommended_data_source=recommended_data_source,
        expected_topics=EXPECTED_REPLAY_TOPICS,
        panel_hints=panel_hints,
        marker_overlays=overlays,
        review_notes=review_notes,
        known_limitations=tuple(known_limitations),
    )


def write_session(session: FoxgloveSession, *, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(session.as_dict(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
