"""Replay-compatible metadata for a compiled mission plan.

The platform is **not safety-certified**. This module emits the
metadata the existing replay layer would need to align a *future*
run with the compiled plan. It explicitly marks
``runtime_executed=false`` and never references fabricated bag or
event evidence.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .models import MissionPlan


@dataclass(frozen=True)
class ReplayBinding:
    replay_binding_id: str
    plan_id: str
    scenario_id: str
    timeline_markers: tuple[str, ...]
    mission_stages: tuple[str, ...]
    decision_points: tuple[str, ...]
    runtime_executed: bool = False


def build_replay_binding(plan: MissionPlan) -> ReplayBinding:
    binding_id = f"replay-{plan.plan_id}"
    scenario_id = f"compiled-{plan.plan_id}"
    markers = tuple(f"stage:{n.stage_kind}:{n.node_id}" for n in plan.graph.nodes)
    stages = tuple(n.label for n in plan.graph.nodes)
    decision_points = tuple(
        f"edge:{e.source}->{e.target}{':' + e.condition if e.condition else ''}"
        for e in plan.graph.edges
    )
    return ReplayBinding(
        replay_binding_id=binding_id,
        plan_id=plan.plan_id,
        scenario_id=scenario_id,
        timeline_markers=markers,
        mission_stages=stages,
        decision_points=decision_points,
        runtime_executed=False,
    )


def to_dict(binding: ReplayBinding) -> dict:
    out = asdict(binding)
    out["timeline_markers"] = list(binding.timeline_markers)
    out["mission_stages"] = list(binding.mission_stages)
    out["decision_points"] = list(binding.decision_points)
    return out


__all__ = [
    "ReplayBinding",
    "build_replay_binding",
    "to_dict",
]
