"""Translate extracted clauses into objectives + constraints.

The platform is **not safety-certified**. This module is a pure
mapping from the parser's bounded template ids to the typed mission
objects (objectives, constraints). It never invents fields.
"""

from __future__ import annotations

from typing import Mapping

from .models import (
    CONSTRAINT_AVOID,
    CONSTRAINT_CONTINGENCY,
    CONSTRAINT_RECOVERY_DIRECTIVE,
    CONSTRAINT_RESTRICTED_CORRIDOR,
    CONSTRAINT_SAFETY_TRIGGER,
    CONSTRAINT_SPEED_LIMIT,
    CONSTRAINT_TIME_WINDOW,
    Diagnostic,
    ExtractedClause,
    MissionConstraint,
    MissionObjective,
    SEVERITY_REJECTION,
    SEVERITY_WARNING,
    STAGE_DOCK_RETURN,
    STAGE_INSPECT,
    STAGE_MOVE,
    STAGE_PATROL,
    STAGE_PAUSE,
    STAGE_TERMINATE,
    STAGE_WAIT,
)


_TEMPLATE_TO_STAGE: Mapping[str, str] = {
    "move_to_target": STAGE_MOVE,
    "patrol_area": STAGE_PATROL,
    "inspect_zone": STAGE_INSPECT,
    "return_to_dock": STAGE_DOCK_RETURN,
    "wait_for_condition": STAGE_WAIT,
    "pause_at_checkpoint": STAGE_PAUSE,
    "terminate_mission": STAGE_TERMINATE,
}


_TEMPLATE_TO_CONSTRAINT_KIND: Mapping[str, str] = {
    "avoid_region": CONSTRAINT_AVOID,
    "restricted_corridor_avoidance": CONSTRAINT_RESTRICTED_CORRIDOR,
    "speed_limit": CONSTRAINT_SPEED_LIMIT,
    "time_window": CONSTRAINT_TIME_WINDOW,
    "safe_stop_on_trigger": CONSTRAINT_SAFETY_TRIGGER,
    "recovery_directive_return_to_dock": CONSTRAINT_RECOVERY_DIRECTIVE,
    "continue_under_degraded": CONSTRAINT_CONTINGENCY,
}


def build_objective_from_clause(
    clause: ExtractedClause, idx: int
) -> MissionObjective | None:
    stage = _TEMPLATE_TO_STAGE.get(clause.template_id)
    if stage is None:
        return None
    obj_id = f"obj-{idx + 1:02d}"
    label_parts: list[str] = [stage]
    for key in ("target", "zone", "region", "condition"):
        if key in clause.slots and clause.slots[key]:
            label_parts.append(clause.slots[key])
    label = "/".join(label_parts)
    return MissionObjective(
        objective_id=obj_id,
        objective_kind=stage,
        label=label,
        parameters=dict(clause.slots),
        source_clause=clause.raw,
    )


def build_constraint_from_clause(
    clause: ExtractedClause, idx: int
) -> MissionConstraint | None:
    kind = _TEMPLATE_TO_CONSTRAINT_KIND.get(clause.template_id)
    if kind is None:
        return None
    cid = f"con-{idx + 1:02d}"
    label_parts: list[str] = [kind]
    for key in ("region", "limit_mps", "window", "trigger"):
        if key in clause.slots and clause.slots[key]:
            label_parts.append(clause.slots[key])
    return MissionConstraint(
        constraint_id=cid,
        constraint_kind=kind,
        label="/".join(label_parts),
        parameters=dict(clause.slots),
        source_clause=clause.raw,
    )


def detect_contradictions(
    objectives: tuple[MissionObjective, ...],
    constraints: tuple[MissionConstraint, ...],
) -> tuple[Diagnostic, ...]:
    """Report contradictions between objectives and constraints."""

    diags: list[Diagnostic] = []
    targets = {
        obj.parameters.get("target", "").strip().lower()
        for obj in objectives
        if obj.objective_kind == "move"
    } - {""}
    zones_visited = {
        obj.parameters.get("zone", "").strip().lower()
        for obj in objectives
        if obj.objective_kind in ("patrol", "inspect")
    } - {""}
    # Avoid-region contradictions
    for con in constraints:
        if con.constraint_kind == CONSTRAINT_AVOID:
            region = con.parameters.get("region", "").strip().lower()
            if region and region in (targets | zones_visited):
                diags.append(
                    Diagnostic(
                        code="contradiction",
                        severity=SEVERITY_REJECTION,
                        message=(
                            "mission both visits and avoids "
                            f"region {region!r}"
                        ),
                        clause=con.source_clause,
                        field=region,
                    )
                )
        if con.constraint_kind == CONSTRAINT_SPEED_LIMIT:
            raw_limit = con.parameters.get("limit_mps", "").strip()
            if raw_limit:
                try:
                    if float(raw_limit) <= 0:
                        diags.append(
                            Diagnostic(
                                code="contradiction",
                                severity=SEVERITY_REJECTION,
                                message="non-positive speed limit is not permitted",
                                clause=con.source_clause,
                                field="limit_mps",
                            )
                        )
                except ValueError:
                    diags.append(
                        Diagnostic(
                            code="malformed_speed_limit",
                            severity=SEVERITY_WARNING,
                            message=f"speed limit {raw_limit!r} is not a number",
                            clause=con.source_clause,
                            field="limit_mps",
                        )
                    )
    return tuple(diags)


__all__ = [
    "build_objective_from_clause",
    "build_constraint_from_clause",
    "detect_contradictions",
]
