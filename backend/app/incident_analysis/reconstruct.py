"""End-to-end incident reconstruction entry point.

Wires the loader, normaliser, timeline builder, causality engine,
classifier, and reporter into a single pure-logic call:

    reconstruct_incident(runtime_run_dir=..., scenario_dir=...) -> Incident

The CLI ``rover_ws/tools/reconstruct_incident.py`` is a thin wrapper
that calls this function and persists the resulting bundle.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.incident_analysis.causality import build_causality_chains
from app.incident_analysis.classifier import classify_incident
from app.incident_analysis.foxglove import build_foxglove_hint
from app.incident_analysis.loader import load_evidence_bundle
from app.incident_analysis.models import (
    Incident,
    IncidentEvidenceStatus,
    IncidentOutcome,
    IncidentSeverity,
)
from app.incident_analysis.normalizer import normalise_bundle
from app.incident_analysis.reporter import (
    derive_operational_interpretation,
    derive_recommendations,
)
from app.incident_analysis.timeline import build_timeline


def reconstruct_incident(
    *,
    incident_id: str,
    runtime_run_dir: Optional[Path] = None,
    scenario_dir: Optional[Path] = None,
    runs_root: Optional[Path] = None,
    foxglove_layout_path: str = "foxglove/layouts/incident-review-layout.json",
) -> Incident:
    """Compose a fully-populated :class:`Incident` from the inputs.

    The function never writes; the caller persists with
    :func:`app.incident_analysis.reporter.write_incident_bundle`.
    """

    bundle = load_evidence_bundle(
        runtime_run_dir=runtime_run_dir,
        scenario_dir=scenario_dir,
        runs_root=runs_root,
    )
    entries = normalise_bundle(bundle)
    timeline = build_timeline(incident_id=incident_id, entries=entries)
    chains = build_causality_chains(timeline)
    severity, outcome, evidence_status, cause, missing, contradictions = classify_incident(
        bundle=bundle, timeline=timeline, chains=chains
    )

    safety_states = _safety_state_sequence(timeline)
    mission_states = _mission_state_sequence(timeline)
    fault_ids = _fault_ids(timeline)

    foxglove_hint = build_foxglove_hint(
        timeline=timeline, layout_path=foxglove_layout_path
    )

    incident = Incident(
        incident_id=incident_id,
        run_id=(bundle.runtime.run_id if bundle.runtime else None) or (
            bundle.scenario.scenario_id if bundle.scenario else None
        ),
        scenario_id=bundle.scenario.scenario_id if bundle.scenario else None,
        severity=severity,
        outcome=outcome,
        evidence_status=evidence_status,
        cause=cause,
        safety_states=tuple(safety_states),
        mission_states=tuple(mission_states),
        fault_ids=tuple(fault_ids),
        timeline=timeline,
        causality_chains=chains,
        foxglove_hint=foxglove_hint,
        evidence_manifest=bundle.as_evidence_manifest(),
        missing_evidence=missing,
        contradictions=contradictions,
        generated_at_utc=datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
    )
    incident.operational_interpretation = derive_operational_interpretation(incident)
    incident.recommended_follow_up = derive_recommendations(incident)
    return incident


def _safety_state_sequence(timeline) -> list[str]:
    out: list[str] = []
    for entry in timeline.entries:
        if entry.category != "safety_transition":
            continue
        state = entry.safety_state or entry.attributes.get("to_state")
        if state and (not out or out[-1] != state):
            out.append(state)
    return out


def _mission_state_sequence(timeline) -> list[str]:
    out: list[str] = []
    for entry in timeline.entries:
        if entry.category != "mission_transition":
            continue
        state = entry.mission_state or entry.attributes.get("to_state")
        if state and (not out or out[-1] != state):
            out.append(state)
    return out


def _fault_ids(timeline) -> list[str]:
    seen: list[str] = []
    seen_set: set[str] = set()
    for entry in timeline.entries:
        if entry.category != "fault_injection":
            continue
        fid = entry.attributes.get("fault_id")
        if isinstance(fid, str) and fid not in seen_set:
            seen.append(fid)
            seen_set.add(fid)
    return seen
