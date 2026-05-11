"""Phase 14A: deterministic natural-language mission compiler.

The platform is **not safety-certified**. The compiler is an
offline, deterministic translation layer that turns natural
language mission intent into a *candidate* mission plan. The
mission runtime, safety supervisor, and motion arbitration remain
authoritative; this package never authorises motion and never
executes user intent.
"""

from __future__ import annotations

from .audit import build_audit, render_audit_markdown, write_audit
from .compiler import compile_and_bind, compile_intent
from .constraints import (
    build_constraint_from_clause,
    build_objective_from_clause,
    detect_contradictions,
)
from .diagnostics import has_rejection, has_warning, merge, to_dicts
from .examples import EXAMPLES, IntentExample, example_by_id
from .explainability import build_chain, render_markdown as render_chain_markdown
from .models import (
    COMPILER_VERSION,
    COMPILE_STATUSES,
    COMPILE_STATUS_AMBIGUOUS,
    COMPILE_STATUS_OK,
    COMPILE_STATUS_OK_WITH_WARNINGS,
    COMPILE_STATUS_REJECTED,
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
    MissionGraph,
    MissionGraphEdge,
    MissionGraphNode,
    MissionObjective,
    MissionPlan,
    MissionRisk,
    NON_CERTIFICATION_DISCLAIMER,
    OperationalDesignDomain,
    RISK_BANDS,
    RISK_CRITICAL,
    RISK_ELEVATED,
    RISK_HIGH,
    RISK_INFORMATIONAL,
    RISK_LOW,
    RISK_MODERATE,
    SEVERITY_INFO,
    SEVERITY_REJECTION,
    SEVERITY_WARNING,
    STAGE_DOCK_RETURN,
    STAGE_INSPECT,
    STAGE_KINDS,
    STAGE_MOVE,
    STAGE_PATROL,
    STAGE_PAUSE,
    STAGE_TERMINATE,
    STAGE_WAIT,
)
from .odd import DEFAULT_ODD_PROFILE_ID, get_profile, list_profiles
from .parser import ParseResult, parse_intent
from .replay_binding import ReplayBinding, build_replay_binding
from .reporting import (
    plan_to_dict,
    render_plan_markdown,
    render_plan_mermaid,
    write_plan,
    write_replay_binding,
)
from .risk import classify_risk
from .templates import (
    AMBIGUITY_PHRASES,
    DANGEROUS_PHRASES,
    Template,
    all_templates,
    match_clause,
    template_by_id,
)
from .validator import (
    validate_against_odd,
    validate_all,
    validate_recovery_paths,
    validate_route_feasibility,
)


__all__ = [
    "COMPILER_VERSION",
    "NON_CERTIFICATION_DISCLAIMER",
    "COMPILE_STATUSES",
    "COMPILE_STATUS_OK",
    "COMPILE_STATUS_OK_WITH_WARNINGS",
    "COMPILE_STATUS_AMBIGUOUS",
    "COMPILE_STATUS_REJECTED",
    "RISK_BANDS",
    "RISK_INFORMATIONAL",
    "RISK_LOW",
    "RISK_MODERATE",
    "RISK_ELEVATED",
    "RISK_HIGH",
    "RISK_CRITICAL",
    "STAGE_KINDS",
    "STAGE_MOVE",
    "STAGE_PATROL",
    "STAGE_INSPECT",
    "STAGE_WAIT",
    "STAGE_PAUSE",
    "STAGE_DOCK_RETURN",
    "STAGE_TERMINATE",
    "CONSTRAINT_AVOID",
    "CONSTRAINT_RESTRICTED_CORRIDOR",
    "CONSTRAINT_SPEED_LIMIT",
    "CONSTRAINT_TIME_WINDOW",
    "CONSTRAINT_SAFETY_TRIGGER",
    "CONSTRAINT_RECOVERY_DIRECTIVE",
    "CONSTRAINT_CONTINGENCY",
    "SEVERITY_INFO",
    "SEVERITY_WARNING",
    "SEVERITY_REJECTION",
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
    "ReplayBinding",
    "DEFAULT_ODD_PROFILE_ID",
    "Template",
    "AMBIGUITY_PHRASES",
    "DANGEROUS_PHRASES",
    "all_templates",
    "match_clause",
    "template_by_id",
    "get_profile",
    "list_profiles",
    "ParseResult",
    "parse_intent",
    "build_objective_from_clause",
    "build_constraint_from_clause",
    "detect_contradictions",
    "validate_all",
    "validate_against_odd",
    "validate_recovery_paths",
    "validate_route_feasibility",
    "classify_risk",
    "build_chain",
    "render_chain_markdown",
    "build_replay_binding",
    "plan_to_dict",
    "render_plan_markdown",
    "render_plan_mermaid",
    "write_plan",
    "write_replay_binding",
    "build_audit",
    "render_audit_markdown",
    "write_audit",
    "merge",
    "has_rejection",
    "has_warning",
    "to_dicts",
    "EXAMPLES",
    "IntentExample",
    "example_by_id",
    "compile_intent",
    "compile_and_bind",
]
