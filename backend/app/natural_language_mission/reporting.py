"""JSON, Markdown, and Mermaid renderers for a compiled mission plan.

The platform is **not safety-certified**.
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
from .replay_binding import ReplayBinding, build_replay_binding, to_dict as binding_to_dict


def plan_to_dict(plan: MissionPlan) -> dict:
    return {
        "plan_id": plan.plan_id,
        "compiler_version": plan.compiler_version,
        "odd_profile_id": plan.odd_profile_id,
        "original_intent": plan.original_intent,
        "normalized_intent": plan.normalized_intent,
        "status": plan.status,
        "objectives": [
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
        "graph": {
            "nodes": [
                {
                    "node_id": n.node_id,
                    "label": n.label,
                    "stage_kind": n.stage_kind,
                    "objective_id": n.objective_id,
                    "branch": n.branch,
                }
                for n in plan.graph.nodes
            ],
            "edges": [
                {"source": e.source, "target": e.target, "condition": e.condition}
                for e in plan.graph.edges
            ],
        },
        "risk": {
            "band": plan.risk.band,
            "score": plan.risk.score,
            "drivers": list(plan.risk.drivers),
            "mitigations": list(plan.risk.mitigations),
            "required_reviewer_actions": list(plan.risk.required_reviewer_actions),
        },
        "diagnostics": to_dicts(plan.diagnostics),
        "compile_hash": plan.compile_hash,
        "generated_at_utc": plan.generated_at_utc,
        "extracted_clauses": [
            {
                "raw": c.raw,
                "normalized": c.normalized,
                "template_id": c.template_id,
                "slots": dict(c.slots),
            }
            for c in plan.extracted_clauses
        ],
        "rejected_clauses": list(plan.rejected_clauses),
        "assumptions": list(plan.assumptions),
        "explainability_chain": list(plan.explainability_chain),
        "replay_binding_id": plan.replay_binding_id,
        "disclaimer": NON_CERTIFICATION_DISCLAIMER,
    }


def render_plan_markdown(plan: MissionPlan) -> str:
    lines = [
        "# Compiled Mission Plan",
        "",
        f"_{NON_CERTIFICATION_DISCLAIMER}_",
        "",
        f"- **plan_id:** `{plan.plan_id}`",
        f"- **status:** `{plan.status}`",
        f"- **compile_hash:** `{plan.compile_hash}`",
        f"- **compiler_version:** `{plan.compiler_version}`",
        f"- **odd_profile_id:** `{plan.odd_profile_id}`",
        f"- **generated (UTC):** `{plan.generated_at_utc}`",
        f"- **replay_binding_id:** `{plan.replay_binding_id}`",
        "",
        "## Intent",
        "",
        f"> Original: {plan.original_intent}",
        "",
        f"> Normalised: {plan.normalized_intent}",
        "",
    ]

    lines.append("## Objectives")
    lines.append("")
    if plan.objectives:
        for o in plan.objectives:
            param_repr = ", ".join(f"{k}=`{v}`" for k, v in sorted(o.parameters.items()))
            lines.append(f"- **{o.objective_id}** ({o.objective_kind}): {o.label}  ")
            lines.append(f"  - parameters: {param_repr or '(none)'}  ")
            lines.append(f"  - source clause: `{o.source_clause}`")
    else:
        lines.append("- (no objectives compiled)")
    lines.append("")

    lines.append("## Constraints")
    lines.append("")
    if plan.constraints:
        for c in plan.constraints:
            param_repr = ", ".join(f"{k}=`{v}`" for k, v in sorted(c.parameters.items()))
            lines.append(f"- **{c.constraint_id}** ({c.constraint_kind}): {c.label}  ")
            lines.append(f"  - parameters: {param_repr or '(none)'}  ")
            lines.append(f"  - source clause: `{c.source_clause}`")
    else:
        lines.append("- (no constraints compiled)")
    lines.append("")

    lines.append("## Risk")
    lines.append("")
    lines.append(f"- band: `{plan.risk.band}`")
    lines.append(f"- score: `{plan.risk.score}`")
    if plan.risk.drivers:
        lines.append("- drivers:")
        for d in plan.risk.drivers:
            lines.append(f"  - `{d}`")
    if plan.risk.mitigations:
        lines.append("- mitigations:")
        for m in plan.risk.mitigations:
            lines.append(f"  - {m}")
    if plan.risk.required_reviewer_actions:
        lines.append("- required reviewer actions:")
        for a in plan.risk.required_reviewer_actions:
            lines.append(f"  - {a}")
    lines.append("")

    if plan.diagnostics:
        lines.append("## Diagnostics")
        lines.append("")
        for d in plan.diagnostics:
            lines.append(f"- `[{d.severity}/{d.code}]` {d.message}")
            if d.clause:
                lines.append(f"  - clause: `{d.clause}`")
            if d.field:
                lines.append(f"  - field: `{d.field}`")
        lines.append("")

    if plan.rejected_clauses:
        lines.append("## Rejected clauses")
        lines.append("")
        for r in plan.rejected_clauses:
            lines.append(f"- `{r}`")
        lines.append("")

    lines.append("## Mission graph (Mermaid)")
    lines.append("")
    lines.append("```mermaid")
    lines.append(render_plan_mermaid(plan))
    lines.append("```")
    lines.append("")

    if plan.explainability_chain:
        lines.append("## Explainability chain")
        lines.append("")
        for line in plan.explainability_chain:
            lines.append(f"- {line}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def render_plan_mermaid(plan: MissionPlan) -> str:
    """Deterministic Mermaid rendering of the mission graph."""

    out: list[str] = ["flowchart TD"]
    for node in plan.graph.nodes:
        safe_id = node.node_id.replace("-", "_")
        label = node.label.replace('"', "'")
        out.append(f'    {safe_id}["{label}"]')
    for edge in plan.graph.edges:
        src = edge.source.replace("-", "_")
        tgt = edge.target.replace("-", "_")
        if edge.condition:
            cond = edge.condition.replace('"', "'")
            out.append(f'    {src} -->|"{cond}"| {tgt}')
        else:
            out.append(f"    {src} --> {tgt}")
    return "\n".join(out)


def write_plan(plan: MissionPlan, *, json_path: Path, md_path: Path) -> None:
    Path(json_path).write_text(
        json.dumps(plan_to_dict(plan), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    Path(md_path).write_text(render_plan_markdown(plan), encoding="utf-8")


def write_replay_binding(plan: MissionPlan, json_path: Path) -> ReplayBinding:
    binding = build_replay_binding(plan)
    Path(json_path).write_text(
        json.dumps(binding_to_dict(binding), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return binding


__all__ = [
    "plan_to_dict",
    "render_plan_markdown",
    "render_plan_mermaid",
    "write_plan",
    "write_replay_binding",
]
