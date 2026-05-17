"""Evidence artefact generator.

Writes evidence/scenarios/<scenario_id>/ deterministically; never
modifies the scenario's run_dir. Re-running overwrites in place.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.verification.acceptance import AcceptanceStatus
from app.verification.command_audit import audit_command_path
from app.verification.replay_integrity import verify_replay_integrity
from app.verification.safety_audit import audit_safety_transitions
from app.verification.scenario_verifier import ScenarioVerification


@dataclass(frozen=True)
class EvidenceArtifact:
    path: Path
    kind: str
    """One of ``evidence.json``, ``evidence.md``, ``events-summary.md``,
    ``replay-integrity.json``, ``command-audit.json``,
    ``safety-transition-audit.json``."""


@dataclass
class ScenarioEvidence:
    scenario_id: str
    status: AcceptanceStatus
    artefacts: tuple[EvidenceArtifact, ...]
    summary: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "status": self.status.value,
            "summary": self.summary,
            "artefacts": [
                {"kind": a.kind, "path": str(a.path)} for a in self.artefacts
            ],
        }


def write_evidence(
    verification: ScenarioVerification,
    *,
    evidence_root: Path | str,
) -> ScenarioEvidence:
    """Materialise the evidence directory for one verification result."""

    evidence_root = Path(evidence_root)
    scenario_dir = evidence_root / "scenarios" / verification.expectation.scenario_id
    scenario_dir.mkdir(parents=True, exist_ok=True)

    artefacts: list[EvidenceArtifact] = []

    payload: dict[str, Any] = {
        "scenario_id": verification.expectation.scenario_id,
        "scenario_file": verification.expectation.scenario_file,
        "requirement_ids": list(verification.expectation.requirement_ids),
        "description": verification.expectation.description,
        "expected": {
            "safety_state": verification.expectation.expected_safety_state.value,
            "mission_state": verification.expectation.expected_mission_state,
            "required_event_types": list(verification.expectation.required_event_types),
            "forbidden_event_types": list(verification.expectation.forbidden_event_types),
            "expected_fired_faults": list(verification.expectation.expected_fired_faults),
            "min_recovery_engagements": verification.expectation.min_recovery_engagements,
            "expected_safe_stop_zero_motion": verification.expectation.expected_safe_stop_zero_motion,
        },
        "observed": {
            "final_safety_state": (
                verification.final_safety_state.value
                if verification.final_safety_state
                else None
            ),
            "final_mission_state": verification.final_mission_state,
            "fired_faults": list(verification.fired_faults),
            "recovery_engagement_count": verification.recovery_engagement_count,
            "run_dir": (
                str(verification.run_dir) if verification.run_dir else None
            ),
        },
        "status": verification.status.value,
        "checks": [c.as_dict() for c in verification.checks],
        "not_executed_reason": verification.not_executed_reason,
        "generated_at_utc": datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
    }
    evidence_json_path = scenario_dir / "evidence.json"
    evidence_json_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    artefacts.append(EvidenceArtifact(path=evidence_json_path, kind="evidence.json"))

    summary_md = _render_summary_md(verification, payload)
    evidence_md_path = scenario_dir / "evidence.md"
    evidence_md_path.write_text(summary_md, encoding="utf-8")
    artefacts.append(EvidenceArtifact(path=evidence_md_path, kind="evidence.md"))

    if verification.run_dir is not None and verification.run_dir.exists():
        events_md = _render_events_summary_md(verification.run_dir)
        events_md_path = scenario_dir / "events-summary.md"
        events_md_path.write_text(events_md, encoding="utf-8")
        artefacts.append(
            EvidenceArtifact(path=events_md_path, kind="events-summary.md")
        )

        replay_result = verify_replay_integrity(verification.run_dir)
        rp_path = scenario_dir / "replay-integrity.json"
        rp_path.write_text(
            json.dumps(replay_result.as_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        artefacts.append(EvidenceArtifact(path=rp_path, kind="replay-integrity.json"))

        cmd_result = audit_command_path(verification.run_dir)
        cmd_path = scenario_dir / "command-audit.json"
        cmd_path.write_text(
            json.dumps(cmd_result.as_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        artefacts.append(EvidenceArtifact(path=cmd_path, kind="command-audit.json"))

        safety_result = audit_safety_transitions(verification.run_dir)
        sa_path = scenario_dir / "safety-transition-audit.json"
        sa_path.write_text(
            json.dumps(safety_result.as_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        artefacts.append(
            EvidenceArtifact(path=sa_path, kind="safety-transition-audit.json")
        )

    summary = _short_summary(verification)
    return ScenarioEvidence(
        scenario_id=verification.expectation.scenario_id,
        status=verification.status,
        artefacts=tuple(artefacts),
        summary=summary,
    )


def _render_summary_md(verification: ScenarioVerification, payload: dict[str, Any]) -> str:
    exp = verification.expectation
    lines: list[str] = []
    lines.append(f"# Scenario evidence — `{exp.scenario_id}`")
    lines.append("")
    lines.append(f"- **Status:** `{verification.status.value}`")
    lines.append(f"- **Description:** {exp.description}")
    lines.append(f"- **Requirements covered:** {', '.join('`' + r + '`' for r in exp.requirement_ids) or '_none_'}")
    if verification.run_dir:
        lines.append(f"- **Run directory:** `{verification.run_dir}`")
    if verification.not_executed_reason:
        lines.append(f"- **Not executed reason:** {verification.not_executed_reason}")
    lines.append("")
    lines.append("## Expected vs observed")
    lines.append("")
    lines.append("| | Expected | Observed |")
    lines.append("|---|---|---|")
    lines.append(
        f"| Safety state | `{exp.expected_safety_state.value}` | "
        f"`{verification.final_safety_state.value if verification.final_safety_state else '-'}` |"
    )
    if exp.expected_mission_state is not None:
        lines.append(
            f"| Mission state | `{exp.expected_mission_state}` | "
            f"`{verification.final_mission_state or '-'}` |"
        )
    if exp.expected_fired_faults:
        lines.append(
            f"| Fired faults | {', '.join(f'`{f}`' for f in exp.expected_fired_faults)} | "
            f"{', '.join(f'`{f}`' for f in verification.fired_faults) or '_none_'} |"
        )
    if exp.min_recovery_engagements:
        lines.append(
            f"| Recovery engagements | ≥ {exp.min_recovery_engagements} | "
            f"{verification.recovery_engagement_count} |"
        )
    lines.append("")
    lines.append("## Checks")
    lines.append("")
    lines.append("| Check | Status | Detail |")
    lines.append("|---|---|---|")
    for check in verification.checks:
        lines.append(
            f"| `{check.name}` | `{check.status.value}` | {check.detail or '-'} |"
        )
        for err in check.errors:
            lines.append(f"|   _error_ |   | {err} |")
        for warn in check.warnings:
            lines.append(f"|   _warning_ |   | {warn} |")
    lines.append("")
    return "\n".join(lines)


def _render_events_summary_md(run_dir: Path) -> str:
    """Emit a flat Markdown listing of operationally significant events.

    The summary is intentionally narrow: it lists safety transitions,
    mission lifecycle entries, fault lifecycle, and watchdog
    expirations. Replay analysts use the canonical events.jsonl for
    full detail.
    """

    events_path = run_dir / "events.jsonl"
    if not events_path.exists():
        return f"# Events summary\n\n_events.jsonl missing in {run_dir}._\n"
    lines: list[str] = ["# Events summary", "", f"Source: `{events_path}`", ""]
    for label, prefix in (
        ("Safety transitions", "safety_transition."),
        ("Mission lifecycle", "mission_lifecycle."),
        ("Mission waypoint events", "mission_waypoint."),
        ("Mission recovery events", "mission_recovery."),
        ("World model events", "world_model."),
        ("Fault lifecycle", "fault_injection."),
        ("Watchdogs", "watchdog."),
    ):
        rows = _filter_events(events_path, prefix)
        lines.append(f"## {label}")
        if not rows:
            lines.append("_None._")
        else:
            for r in rows:
                lines.append(
                    f"- `t={r.get('sim_time_ns', 0)/1_000_000:.0f}ms` "
                    f"`{r.get('event_type', '?')}` "
                    f"reason `{r.get('reason_code', '-')}` "
                    f"safety=`{r.get('safety_state', '-')}` — "
                    f"{r.get('message', '')}"
                )
        lines.append("")
    return "\n".join(lines)


def _filter_events(events_path: Path, prefix: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    with events_path.open("r", encoding="utf-8") as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                continue
            event_type = payload.get("event_type", "")
            if event_type.startswith(prefix):
                out.append(payload)
    return out


def _short_summary(verification: ScenarioVerification) -> str:
    failed = [c for c in verification.checks if c.status == AcceptanceStatus.FAILED]
    if not failed:
        return f"{len(verification.checks)} checks passed"
    names = ", ".join(c.name for c in failed)
    return f"{len(failed)} check(s) failed: {names}"
