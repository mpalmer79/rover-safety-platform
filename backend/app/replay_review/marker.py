"""Replay marker generator.

Reads incident timeline entries (the Phase 6 :class:`IncidentTimeline`)
and produces :class:`ReplayMarker` instances aligned to replay time.

A marker is emitted only when the corresponding evidence exists. If
the timeline has no first-fault entry the marker for ``first_fault``
is omitted — the generator never invents a marker.

When a timeline entry lacks ``sim_time_ns`` the marker is emitted
with ``alignment="partial"`` so the operator knows it can be aligned
only to relative time.
"""

from __future__ import annotations

from typing import Iterable, Optional

from app.replay_review.models import (
    ReplayEvidenceOrigin,
    ReplayMarker,
)


_OUTCOME_MAP: dict[str, tuple[str, str]] = {
    "controlled_degradation": ("controlled_degradation", "Run terminated in controlled degradation"),
    "safe_stop_success": ("safe_stop_success", "Run terminated in SAFE_STOP success"),
    "estop_latched": ("estop_latched", "Run terminated in E_STOP_LATCHED"),
    "mission_aborted": ("mission_aborted", "Run terminated with mission abort"),
    "recovery_success": ("recovery_success", "Run terminated after successful recovery"),
    "recovery_failed": ("recovery_failed", "Run terminated after failed recovery"),
    "inconclusive": ("terminal_outcome", "Run terminated with inconclusive outcome"),
}


def build_markers(
    *,
    incident: dict,
    causality_confidence: Optional[str] = None,
) -> list[ReplayMarker]:
    """Return markers for the supplied :class:`Incident` dict.

    ``incident`` is the dict produced by
    :meth:`Incident.as_dict`; passing the dict (rather than the
    Incident object) keeps the replay layer decoupled from the
    incident_analysis module's import surface.
    """

    timeline = incident.get("timeline") or {}
    entries = timeline.get("entries") or []
    safety_states = incident.get("safety_states") or []
    outcome = incident.get("outcome", "")
    confidence = causality_confidence
    if confidence is None and incident.get("cause"):
        confidence = incident["cause"].get("confidence")
    confidence = confidence or "unknown"

    markers: list[ReplayMarker] = []

    def _make_marker(
        *,
        marker_id: str,
        label: str,
        description: str,
        timeline_index: int,
    ) -> Optional[ReplayMarker]:
        if (
            timeline_index is None
            or timeline_index < 0
            or timeline_index >= len(entries)
        ):
            return None
        entry = entries[timeline_index]
        sim = entry.get("sim_time_ns")
        rel = entry.get("relative_time_ms")
        alignment = "exact" if isinstance(sim, (int, float)) else (
            "partial" if isinstance(rel, (int, float)) else "unaligned"
        )
        origin_raw = entry.get("evidence_origin", "unknown")
        try:
            origin = ReplayEvidenceOrigin(origin_raw)
        except ValueError:
            origin = ReplayEvidenceOrigin.UNKNOWN
        return ReplayMarker(
            marker_id=marker_id,
            label=label,
            description=description,
            timeline_index=timeline_index,
            relative_time_ms=int(rel) if isinstance(rel, (int, float)) else None,
            sim_time_ns=int(sim) if isinstance(sim, (int, float)) else None,
            source_event_id=str(entry.get("raw_reference") or ""),
            source_file=str(entry.get("source_file") or ""),
            confidence=str(confidence),
            evidence_origin=origin,
            alignment=alignment,
        )

    # Key markers from the timeline indices.
    pairs: tuple[tuple[str, str, str, Optional[int]], ...] = (
        (
            "first_fault",
            "First fault",
            "First fault_injection.fired entry observed in evidence",
            timeline.get("first_fault_index"),
        ),
        (
            "first_safety_transition",
            "First safety transition",
            "First safety_transition.entered entry observed in evidence",
            timeline.get("first_safety_transition_index"),
        ),
        (
            "first_command_intervention",
            "First command intervention",
            "First motion arbitration entry that clamped, zeroed, or rejected a command",
            timeline.get("first_command_intervention_index"),
        ),
        (
            "terminal_outcome",
            "Terminal outcome",
            f"Terminal entry; outcome={outcome or 'unknown'}",
            timeline.get("terminal_index"),
        ),
    )
    for marker_id, label, description, idx in pairs:
        marker = _make_marker(
            marker_id=marker_id,
            label=label,
            description=description,
            timeline_index=idx if isinstance(idx, int) else -1,
        )
        if marker is not None:
            markers.append(marker)

    # Markers derived from the safety state walk: SAFE_STOP / E_STOP /
    # mission abort / recovery start / recovery completion. We pick
    # the first timeline entry whose terminal state matches.
    for state, marker_id, label in (
        ("SAFE_STOP", "safe_stop", "First SAFE_STOP transition"),
        ("E_STOP_LATCHED", "estop_latched", "First E_STOP_LATCHED transition"),
        ("RECOVERY", "recovery_started", "First RECOVERY transition"),
    ):
        index = _first_index_for_state(entries, state)
        if index is not None:
            marker = _make_marker(
                marker_id=marker_id,
                label=label,
                description=f"First entry with safety_state={state}",
                timeline_index=index,
            )
            if marker is not None:
                markers.append(marker)

    if outcome == "recovery_success":
        # Approximate recovery completion as the first ACTIVE_NORMAL
        # after the first RECOVERY.
        recovery_index = _first_index_for_state(entries, "RECOVERY")
        if recovery_index is not None:
            for i, entry in enumerate(entries[recovery_index + 1 :], start=recovery_index + 1):
                if entry.get("safety_state") == "ACTIVE_NORMAL":
                    marker = _make_marker(
                        marker_id="recovery_completed",
                        label="Recovery completed",
                        description="First ACTIVE_NORMAL entry after RECOVERY",
                        timeline_index=i,
                    )
                    if marker is not None:
                        markers.append(marker)
                    break

    if outcome == "mission_aborted":
        # Find the first mission-state transition that mentions abort.
        for i, entry in enumerate(entries):
            if entry.get("category") != "mission_transition":
                continue
            label = entry.get("event_type", "")
            attrs = entry.get("attributes", {}) or {}
            if "abort" in label.lower() or attrs.get("to_state") == "MISSION_ABORTED":
                marker = _make_marker(
                    marker_id="mission_abort",
                    label="Mission abort",
                    description="First mission_transition entry with abort",
                    timeline_index=i,
                )
                if marker is not None:
                    markers.append(marker)
                break

    return markers


def _first_index_for_state(entries: list[dict], state: str) -> Optional[int]:
    for i, entry in enumerate(entries):
        if entry.get("category") != "safety_transition":
            continue
        if entry.get("safety_state") == state:
            return i
        attrs = entry.get("attributes", {}) or {}
        if attrs.get("to_state") == state:
            return i
    return None


def alignment_status(markers: Iterable[ReplayMarker]) -> str:
    """Aggregate the per-marker alignment into a single label.

    * ``exact`` when every marker has ``alignment=exact``.
    * ``partial`` when at least one marker is ``partial``.
    * ``unaligned`` when every marker is ``unaligned``.
    """

    seen_exact = False
    seen_partial = False
    seen_unaligned = False
    any_marker = False
    for m in markers:
        any_marker = True
        if m.alignment == "exact":
            seen_exact = True
        elif m.alignment == "partial":
            seen_partial = True
        else:
            seen_unaligned = True
    if not any_marker:
        return "no_markers"
    if seen_partial or (seen_unaligned and seen_exact):
        return "partial"
    if seen_exact and not seen_unaligned:
        return "exact"
    return "unaligned"
