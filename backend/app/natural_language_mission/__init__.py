"""English -> compiled mission objective compiler."""

from __future__ import annotations

from .audit import (
    build_audit,
    render_audit_markdown,
    write_audit,
)
from .compiler import compile_intent
from .constraints import detect_contradictions
from .examples import EXAMPLES
from .explainability import build_chain
from .models import (
    COMPILER_VERSION,
    COMPILE_STATUS_AMBIGUOUS,
    COMPILE_STATUS_OK,
    COMPILE_STATUS_OK_WITH_WARNINGS,
    COMPILE_STATUS_REJECTED,
    NON_CERTIFICATION_DISCLAIMER,
    RISK_BANDS,
    RISK_CRITICAL,
    RISK_LOW,
    RISK_MODERATE,
)
from .odd import (
    DEFAULT_ODD_PROFILE_ID,
    get_profile,
    list_profiles,
)
from .parser import parse_intent
from .replay_binding import build_replay_binding
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
    all_templates,
    template_by_id,
)
from .validator import validate_all

__all__ = [
    "AMBIGUITY_PHRASES",
    "COMPILER_VERSION",
    "COMPILE_STATUS_AMBIGUOUS",
    "COMPILE_STATUS_OK",
    "COMPILE_STATUS_OK_WITH_WARNINGS",
    "COMPILE_STATUS_REJECTED",
    "DANGEROUS_PHRASES",
    "DEFAULT_ODD_PROFILE_ID",
    "EXAMPLES",
    "NON_CERTIFICATION_DISCLAIMER",
    "RISK_BANDS",
    "RISK_CRITICAL",
    "RISK_LOW",
    "RISK_MODERATE",
    "all_templates",
    "build_audit",
    "build_chain",
    "build_replay_binding",
    "classify_risk",
    "compile_intent",
    "detect_contradictions",
    "get_profile",
    "list_profiles",
    "parse_intent",
    "plan_to_dict",
    "render_audit_markdown",
    "render_plan_markdown",
    "render_plan_mermaid",
    "template_by_id",
    "validate_all",
    "write_audit",
    "write_plan",
    "write_replay_binding",
]
