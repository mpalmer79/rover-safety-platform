"""Incident index: enumerate retained incident bundles.

Each bundle directory under ``incidents/`` is expected to contain
``incident-report.json``. The index reads that file (when present),
projects the documented fields, and writes ``incidents/index.json``
plus ``docs/INCIDENT_INDEX.md``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional


@dataclass(frozen=True)
class IncidentIndexRow:
    incident_id: str
    run_id: Optional[str]
    scenario_id: Optional[str]
    severity: str
    outcome: str
    evidence_status: str
    first_fault: str
    terminal_safety_state: str
    replay_integrity_status: str
    created_at: str
    report_path: str
    notes: str = ""

    def as_dict(self) -> dict:
        return {
            "incident_id": self.incident_id,
            "run_id": self.run_id,
            "scenario_id": self.scenario_id,
            "severity": self.severity,
            "outcome": self.outcome,
            "evidence_status": self.evidence_status,
            "first_fault": self.first_fault,
            "terminal_safety_state": self.terminal_safety_state,
            "replay_integrity_status": self.replay_integrity_status,
            "created_at": self.created_at,
            "report_path": self.report_path,
            "notes": self.notes,
        }


@dataclass
class IncidentIndex:
    root: Path
    rows: list[IncidentIndexRow] = field(default_factory=list)

    def filter(
        self,
        *,
        severity: Optional[str] = None,
        outcome: Optional[str] = None,
        scenario_id: Optional[str] = None,
        evidence_status: Optional[str] = None,
        terminal_safety_state: Optional[str] = None,
    ) -> list[IncidentIndexRow]:
        out: list[IncidentIndexRow] = []
        for row in self.rows:
            if severity is not None and row.severity != severity:
                continue
            if outcome is not None and row.outcome != outcome:
                continue
            if scenario_id is not None and row.scenario_id != scenario_id:
                continue
            if evidence_status is not None and row.evidence_status != evidence_status:
                continue
            if (
                terminal_safety_state is not None
                and row.terminal_safety_state != terminal_safety_state
            ):
                continue
            out.append(row)
        return out

    def as_dict(self) -> dict:
        return {
            "root": str(self.root),
            "rows": [r.as_dict() for r in self.rows],
        }


def build_incident_index(*, incidents_root: Path) -> IncidentIndex:
    """Scan ``incidents_root`` and produce an index."""

    index = IncidentIndex(root=incidents_root)
    if not incidents_root.exists():
        return index
    for run_dir in sorted(p for p in incidents_root.iterdir() if p.is_dir()):
        if run_dir.name == "comparisons":
            continue
        report_path = run_dir / "incident-report.json"
        if not report_path.exists():
            index.rows.append(
                IncidentIndexRow(
                    incident_id=run_dir.name,
                    run_id=None,
                    scenario_id=None,
                    severity="unknown",
                    outcome="inconclusive",
                    evidence_status="missing",
                    first_fault="",
                    terminal_safety_state="",
                    replay_integrity_status="",
                    created_at="",
                    report_path="",
                    notes="incident-report.json missing",
                )
            )
            continue
        try:
            payload = json.loads(report_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            index.rows.append(
                IncidentIndexRow(
                    incident_id=run_dir.name,
                    run_id=None,
                    scenario_id=None,
                    severity="unknown",
                    outcome="inconclusive",
                    evidence_status="missing",
                    first_fault="",
                    terminal_safety_state="",
                    replay_integrity_status="",
                    created_at="",
                    report_path=str(report_path),
                    notes=f"incident-report.json did not parse: {exc}",
                )
            )
            continue

        timeline = payload.get("timeline") or {}
        entries = timeline.get("entries") or []

        first_fault = ""
        first_fault_idx = timeline.get("first_fault_index")
        if first_fault_idx is not None and first_fault_idx < len(entries):
            ff = entries[first_fault_idx]
            first_fault = (
                ff.get("attributes", {}).get("fault_type")
                or ff.get("event_type", "")
            )

        terminal_state = ""
        terminal_idx = timeline.get("terminal_index")
        if terminal_idx is not None and terminal_idx < len(entries):
            terminal_state = entries[terminal_idx].get("safety_state") or ""
        if not terminal_state:
            safety_states = payload.get("safety_states") or []
            if safety_states:
                terminal_state = safety_states[-1]

        replay_status = ""
        for entry in entries:
            if entry.get("event_type") == "replay.integrity_summary":
                replay_status = entry.get("attributes", {}).get("status", "")
                break

        index.rows.append(
            IncidentIndexRow(
                incident_id=payload.get("incident_id", run_dir.name),
                run_id=payload.get("run_id"),
                scenario_id=payload.get("scenario_id"),
                severity=payload.get("severity", "unknown"),
                outcome=payload.get("outcome", "inconclusive"),
                evidence_status=payload.get("evidence_status", "missing"),
                first_fault=first_fault,
                terminal_safety_state=terminal_state,
                replay_integrity_status=replay_status,
                created_at=payload.get("generated_at_utc", ""),
                report_path=str(report_path),
            )
        )
    return index


def write_incident_index(
    index: IncidentIndex,
    *,
    json_path: Optional[Path] = None,
    markdown_path: Optional[Path] = None,
) -> None:
    if json_path is not None:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(
            json.dumps(index.as_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
    if markdown_path is not None:
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(
            render_incident_index_md(index), encoding="utf-8"
        )


def render_incident_index_md(index: IncidentIndex) -> str:
    lines: list[str] = []
    lines.append("# Incident Index")
    lines.append("")
    lines.append(
        "_Generated by `rover_ws/tools/index_incidents.py`. Each row "
        "lists a retained incident bundle under `incidents/<incident_id>/`. "
        "The platform is **not safety-certified**; this index is "
        "engineering analysis material._"
    )
    lines.append("")
    lines.append(f"- **Incidents root:** `{index.root}`")
    lines.append(f"- **Bundles retained:** {len(index.rows)}")
    lines.append("")
    if not index.rows:
        lines.append("_No incident bundles retained yet._")
        lines.append("")
        return "\n".join(lines)
    lines.append(
        "| Incident | Scenario | Severity | Outcome | Evidence | Terminal | Replay | Generated |"
    )
    lines.append("|---|---|---|---|---|---|---|---|")
    for r in index.rows:
        lines.append(
            f"| `{r.incident_id}` | `{r.scenario_id or '-'}` | `{r.severity}` | "
            f"`{r.outcome}` | `{r.evidence_status}` | "
            f"`{r.terminal_safety_state or '-'}` | "
            f"`{r.replay_integrity_status or '-'}` | "
            f"{r.created_at or '-'} |"
        )
        if r.notes:
            lines.append(f"|   |   | _{r.notes}_ |   |   |   |   |   |")
    lines.append("")
    return "\n".join(lines)
