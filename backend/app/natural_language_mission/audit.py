"""Mission compile audit artefact (JSON + Markdown).

The platform is **not safety-certified**. The audit artefact is a
read-only record of one compile run; nothing in this module mutates
the compiled plan.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .diagnostics import to_dicts
from .models import (
    NON_CERTIFICATION_DISCLAIMER,
    MissionPlan,
)


def build_audit(plan: MissionPlan) -> dict:
    return {
        "plan_id": plan.plan_id,
        "compiler_version": plan.compiler_version,
        "compile_hash": plan.compile_hash,
        "generated_at_utc": plan.generated_at_utc,
        "odd_profile_id": plan.odd_profile_id,
        "original_intent": plan.original_intent,
        "normalized_intent": plan.normalized_intent,
        "status": plan.status,
        "extracted_objectives": [
            {
                "objective_id": o.objective_id,
                "objective_kind": o.objective_kind,
                "label": o.label,
                "parameters": dict(o.parameters),
                "source_clause": o.source_clause,
            }
            for o in plan.objectives
        ],
        "constraints": [
            {
                "constraint_id": c.constraint_id,
                "constraint_kind": c.constraint_kind,
                "label": c.label,
                "parameters": dict(c.parameters),
                "source_clause": c.source_clause,
            }
            for c in plan.constraints
        ],
        "rejected_instructions": list(plan.rejected_clauses),
        "validation_diagnostics": to_dicts(plan.diagnostics),
        "assumptions": list(plan.assumptions),
        "risk": {
            "band": plan.risk.band,
            "score": plan.risk.score,
            "drivers": list(plan.risk.drivers),
            "mitigations": list(plan.risk.mitigations),
            "required_reviewer_actions": list(plan.risk.required_reviewer_actions),
        },
        "replay_binding_id": plan.replay_binding_id,
        "replay_compatibility": {
            "runtime_executed": False,
            "binding_id": plan.replay_binding_id,
        },
        "disclaimer": NON_CERTIFICATION_DISCLAIMER,
    }


def render_audit_markdown(plan: MissionPlan) -> str:
    audit = build_audit(plan)
    lines = [
        "# Mission Compile Audit",
        "",
        f"_{NON_CERTIFICATION_DISCLAIMER}_",
        "",
        f"- **plan_id:** `{plan.plan_id}`",
        f"- **compile_hash:** `{plan.compile_hash}`",
        f"- **compiler_version:** `{plan.compiler_version}`",
        f"- **odd_profile_id:** `{plan.odd_profile_id}`",
        f"- **status:** `{plan.status}`",
        f"- **generated (UTC):** `{plan.generated_at_utc}`",
        "",
        "## Original intent",
        "",
        f"> {plan.original_intent}",
        "",
        "## Normalised intent",
        "",
        f"> {plan.normalized_intent}",
        "",
        f"## Risk: `{plan.risk.band}` (score `{plan.risk.score}`)",
        "",
    ]
    if plan.risk.drivers:
        for d in plan.risk.drivers:
            lines.append(f"- driver: `{d}`")
        lines.append("")
    if plan.rejected_clauses:
        lines.append("## Rejected instructions")
        lines.append("")
        for r in plan.rejected_clauses:
            lines.append(f"- `{r}`")
        lines.append("")
    if plan.diagnostics:
        lines.append("## Validation diagnostics")
        lines.append("")
        for d in plan.diagnostics:
            lines.append(f"- `[{d.severity}/{d.code}]` {d.message}")
        lines.append("")
    lines.append("## Replay compatibility")
    lines.append("")
    lines.append(f"- runtime_executed: `false`")
    lines.append(f"- binding_id: `{plan.replay_binding_id}`")
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_audit(plan: MissionPlan, *, json_path: Path, md_path: Path) -> dict:
    audit = build_audit(plan)
    Path(json_path).write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    Path(md_path).write_text(render_audit_markdown(plan), encoding="utf-8")
    return audit


__all__ = [
    "build_audit",
    "render_audit_markdown",
    "write_audit",
]
