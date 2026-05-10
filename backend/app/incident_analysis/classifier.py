"""Incident classifier: derive severity, outcome, and evidence status from evidence.

The classifier is intentionally conservative. Severity is never
upgraded above what the evidence supports; missing files always
yield ``partial`` or worse. Contradictory evidence is surfaced
explicitly so the reporter can show it.
"""

from __future__ import annotations

from typing import Iterable, Optional

from app.incident_analysis.loader import LoadedEvidenceBundle
from app.incident_analysis.models import (
    CausalityChain,
    CausalityConfidence,
    IncidentCause,
    IncidentEvidenceStatus,
    IncidentOutcome,
    IncidentSeverity,
    IncidentTimeline,
)


_FORCED_ZERO_STATES: frozenset[str] = frozenset(
    {"BOOT", "INACTIVE", "SAFE_STOP", "E_STOP_LATCHED", "RECOVERY"}
)


def classify_incident(
    *,
    bundle: LoadedEvidenceBundle,
    timeline: IncidentTimeline,
    chains: list[CausalityChain],
) -> tuple[
    IncidentSeverity,
    IncidentOutcome,
    IncidentEvidenceStatus,
    Optional[IncidentCause],
    tuple[str, ...],
    tuple[str, ...],
]:
    """Return ``(severity, outcome, evidence_status, cause, missing, contradictions)``."""

    safety_states = _collect_safety_states(timeline)
    terminal = safety_states[-1] if safety_states else None

    severity = _derive_severity(timeline, terminal, chains)
    outcome = _derive_outcome(bundle, timeline, terminal, chains)
    evidence_status, missing, contradictions = _derive_evidence_status(
        bundle, timeline, chains
    )
    cause = _derive_cause(timeline, chains)
    return severity, outcome, evidence_status, cause, missing, contradictions


def _collect_safety_states(timeline: IncidentTimeline) -> list[str]:
    out: list[str] = []
    for entry in timeline.entries:
        if entry.category != "safety_transition":
            continue
        state = entry.safety_state or entry.attributes.get("to_state")
        if state and (not out or out[-1] != state):
            out.append(state)
    return out


def _derive_severity(
    timeline: IncidentTimeline,
    terminal: Optional[str],
    chains: list[CausalityChain],
) -> IncidentSeverity:
    if terminal == "E_STOP_LATCHED":
        return IncidentSeverity.HIGH
    if terminal == "SAFE_STOP":
        return IncidentSeverity.MODERATE
    if terminal in {"ACTIVE_DEGRADED", "ACTIVE_RESTRICTED"}:
        return IncidentSeverity.LOW
    if any(c.contradictions for c in chains):
        return IncidentSeverity.HIGH
    if any(
        e.category == "regression"
        and e.attributes.get("severity") == "critical_regression"
        for e in timeline.entries
    ):
        return IncidentSeverity.HIGH
    if any(
        e.category == "regression"
        and e.attributes.get("severity") == "regression"
        for e in timeline.entries
    ):
        return IncidentSeverity.MODERATE
    return IncidentSeverity.INFORMATIONAL


def _derive_outcome(
    bundle: LoadedEvidenceBundle,
    timeline: IncidentTimeline,
    terminal: Optional[str],
    chains: list[CausalityChain],
) -> IncidentOutcome:
    # Mission abort first (highest specificity).
    if bundle.scenario and bundle.scenario.evidence:
        observed = bundle.scenario.evidence.get("observed", {})
        if observed.get("final_mission_state") == "MISSION_ABORTED":
            return IncidentOutcome.MISSION_ABORTED
    if terminal == "E_STOP_LATCHED":
        return IncidentOutcome.ESTOP_LATCHED
    if terminal == "SAFE_STOP":
        # Distinguish controlled SAFE_STOP from a contradictory one.
        if any(c.contradictions for c in chains):
            return IncidentOutcome.INCONCLUSIVE
        return IncidentOutcome.SAFE_STOP_SUCCESS
    if terminal in {"ACTIVE_DEGRADED", "ACTIVE_RESTRICTED"}:
        return IncidentOutcome.CONTROLLED_DEGRADATION
    if terminal == "ACTIVE_NORMAL":
        # Did the run engage recovery? If so call it recovery_success.
        if bundle.scenario and bundle.scenario.evidence:
            recoveries = bundle.scenario.evidence.get("observed", {}).get(
                "recovery_engagement_count", 0
            )
            if recoveries:
                return IncidentOutcome.RECOVERY_SUCCESS
        return IncidentOutcome.CONTROLLED_DEGRADATION
    return IncidentOutcome.INCONCLUSIVE


def _derive_evidence_status(
    bundle: LoadedEvidenceBundle,
    timeline: IncidentTimeline,
    chains: list[CausalityChain],
) -> tuple[IncidentEvidenceStatus, tuple[str, ...], tuple[str, ...]]:
    missing: list[str] = []
    contradictions: list[str] = []

    # Track the kinds of evidence available.
    has_scenario_events = bool(bundle.scenario and bundle.scenario.events)
    has_scenario_files = bool(
        bundle.scenario and bundle.scenario.evidence is not None
    )
    has_runtime_files = bool(
        bundle.runtime and bundle.runtime.runtime_validation is not None
    )
    is_static_only = bool(bundle.runtime and bundle.runtime.is_static_only())

    # Aggregate the loader warnings into missing-evidence labels.
    for warning in bundle.all_warnings():
        if warning.category in {"missing_file", "missing_directory", "missing_run_dir"}:
            missing.append(warning.detail)
        elif warning.category in {"malformed_json", "schema_drift"}:
            contradictions.append(warning.detail)

    # Cross-check: scenario reports ok=true but command audit was
    # inconsistent with safety state.
    if bundle.scenario and bundle.scenario.evidence:
        scenario_status = bundle.scenario.evidence.get("status", "")
        if scenario_status == "passed":
            for chain in chains:
                contradictions.extend(chain.contradictions)

    contradictions = list(dict.fromkeys(contradictions))  # de-dupe preserving order
    missing = list(dict.fromkeys(missing))

    if contradictions:
        status = IncidentEvidenceStatus.INCONSISTENT
    elif not (has_scenario_files or has_runtime_files):
        status = IncidentEvidenceStatus.MISSING
    elif missing:
        status = IncidentEvidenceStatus.PARTIAL
    elif is_static_only and not has_scenario_events:
        status = IncidentEvidenceStatus.STATIC_ONLY
    elif has_scenario_events and has_runtime_files and not is_static_only:
        status = IncidentEvidenceStatus.LIVE_RUNTIME
    elif has_scenario_events:
        status = IncidentEvidenceStatus.COMPLETE
    elif has_runtime_files and is_static_only:
        status = IncidentEvidenceStatus.STATIC_ONLY
    else:
        status = IncidentEvidenceStatus.PARTIAL

    return status, tuple(missing), tuple(contradictions)


def _derive_cause(
    timeline: IncidentTimeline,
    chains: list[CausalityChain],
) -> Optional[IncidentCause]:
    if not chains:
        # Fall back to the first fault if we have one.
        for entry in timeline.entries:
            if entry.category == "fault_injection" and entry.event_type.startswith(
                "fault_injection."
            ):
                return IncidentCause(
                    label=f"fault: {entry.attributes.get('fault_type', 'unknown')}",
                    confidence=CausalityConfidence.WEAK,
                    rationale=(
                        "no causality chain assembled; first observed fault "
                        "entry adopted as the cause hypothesis"
                    ),
                )
        return None

    # Pick the chain with the highest overall confidence; tie-breaker
    # is the chain that has the most observed (non-inferred) links.
    order = {
        CausalityConfidence.DIRECT: 4,
        CausalityConfidence.STRONG: 3,
        CausalityConfidence.MODERATE: 2,
        CausalityConfidence.WEAK: 1,
        CausalityConfidence.INCONCLUSIVE: 0,
    }

    def _key(c: CausalityChain) -> tuple[int, int]:
        observed_links = sum(1 for l in c.links if not l.inferred)
        return (order[c.overall_confidence], observed_links)

    best = max(chains, key=_key)
    return IncidentCause(
        label=best.chain_id,
        confidence=best.overall_confidence,
        rationale=best.description,
    )
