"""Dataclasses, status constants, and the verbatim disclaimer.

The platform is **not safety-certified**. The natural-language
mission compiler is an offline, deterministic translation layer; it
never authorises motion and never executes user intent. The mission
runtime and safety supervisor remain authoritative.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


COMPILER_VERSION: str = "phase14a-1"

NON_CERTIFICATION_DISCLAIMER: str = (
    "This system is not safety-certified and does not authorize "
    "autonomous deployment."
)


# Compile status vocabulary.
COMPILE_STATUS_OK: str = "compile_ok"
COMPILE_STATUS_OK_WITH_WARNINGS: str = "compile_ok_with_warnings"
COMPILE_STATUS_AMBIGUOUS: str = "compile_ambiguous"
COMPILE_STATUS_REJECTED: str = "compile_rejected"

COMPILE_STATUSES: tuple[str, ...] = (
    COMPILE_STATUS_OK,
    COMPILE_STATUS_OK_WITH_WARNINGS,
    COMPILE_STATUS_AMBIGUOUS,
    COMPILE_STATUS_REJECTED,
)


# Diagnostic severities.
SEVERITY_INFO: str = "info"
SEVERITY_WARNING: str = "warning"
SEVERITY_REJECTION: str = "rejection"


# Risk bands.
RISK_INFORMATIONAL: str = "informational"
RISK_LOW: str = "low"
RISK_MODERATE: str = "moderate"
RISK_ELEVATED: str = "elevated"
RISK_HIGH: str = "high"
RISK_CRITICAL: str = "critical"

RISK_BANDS: tuple[str, ...] = (
    RISK_INFORMATIONAL,
    RISK_LOW,
    RISK_MODERATE,
    RISK_ELEVATED,
    RISK_HIGH,
    RISK_CRITICAL,
)


# Stage kinds (the bounded set of supported mission stages).
STAGE_MOVE: str = "move"
STAGE_PATROL: str = "patrol"
STAGE_INSPECT: str = "inspect"
STAGE_WAIT: str = "wait"
STAGE_PAUSE: str = "pause"
STAGE_DOCK_RETURN: str = "return_to_dock"
STAGE_TERMINATE: str = "terminate"

STAGE_KINDS: tuple[str, ...] = (
    STAGE_MOVE,
    STAGE_PATROL,
    STAGE_INSPECT,
    STAGE_WAIT,
    STAGE_PAUSE,
    STAGE_DOCK_RETURN,
    STAGE_TERMINATE,
)


# Constraint kinds.
CONSTRAINT_AVOID: str = "avoid_region"
CONSTRAINT_RESTRICTED_CORRIDOR: str = "restricted_corridor"
CONSTRAINT_SPEED_LIMIT: str = "speed_limit"
CONSTRAINT_TIME_WINDOW: str = "time_window"
CONSTRAINT_SAFETY_TRIGGER: str = "safety_trigger"
CONSTRAINT_CONTINGENCY: str = "contingency"
CONSTRAINT_RECOVERY_DIRECTIVE: str = "recovery_directive"


@dataclass(frozen=True)
class Diagnostic:
    """A single compiler diagnostic.

    Diagnostics are first-class outputs. The compiler emits them
    instead of inventing missing information.
    """

    code: str
    severity: str
    message: str
    clause: str = ""
    field: str = ""


@dataclass(frozen=True)
class ExtractedClause:
    """One clause extracted from the user's natural-language input."""

    raw: str
    normalized: str
    template_id: str
    slots: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class MissionObjective:
    """A bounded, named objective derived from a clause.

    Examples: ``move_to_waypoint``, ``inspect_zone``,
    ``return_to_dock``. Objectives are *abstract* — they reference
    waypoint / zone names by string, never invented coordinates.
    """

    objective_id: str
    objective_kind: str
    label: str
    parameters: Mapping[str, str] = field(default_factory=dict)
    source_clause: str = ""


@dataclass(frozen=True)
class MissionConstraint:
    constraint_id: str
    constraint_kind: str
    label: str
    parameters: Mapping[str, str] = field(default_factory=dict)
    source_clause: str = ""


@dataclass(frozen=True)
class OperationalDesignDomain:
    """A snapshot of the authorised operational envelope.

    The ODD is an explicit, declarative profile - not a learned model.
    Compilation rejects plans outside this envelope.
    """

    profile_id: str
    authorized_zones: tuple[str, ...] = ()
    prohibited_regions: tuple[str, ...] = ()
    speed_limit_mps: float = 1.5
    max_mission_minutes: int = 30
    requires_lidar: bool = True
    requires_battery_min_pct: int = 25
    requires_dock_known: bool = True
    operating_window: str = "daylight"
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class MissionGraphNode:
    node_id: str
    label: str
    stage_kind: str
    objective_id: str = ""
    branch: str = "main"


@dataclass(frozen=True)
class MissionGraphEdge:
    source: str
    target: str
    condition: str = ""


@dataclass(frozen=True)
class MissionGraph:
    nodes: tuple[MissionGraphNode, ...]
    edges: tuple[MissionGraphEdge, ...]


@dataclass(frozen=True)
class MissionRisk:
    band: str
    score: int
    drivers: tuple[str, ...] = ()
    mitigations: tuple[str, ...] = ()
    required_reviewer_actions: tuple[str, ...] = ()


@dataclass(frozen=True)
class MissionPlan:
    """The compiled, validated mission candidate.

    A plan is a *candidate* only; the runtime is authoritative. The
    compiler never claims this plan has executed.
    """

    plan_id: str
    compiler_version: str
    odd_profile_id: str
    original_intent: str
    normalized_intent: str
    objectives: tuple[MissionObjective, ...]
    constraints: tuple[MissionConstraint, ...]
    graph: MissionGraph
    risk: MissionRisk
    status: str
    diagnostics: tuple[Diagnostic, ...]
    compile_hash: str
    generated_at_utc: str
    extracted_clauses: tuple[ExtractedClause, ...]
    rejected_clauses: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    explainability_chain: tuple[str, ...] = ()
    replay_binding_id: str = ""


__all__ = [
    "COMPILER_VERSION",
    "NON_CERTIFICATION_DISCLAIMER",
    "COMPILE_STATUS_OK",
    "COMPILE_STATUS_OK_WITH_WARNINGS",
    "COMPILE_STATUS_AMBIGUOUS",
    "COMPILE_STATUS_REJECTED",
    "COMPILE_STATUSES",
    "SEVERITY_INFO",
    "SEVERITY_WARNING",
    "SEVERITY_REJECTION",
    "RISK_INFORMATIONAL",
    "RISK_LOW",
    "RISK_MODERATE",
    "RISK_ELEVATED",
    "RISK_HIGH",
    "RISK_CRITICAL",
    "RISK_BANDS",
    "STAGE_MOVE",
    "STAGE_PATROL",
    "STAGE_INSPECT",
    "STAGE_WAIT",
    "STAGE_PAUSE",
    "STAGE_DOCK_RETURN",
    "STAGE_TERMINATE",
    "STAGE_KINDS",
    "CONSTRAINT_AVOID",
    "CONSTRAINT_RESTRICTED_CORRIDOR",
    "CONSTRAINT_SPEED_LIMIT",
    "CONSTRAINT_TIME_WINDOW",
    "CONSTRAINT_SAFETY_TRIGGER",
    "CONSTRAINT_CONTINGENCY",
    "CONSTRAINT_RECOVERY_DIRECTIVE",
    "Diagnostic",
    "ExtractedClause",
    "MissionObjective",
    "MissionConstraint",
    "OperationalDesignDomain",
    "MissionGraphNode",
    "MissionGraphEdge",
    "MissionGraph",
    "MissionRisk",
    "MissionPlan",
]
