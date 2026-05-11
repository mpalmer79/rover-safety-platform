"""Render the reviewer-facing explainability chain.

The platform is **not safety-certified**. The chain shows each
deterministic stage so a reviewer can verify how user input became
the final compiled plan.
"""

from __future__ import annotations

from .models import (
    Diagnostic,
    ExtractedClause,
    MissionConstraint,
    MissionObjective,
    MissionRisk,
)


def build_chain(
    *,
    original_intent: str,
    normalized_intent: str,
    clauses: tuple[ExtractedClause, ...],
    rejected: tuple[str, ...],
    objectives: tuple[MissionObjective, ...],
    constraints: tuple[MissionConstraint, ...],
    diagnostics: tuple[Diagnostic, ...],
    risk: MissionRisk,
    final_status: str,
) -> tuple[str, ...]:
    """Build the explainability chain as a tuple of human-readable lines."""

    lines: list[str] = []
    lines.append(f"USER INPUT: {original_intent}")
    lines.append(f"NORMALIZED INPUT: {normalized_intent}")
    if clauses:
        lines.append("EXTRACTED CLAUSES:")
        for c in clauses:
            slot_repr = ", ".join(f"{k}={v}" for k, v in sorted(c.slots.items())) or "(no slots)"
            lines.append(f"  - [{c.template_id}] {c.raw} :: {slot_repr}")
    else:
        lines.append("EXTRACTED CLAUSES: (none accepted)")
    if rejected:
        lines.append("REJECTED CLAUSES:")
        for r in rejected:
            lines.append(f"  - {r}")
    if objectives:
        lines.append("NORMALIZED OBJECTIVES:")
        for o in objectives:
            lines.append(f"  - {o.objective_id} {o.objective_kind} :: {o.label}")
    if constraints:
        lines.append("NORMALIZED CONSTRAINTS:")
        for c in constraints:
            lines.append(f"  - {c.constraint_id} {c.constraint_kind} :: {c.label}")
    if diagnostics:
        lines.append("VALIDATION DIAGNOSTICS:")
        for d in diagnostics:
            lines.append(f"  - [{d.severity}/{d.code}] {d.message}")
    else:
        lines.append("VALIDATION DIAGNOSTICS: (none)")
    lines.append(
        f"RISK CLASSIFICATION: band={risk.band} score={risk.score} drivers={list(risk.drivers)}"
    )
    lines.append(f"FINAL COMPILED PLAN STATUS: {final_status}")
    return tuple(lines)


def render_markdown(chain: tuple[str, ...]) -> str:
    body = "\n".join(f"- {line}" for line in chain)
    return body + ("\n" if body else "")


__all__ = [
    "build_chain",
    "render_markdown",
]
