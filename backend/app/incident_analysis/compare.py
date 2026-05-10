"""Cross-incident comparison.

Reads two or more incident bundles (each containing
``incident-report.json``) and emits a structured comparison
suitable for review:

* terminal outcome side-by-side
* severity / evidence_status side-by-side
* safety response latency (first_fault to first SAFE_STOP)
* fault-to-transition chain summary
* command intervention summary
* replay completeness summary
* regression status
* cause label and causality confidence

The comparator is read-only and never invents data; missing fields
appear as ``-`` in the rendered Markdown.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional


@dataclass
class IncidentComparisonRow:
    incident_id: str
    run_id: Optional[str]
    scenario_id: Optional[str]
    severity: str
    outcome: str
    evidence_status: str
    cause_label: str
    cause_confidence: str
    safety_response_latency_ms: Optional[int]
    fault_count: int
    safety_transition_count: int
    command_audit_zeroed: int
    command_audit_clamped: int
    command_audit_rejected: int
    replay_status: str
    regression_count: int
    contradictions: int
    missing_evidence: int

    def as_dict(self) -> dict:
        return {
            "incident_id": self.incident_id,
            "run_id": self.run_id,
            "scenario_id": self.scenario_id,
            "severity": self.severity,
            "outcome": self.outcome,
            "evidence_status": self.evidence_status,
            "cause_label": self.cause_label,
            "cause_confidence": self.cause_confidence,
            "safety_response_latency_ms": self.safety_response_latency_ms,
            "fault_count": self.fault_count,
            "safety_transition_count": self.safety_transition_count,
            "command_audit_zeroed": self.command_audit_zeroed,
            "command_audit_clamped": self.command_audit_clamped,
            "command_audit_rejected": self.command_audit_rejected,
            "replay_status": self.replay_status,
            "regression_count": self.regression_count,
            "contradictions": self.contradictions,
            "missing_evidence": self.missing_evidence,
        }


@dataclass
class IncidentComparison:
    comparison_id: str
    rows: list[IncidentComparisonRow] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "comparison_id": self.comparison_id,
            "rows": [r.as_dict() for r in self.rows],
        }


def compare_incidents(
    *,
    bundle_dirs: Iterable[Path],
    comparison_id: str,
) -> IncidentComparison:
    comp = IncidentComparison(comparison_id=comparison_id)
    for bundle_dir in bundle_dirs:
        report = bundle_dir / "incident-report.json"
        if not report.exists():
            comp.rows.append(
                IncidentComparisonRow(
                    incident_id=bundle_dir.name,
                    run_id=None,
                    scenario_id=None,
                    severity="unknown",
                    outcome="inconclusive",
                    evidence_status="missing",
                    cause_label="-",
                    cause_confidence="inconclusive",
                    safety_response_latency_ms=None,
                    fault_count=0,
                    safety_transition_count=0,
                    command_audit_zeroed=0,
                    command_audit_clamped=0,
                    command_audit_rejected=0,
                    replay_status="-",
                    regression_count=0,
                    contradictions=0,
                    missing_evidence=0,
                )
            )
            continue
        try:
            payload = json.loads(report.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        comp.rows.append(_row_from_payload(payload, bundle_dir))
    return comp


def _row_from_payload(
    payload: dict, bundle_dir: Path
) -> IncidentComparisonRow:
    timeline = payload.get("timeline") or {}
    entries = timeline.get("entries") or []

    cause = payload.get("cause") or {}

    # Safety response latency: first fault -> first SAFE_STOP transition.
    fault_idx = timeline.get("first_fault_index")
    safe_stop_entry = None
    for entry in entries:
        if entry.get("safety_state") == "SAFE_STOP":
            safe_stop_entry = entry
            break
    latency: Optional[int] = None
    if (
        fault_idx is not None
        and fault_idx < len(entries)
        and safe_stop_entry is not None
        and entries[fault_idx].get("relative_time_ms") is not None
        and safe_stop_entry.get("relative_time_ms") is not None
    ):
        latency = int(safe_stop_entry["relative_time_ms"]) - int(
            entries[fault_idx]["relative_time_ms"]
        )

    fault_count = sum(
        1
        for e in entries
        if e.get("category") == "fault_injection"
        and e.get("event_type", "").startswith("fault_injection.")
    )
    transition_count = sum(
        1 for e in entries if e.get("category") == "safety_transition"
    )

    cmd_zero = cmd_clamped = cmd_rej = 0
    replay_status = ""
    for entry in entries:
        if entry.get("event_type") == "motion_arbitration.summary":
            attrs = entry.get("attributes", {}) or {}
            cmd_zero = int(attrs.get("zeroed_count", 0) or 0)
            cmd_clamped = int(attrs.get("clamped_count", 0) or 0)
            cmd_rej = int(attrs.get("rejected_count", 0) or 0)
        if entry.get("event_type") == "replay.integrity_summary":
            replay_status = entry.get("attributes", {}).get("status", "")

    regression_count = sum(
        1 for e in entries if e.get("category") == "regression"
    )

    return IncidentComparisonRow(
        incident_id=payload.get("incident_id", bundle_dir.name),
        run_id=payload.get("run_id"),
        scenario_id=payload.get("scenario_id"),
        severity=payload.get("severity", "unknown"),
        outcome=payload.get("outcome", "inconclusive"),
        evidence_status=payload.get("evidence_status", "missing"),
        cause_label=cause.get("label", "-") if cause else "-",
        cause_confidence=cause.get("confidence", "inconclusive") if cause else "inconclusive",
        safety_response_latency_ms=latency,
        fault_count=fault_count,
        safety_transition_count=transition_count,
        command_audit_zeroed=cmd_zero,
        command_audit_clamped=cmd_clamped,
        command_audit_rejected=cmd_rej,
        replay_status=replay_status,
        regression_count=regression_count,
        contradictions=len(payload.get("contradictions") or []),
        missing_evidence=len(payload.get("missing_evidence") or []),
    )


def render_comparison_md(comparison: IncidentComparison) -> str:
    lines: list[str] = []
    lines.append(f"# Incident Comparison — `{comparison.comparison_id}`")
    lines.append("")
    lines.append(
        "_Generated by `rover_ws/tools/compare_incidents.py`. The "
        "platform is **not safety-certified**; this comparison is "
        "engineering analysis material._"
    )
    lines.append("")
    if not comparison.rows:
        lines.append("_No bundles supplied._")
        return "\n".join(lines) + "\n"
    lines.append(
        "| Incident | Scenario | Severity | Outcome | Evidence | "
        "Cause | Confidence | Safety latency (ms) | "
        "Faults | Transitions | Zeroed | Clamped | Rejected | "
        "Replay | Regressions | Contradictions | Missing |"
    )
    lines.append(
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"
    )
    for r in comparison.rows:
        latency = "-" if r.safety_response_latency_ms is None else str(
            r.safety_response_latency_ms
        )
        lines.append(
            f"| `{r.incident_id}` | `{r.scenario_id or '-'}` | "
            f"`{r.severity}` | `{r.outcome}` | `{r.evidence_status}` | "
            f"`{r.cause_label}` | `{r.cause_confidence}` | {latency} | "
            f"{r.fault_count} | {r.safety_transition_count} | "
            f"{r.command_audit_zeroed} | {r.command_audit_clamped} | "
            f"{r.command_audit_rejected} | "
            f"`{r.replay_status or '-'}` | {r.regression_count} | "
            f"{r.contradictions} | {r.missing_evidence} |"
        )
    lines.append("")
    return "\n".join(lines)
