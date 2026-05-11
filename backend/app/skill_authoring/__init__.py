"""Phase 15A: deterministic robotics skill authoring workbench.

The platform is **not safety-certified**. The skill authoring layer
is an offline, deterministic translation pipeline from a natural
developer request into a bounded, reviewable robotics code
snippet. No real LLM is invoked, no code is executed, and no
generated snippet may bypass the safety supervisor's authority.

Public flow:

    developer request text
       │
       ▼
    intent_parser.parse_request
       │   (deterministic; no fabrication)
       ▼
    SkillCandidate                ← rejected / ambiguous / candidate
       │
       ▼
    generator.generate_skill
       │   (template instantiation only)
       ▼
    GeneratedSkill
       │
       ▼
    validator.validate_generated_skill
       │   (re-check the snippet against safety rules)
       ▼
    safety_review.review_generated_skill
       │
       ▼
    audit.build_audit_bundle
       │
       ▼
    reporter.write_audit_files     (filesystem only)
"""

from __future__ import annotations

from .audit import (
    build_audit_bundle,
    render_rejection_markdown,
    render_skill_report_markdown,
)
from .catalog import (
    SKILL_CATALOG,
    find_template,
    list_supported_skills,
)
from .diagnostics import (
    DIAGNOSTIC_CODES,
    code_card_metadata,
)
from .examples import (
    ACCEPTED_EXAMPLES,
    REJECTED_EXAMPLES,
    SkillExample,
    accepted_example_by_id,
    rejected_example_by_id,
)
from .generator import generate_skill
from .intent_parser import parse_request
from .models import (
    CodeCard,
    GeneratedSkill,
    SKILL_AUTHORING_DISCLAIMER,
    SKILL_AUTHORING_VERSION,
    SkillAuditBundle,
    SkillAuthoringRequest,
    SkillCandidate,
    SkillDiagnostic,
    SkillGenerationResult,
    SkillGenerationStatus,
    SkillLanguage,
    SkillParameter,
    SkillRejectionReason,
    SkillRiskBand,
    SkillSafetyReview,
    SkillSafetyStatus,
    SkillTemplate,
    SkillType,
)
from .reporter import write_audit_files
from .safety_review import review_generated_skill
from .validator import (
    FORBIDDEN_CODE_TOKENS,
    REQUIRED_CODE_TOKENS,
    validate_generated_skill,
    validate_intent_request,
)


__all__ = [
    "ACCEPTED_EXAMPLES",
    "CodeCard",
    "DIAGNOSTIC_CODES",
    "FORBIDDEN_CODE_TOKENS",
    "GeneratedSkill",
    "REJECTED_EXAMPLES",
    "REQUIRED_CODE_TOKENS",
    "SKILL_AUTHORING_DISCLAIMER",
    "SKILL_AUTHORING_VERSION",
    "SKILL_CATALOG",
    "SkillAuditBundle",
    "SkillAuthoringRequest",
    "SkillCandidate",
    "SkillDiagnostic",
    "SkillExample",
    "SkillGenerationResult",
    "SkillGenerationStatus",
    "SkillLanguage",
    "SkillParameter",
    "SkillRejectionReason",
    "SkillRiskBand",
    "SkillSafetyReview",
    "SkillSafetyStatus",
    "SkillTemplate",
    "SkillType",
    "accepted_example_by_id",
    "build_audit_bundle",
    "code_card_metadata",
    "find_template",
    "generate_skill",
    "list_supported_skills",
    "parse_request",
    "rejected_example_by_id",
    "render_rejection_markdown",
    "render_skill_report_markdown",
    "review_generated_skill",
    "validate_generated_skill",
    "validate_intent_request",
    "write_audit_files",
]
