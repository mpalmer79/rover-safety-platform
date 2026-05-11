"""Top-level mission-intent compiler.

The platform is **not safety-certified**. The compiler is a
deterministic, offline translation pipeline:

    natural language input
      -> parser.parse_intent
      -> objectives + constraints (constraints.py)
      -> validator.validate_all
      -> risk.classify_risk
      -> deterministic mission graph
      -> reporting + explainability + replay binding
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from typing import Mapping

from .constraints import (
    build_constraint_from_clause,
    build_objective_from_clause,
    detect_contradictions,
)
from .diagnostics import has_rejection, has_warning, merge
from .explainability import build_chain
from .models import (
    COMPILER_VERSION,
    COMPILE_STATUS_AMBIGUOUS,
    COMPILE_STATUS_OK,
    COMPILE_STATUS_OK_WITH_WARNINGS,
    COMPILE_STATUS_REJECTED,
    Diagnostic,
    MissionConstraint,
    MissionGraph,
    MissionGraphEdge,
    MissionGraphNode,
    MissionObjective,
    MissionPlan,
    OperationalDesignDomain,
    SEVERITY_REJECTION,
    SEVERITY_WARNING,
    STAGE_DOCK_RETURN,
    STAGE_TERMINATE,
)
from .odd import DEFAULT_ODD_PROFILE_ID, get_profile
from .parser import parse_intent
from .replay_binding import build_replay_binding
from .risk import classify_risk
from .validator import validate_all


def _build_graph(
    objectives: tuple[MissionObjective, ...],
    constraints: tuple[MissionConstraint, ...],
) -> MissionGraph:
    nodes: list[MissionGraphNode] = []
    edges: list[MissionGraphEdge] = []

    start = MissionGraphNode(
        node_id="start", label="Mission start", stage_kind="start"
    )
    end = MissionGraphNode(
        node_id="end", label="Mission end", stage_kind="end"
    )
    nodes.append(start)
    prev_id = start.node_id

    for idx, obj in enumerate(objectives, start=1):
        node = MissionGraphNode(
            node_id=f"n-{idx:02d}",
            label=obj.label,
            stage_kind=obj.objective_kind,
            objective_id=obj.objective_id,
        )
        nodes.append(node)
        edges.append(MissionGraphEdge(source=prev_id, target=node.node_id))
        prev_id = node.node_id

    nodes.append(end)
    edges.append(MissionGraphEdge(source=prev_id, target=end.node_id))

    # Recovery / abort branches: dock_return on safety triggers.
    has_safety_trigger = any(c.constraint_kind == "safety_trigger" for c in constraints)
    has_recovery = any(c.constraint_kind == "recovery_directive" for c in constraints)
    has_dock_return = any(o.objective_kind == STAGE_DOCK_RETURN for o in objectives)
    if has_safety_trigger and not has_dock_return:
        dock_node = MissionGraphNode(
            node_id="recovery_dock",
            label="Recovery: return to dock",
            stage_kind=STAGE_DOCK_RETURN,
            branch="recovery",
        )
        nodes.append(dock_node)
        for n in nodes:
            if n.stage_kind not in ("start", "end") and n.branch == "main":
                edges.append(
                    MissionGraphEdge(
                        source=n.node_id,
                        target=dock_node.node_id,
                        condition="safety_trigger",
                    )
                )
        edges.append(MissionGraphEdge(source=dock_node.node_id, target=end.node_id))
    return MissionGraph(nodes=tuple(nodes), edges=tuple(edges))


def _compile_hash(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _final_status(diagnostics: tuple[Diagnostic, ...]) -> str:
    if has_rejection(diagnostics):
        return COMPILE_STATUS_REJECTED
    ambiguity = any(d.code in ("ambiguous_clause", "ambiguous_destination") for d in diagnostics)
    if ambiguity:
        return COMPILE_STATUS_AMBIGUOUS
    if has_warning(diagnostics):
        return COMPILE_STATUS_OK_WITH_WARNINGS
    return COMPILE_STATUS_OK


def compile_intent(
    intent: str,
    *,
    plan_id: str,
    generated_at_utc: str,
    odd_profile_id: str = DEFAULT_ODD_PROFILE_ID,
) -> MissionPlan:
    """Compile a single natural language intent into a candidate mission plan."""

    parse = parse_intent(intent)
    odd: OperationalDesignDomain = get_profile(odd_profile_id)

    objectives: list[MissionObjective] = []
    constraints: list[MissionConstraint] = []
    for idx, clause in enumerate(parse.clauses):
        obj = build_objective_from_clause(clause, idx)
        if obj is not None:
            objectives.append(obj)
            continue
        con = build_constraint_from_clause(clause, idx)
        if con is not None:
            constraints.append(con)

    objectives_t = tuple(objectives)
    constraints_t = tuple(constraints)
    validation_diags = validate_all(objectives_t, constraints_t, odd)
    contradiction_diags = detect_contradictions(objectives_t, constraints_t)
    diagnostics = merge(parse.diagnostics, validation_diags, contradiction_diags)

    risk = classify_risk(
        objectives=objectives_t,
        constraints=constraints_t,
        diagnostics=diagnostics,
        odd=odd,
    )

    graph = _build_graph(objectives_t, constraints_t)
    status = _final_status(diagnostics)
    if status == COMPILE_STATUS_REJECTED:
        # When rejected, present an empty graph except start/end.
        graph = MissionGraph(
            nodes=(
                MissionGraphNode(node_id="start", label="Mission start", stage_kind="start"),
                MissionGraphNode(node_id="end", label="Mission rejected", stage_kind="end"),
            ),
            edges=(MissionGraphEdge(source="start", target="end", condition="rejected"),),
        )

    payload_for_hash = {
        "plan_id": plan_id,
        "compiler_version": COMPILER_VERSION,
        "odd": odd_profile_id,
        "normalized_intent": parse.normalized_text,
        "objectives": [asdict(o) for o in objectives_t],
        "constraints": [asdict(c) for c in constraints_t],
        "diagnostics": [asdict(d) for d in diagnostics],
        "status": status,
    }
    compile_hash = _compile_hash(payload_for_hash)

    assumptions: list[str] = []
    if objectives_t and not any(o.objective_kind == STAGE_DOCK_RETURN for o in objectives_t):
        assumptions.append("Mission does not include a return-to-dock; operator is expected to recover the rover.")
    if any(c.constraint_kind == "safety_trigger" for c in constraints_t):
        assumptions.append("Safety trigger is honoured by the runtime safety supervisor, not by the compiler.")

    explainability = build_chain(
        original_intent=intent,
        normalized_intent=parse.normalized_text,
        clauses=parse.clauses,
        rejected=parse.rejected_clauses,
        objectives=objectives_t,
        constraints=constraints_t,
        diagnostics=diagnostics,
        risk=risk,
        final_status=status,
    )

    plan = MissionPlan(
        plan_id=plan_id,
        compiler_version=COMPILER_VERSION,
        odd_profile_id=odd_profile_id,
        original_intent=intent,
        normalized_intent=parse.normalized_text,
        objectives=objectives_t,
        constraints=constraints_t,
        graph=graph,
        risk=risk,
        status=status,
        diagnostics=diagnostics,
        compile_hash=compile_hash,
        generated_at_utc=generated_at_utc,
        extracted_clauses=parse.clauses,
        rejected_clauses=parse.rejected_clauses,
        assumptions=tuple(assumptions),
        explainability_chain=explainability,
        replay_binding_id=f"replay-{plan_id}",
    )
    return plan


def compile_and_bind(intent: str, **kwargs) -> tuple[MissionPlan, "ReplayBinding"]:  # type: ignore[name-defined]
    plan = compile_intent(intent, **kwargs)
    binding = build_replay_binding(plan)
    return plan, binding


__all__ = ["compile_intent", "compile_and_bind"]
