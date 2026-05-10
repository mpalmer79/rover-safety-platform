"""Subsystem -> requirement-id mapping.

The mapper uses the live :mod:`app.verification.requirements`
registry as the source of truth. Each subsystem resolves to one or
more :class:`RequirementKind` values; the mapper returns every
matching ``REQ-*`` id from the registry. Unknown subsystems are
reported as unmapped so the report can surface them.
"""

from __future__ import annotations

from typing import Optional

from app.reliability_impact.models import (
    RequirementImpact,
    Subsystem,
    SubsystemImpact,
)
from app.verification.requirements import (
    REQUIREMENTS,
    RequirementKind,
    RequirementsRegistry,
)


_SUBSYSTEM_TO_KINDS: dict[Subsystem, tuple[RequirementKind, ...]] = {
    Subsystem.SAFETY: (RequirementKind.SAFETY, RequirementKind.FAULT, RequirementKind.OPERATOR),
    Subsystem.MISSION: (RequirementKind.MISSION, RequirementKind.WORLD),
    Subsystem.MOTION: (RequirementKind.SAFETY, RequirementKind.MISSION),
    Subsystem.REPLAY: (RequirementKind.REPLAY,),
    Subsystem.INCIDENT_ANALYSIS: (RequirementKind.INCIDENT,),
    Subsystem.REPLAY_REVIEW: (RequirementKind.REPLAY,),
    Subsystem.REPLAY_ANALYTICS: (RequirementKind.ANALYTICS,),
    Subsystem.RUNTIME_VALIDATION: (RequirementKind.RUNTIME,),
    Subsystem.VERIFICATION: (
        RequirementKind.SAFETY,
        RequirementKind.REPLAY,
        RequirementKind.RUNTIME,
        RequirementKind.MISSION,
    ),
    Subsystem.RELIABILITY_IMPACT: (RequirementKind.IMPACT,),
    Subsystem.ROS_WORKSPACE: (
        RequirementKind.RUNTIME,
        RequirementKind.REPLAY,
        RequirementKind.OPERATOR,
    ),
    Subsystem.GAZEBO_SIMULATION: (RequirementKind.RUNTIME,),
    Subsystem.OBSERVABILITY: (
        RequirementKind.DIAGNOSTICS,
        RequirementKind.REPLAY,
    ),
    Subsystem.DOCS: (),
    Subsystem.TESTS: (),
    Subsystem.CI: (RequirementKind.RUNTIME, RequirementKind.IMPACT),
    Subsystem.EVIDENCE: (RequirementKind.REPLAY, RequirementKind.ANALYTICS),
    Subsystem.UNKNOWN: (),
}


def map_subsystem_to_requirements(
    subsystem: Subsystem,
    *,
    registry: Optional[RequirementsRegistry] = None,
) -> RequirementImpact:
    """Return the :class:`RequirementImpact` for a subsystem.

    Documentation-only and test-only subsystems map to no
    requirements but are not treated as unmapped — the notes field
    explains the deliberate choice.
    """

    registry = registry or RequirementsRegistry(REQUIREMENTS)
    kinds = _SUBSYSTEM_TO_KINDS.get(subsystem, ())
    seen: list[str] = []
    seen_set: set[str] = set()
    for kind in kinds:
        for req in registry.by_kind(kind):
            if req.req_id in seen_set:
                continue
            seen.append(req.req_id)
            seen_set.add(req.req_id)

    if subsystem == Subsystem.DOCS:
        notes = "documentation-only change; no direct REQ-* coverage"
    elif subsystem == Subsystem.TESTS:
        notes = "test-only change; rerun affected suites instead of mapping requirements"
    elif subsystem == Subsystem.UNKNOWN:
        notes = "unknown subsystem; classify the path explicitly to enable mapping"
    elif not seen:
        notes = "no requirements declared for this subsystem"
    else:
        notes = ""

    return RequirementImpact(
        subsystem=subsystem,
        requirement_ids=tuple(seen),
        notes=notes,
    )


def map_impacts(
    impacts: list[SubsystemImpact],
    *,
    registry: Optional[RequirementsRegistry] = None,
) -> list[RequirementImpact]:
    """Map a list of subsystem impacts to a list of requirement impacts."""

    registry = registry or RequirementsRegistry(REQUIREMENTS)
    out: list[RequirementImpact] = []
    for impact in impacts:
        out.append(
            map_subsystem_to_requirements(impact.subsystem, registry=registry)
        )
    return out
