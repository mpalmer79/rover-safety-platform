"""Convert heterogeneous evidence records into canonical timeline entries.

The normaliser reads:

* ``events.jsonl`` from the underlying ``runs/<run_id>/`` directory
  (the gold source),
* ``safety-transition-audit.json`` and ``command-audit.json``
  (scenario-level summaries),
* ``runtime-validation.json``, ``regression-report.json``, and
  ``host-qualification.json`` (runtime-level qualification results),

and emits :class:`TimelineEntry` instances. It never invents a
record: when an evidence source is missing, the normaliser emits no
entries from that source and the loader's warnings carry the gap.
"""

from __future__ import annotations

from typing import Iterable, Optional

from app.incident_analysis.loader import (
    LoadedEvidenceBundle,
    LoadedRuntimeEvidence,
    LoadedScenarioEvidence,
)
from app.incident_analysis.models import (
    EvidenceOrigin,
    TimelineEntry,
)


_EVENT_CATEGORY_BY_TYPE_PREFIX: tuple[tuple[str, str], ...] = (
    ("safety_transition", "safety_transition"),
    ("fault_injection", "fault_injection"),
    ("motion_arbitration", "motion_arbitration"),
    ("watchdog", "watchdog"),
    ("sensor_health", "sensor_health"),
    ("system_lifecycle", "system_lifecycle"),
    ("mission", "mission_transition"),
    ("waypoint", "mission_transition"),
    ("recovery", "recovery"),
    ("world_model", "world_model"),
    ("operator", "operator_action"),
    ("replay", "replay"),
    ("diagnostic", "diagnostic_health"),
)


def normalise_bundle(
    bundle: LoadedEvidenceBundle,
) -> list[TimelineEntry]:
    """Produce timeline entries for the entire bundle (un-ordered)."""

    entries: list[TimelineEntry] = []
    if bundle.scenario is not None:
        entries.extend(_entries_from_scenario(bundle.scenario))
    if bundle.runtime is not None:
        entries.extend(_entries_from_runtime(bundle.runtime))
    return entries


# ---------------------------------------------------------------------------
# Scenario-side normalisation.
# ---------------------------------------------------------------------------


def _entries_from_scenario(scenario: LoadedScenarioEvidence) -> list[TimelineEntry]:
    entries: list[TimelineEntry] = []
    sid = scenario.scenario_id
    run_id = (
        scenario.evidence.get("observed", {}).get("run_dir", "").rsplit("/", 1)[-1]
        if scenario.evidence
        else None
    ) or None

    # 1. Per-event entries from events.jsonl (the gold source).
    for event in scenario.events:
        entries.append(
            _normalise_event_record(
                record=event,
                source_file="events.jsonl",
                origin=EvidenceOrigin.SCENARIO_EVIDENCE,
                run_id=run_id,
                scenario_id=sid,
            )
        )

    # 2. If events.jsonl is missing, fall back to safety-transition-audit.
    if not scenario.events and scenario.safety_transition_audit:
        for index, transition in enumerate(
            scenario.safety_transition_audit.get("transitions", [])
        ):
            from_state, to_state, reason = (
                transition[0],
                transition[1],
                transition[2] if len(transition) > 2 else "",
            )
            entries.append(
                TimelineEntry(
                    sequence_index=-1,
                    timestamp="",
                    relative_time_ms=None,
                    sim_time_ns=None,
                    source_file="safety-transition-audit.json",
                    category="safety_transition",
                    event_type="safety_transition.entered",
                    severity="INFO",
                    safety_state=to_state,
                    mission_state=None,
                    reason_code=reason or None,
                    message=f"{from_state} -> {to_state}: {reason}",
                    evidence_origin=EvidenceOrigin.SCENARIO_EVIDENCE,
                    run_id=run_id,
                    scenario_id=sid,
                    raw_reference=f"transitions[{index}]",
                    attributes={
                        "from_state": from_state,
                        "to_state": to_state,
                        "reason": reason,
                    },
                )
            )

    # 3. Command-audit summary as a single rolled-up entry.
    if scenario.command_audit:
        ca = scenario.command_audit
        entries.append(
            TimelineEntry(
                sequence_index=-1,
                timestamp="",
                relative_time_ms=None,
                sim_time_ns=None,
                source_file="command-audit.json",
                category="motion_arbitration",
                event_type="motion_arbitration.summary",
                severity="INFO" if ca.get("ok", False) else "WARN",
                safety_state=None,
                mission_state=None,
                reason_code="command_audit_summary",
                message=(
                    f"command audit: requests={ca.get('request_count', 0)} "
                    f"commands={ca.get('command_count', 0)} "
                    f"clamped={ca.get('clamped_count', 0)} "
                    f"zeroed={ca.get('zeroed_count', 0)} "
                    f"rejected={ca.get('rejected_count', 0)}"
                ),
                evidence_origin=EvidenceOrigin.SCENARIO_EVIDENCE,
                run_id=run_id,
                scenario_id=sid,
                raw_reference="command-audit.json",
                attributes={
                    k: ca.get(k)
                    for k in (
                        "request_count",
                        "command_count",
                        "clamped_count",
                        "zeroed_count",
                        "rejected_count",
                        "expired_count",
                        "ok",
                        "status",
                    )
                },
            )
        )

    # 4. Replay-integrity summary.
    if scenario.replay_integrity:
        ri = scenario.replay_integrity
        entries.append(
            TimelineEntry(
                sequence_index=-1,
                timestamp="",
                relative_time_ms=None,
                sim_time_ns=None,
                source_file="replay-integrity.json",
                category="replay",
                event_type="replay.integrity_summary",
                severity="INFO" if ri.get("ok", False) else "WARN",
                safety_state=None,
                mission_state=ri.get("final_mission_state"),
                reason_code="replay_integrity_summary",
                message=(
                    f"replay integrity status={ri.get('status', 'unknown')} "
                    f"events={ri.get('event_count', 0)} "
                    f"transitions={ri.get('transition_count', 0)} "
                    f"waypoints={len(ri.get('waypoints_completed', []))}"
                ),
                evidence_origin=EvidenceOrigin.SCENARIO_EVIDENCE,
                run_id=run_id,
                scenario_id=sid,
                raw_reference="replay-integrity.json",
                attributes={
                    "status": ri.get("status"),
                    "ok": ri.get("ok"),
                    "event_count": ri.get("event_count"),
                    "transition_count": ri.get("transition_count"),
                },
            )
        )

    return entries


def _normalise_event_record(
    *,
    record: dict,
    source_file: str,
    origin: EvidenceOrigin,
    run_id: Optional[str],
    scenario_id: Optional[str],
) -> TimelineEntry:
    """Convert a single events.jsonl record into a TimelineEntry."""

    event_type = str(record.get("event_type", ""))
    category = _category_for(event_type)
    sim_time_ns_raw = record.get("sim_time_ns")
    sim_time_ns: Optional[int] = (
        int(sim_time_ns_raw) if isinstance(sim_time_ns_raw, (int, float)) else None
    )
    return TimelineEntry(
        sequence_index=-1,
        timestamp=str(record.get("timestamp", "")),
        relative_time_ms=None,
        sim_time_ns=sim_time_ns,
        source_file=source_file,
        category=category,
        event_type=event_type,
        severity=str(record.get("severity", "INFO")),
        safety_state=record.get("safety_state"),
        mission_state=_extract_mission_state(record),
        reason_code=record.get("reason_code"),
        message=str(record.get("message", "")),
        evidence_origin=origin,
        run_id=run_id or record.get("run_id"),
        scenario_id=scenario_id or record.get("scenario_id"),
        raw_reference=str(record.get("event_id") or ""),
        attributes=dict(record.get("attributes", {}) or {}),
    )


def _extract_mission_state(record: dict) -> Optional[str]:
    attrs = record.get("attributes", {}) or {}
    for key in ("mission_state", "to_state", "state", "lifecycle_state"):
        if key in attrs and isinstance(attrs[key], str):
            return attrs[key]
    if "lifecycle_state" in record and isinstance(record["lifecycle_state"], str):
        return record["lifecycle_state"]
    return None


def _category_for(event_type: str) -> str:
    for prefix, category in _EVENT_CATEGORY_BY_TYPE_PREFIX:
        if event_type.startswith(prefix):
            return category
    return "unknown"


# ---------------------------------------------------------------------------
# Runtime-side normalisation.
# ---------------------------------------------------------------------------


def _entries_from_runtime(runtime: LoadedRuntimeEvidence) -> list[TimelineEntry]:
    entries: list[TimelineEntry] = []
    rid = runtime.run_id

    if runtime.runtime_validation:
        rv = runtime.runtime_validation
        for index, check in enumerate(rv.get("checks", [])):
            entries.append(
                TimelineEntry(
                    sequence_index=-1,
                    timestamp=rv.get("generated_at_utc", ""),
                    relative_time_ms=None,
                    sim_time_ns=None,
                    source_file="runtime-validation.json",
                    category="runtime_validation",
                    event_type=f"runtime_validation.check[{check.get('name', '?')}]",
                    severity=_severity_for_status(check.get("status", "")),
                    safety_state=None,
                    mission_state=None,
                    reason_code=check.get("reason") or None,
                    message=check.get("detail", ""),
                    evidence_origin=EvidenceOrigin.RUNTIME_EVIDENCE,
                    run_id=rid,
                    scenario_id=None,
                    raw_reference=f"checks[{index}]",
                    attributes={
                        "status": check.get("status"),
                        "errors": list(check.get("errors", [])),
                        "warnings": list(check.get("warnings", [])),
                    },
                )
            )

    if runtime.regression_report:
        rr = runtime.regression_report
        for index, finding in enumerate(rr.get("findings", [])):
            entries.append(
                TimelineEntry(
                    sequence_index=-1,
                    timestamp="",
                    relative_time_ms=None,
                    sim_time_ns=None,
                    source_file="regression-report.json",
                    category="regression",
                    event_type=f"regression.{finding.get('name', 'finding')}",
                    severity=_severity_for_severity_label(
                        finding.get("severity", "")
                    ),
                    safety_state=None,
                    mission_state=None,
                    reason_code="regression_finding",
                    message=finding.get("detail", ""),
                    evidence_origin=EvidenceOrigin.RUNTIME_EVIDENCE,
                    run_id=rid,
                    scenario_id=None,
                    raw_reference=f"findings[{index}]",
                    attributes={
                        "severity": finding.get("severity"),
                        "evidence_paths": list(finding.get("evidence_paths", [])),
                    },
                )
            )

    if runtime.host_qualification:
        hq = runtime.host_qualification
        for index, check in enumerate(hq.get("checks", [])):
            entries.append(
                TimelineEntry(
                    sequence_index=-1,
                    timestamp=hq.get("generated_at_utc", ""),
                    relative_time_ms=None,
                    sim_time_ns=None,
                    source_file="host-qualification.json",
                    category="qualification",
                    event_type=f"host_qualification.{check.get('name', 'check')}",
                    severity=_severity_for_status(check.get("status", "")),
                    safety_state=None,
                    mission_state=None,
                    reason_code=check.get("reason") or None,
                    message=check.get("detail", ""),
                    evidence_origin=EvidenceOrigin.RUNTIME_EVIDENCE,
                    run_id=rid,
                    scenario_id=None,
                    raw_reference=f"checks[{index}]",
                    attributes={"status": check.get("status")},
                )
            )

    return entries


def _severity_for_status(status: str) -> str:
    return {
        "passed": "INFO",
        "skipped": "INFO",
        "not_executed": "INFO",
        "partial": "WARN",
        "failed": "ERROR",
    }.get(status, "INFO")


def _severity_for_severity_label(label: str) -> str:
    return {
        "expected_difference": "INFO",
        "warning": "WARN",
        "regression": "ERROR",
        "critical_regression": "CRITICAL",
    }.get(label, "INFO")
