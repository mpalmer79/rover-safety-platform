"""Local LLM skill candidate provider (disabled by default)."""

from __future__ import annotations

from .adapter import run_skill_llm_pipeline
from .audit import (
    audit_to_dict,
    build_audit_bundle,
)
from .candidate_normalizer import (
    NORMALIZATION_STATUS_ACCEPTED,
    NORMALIZATION_STATUS_REJECTED,
    normalization_result_to_dict,
    normalize_candidate_payload,
)
from .candidate_ranker import (
    rank_candidates,
    ranking_to_dict,
)
from .candidate_repair import (
    REPAIR_STATUS_NOT_APPLICABLE,
    REPAIR_STATUS_REQUIRES_HUMAN_REVIEW,
    REPAIR_STATUS_SUGGESTION_ONLY,
    repair_bundle_to_dict,
    suggest_repairs,
)
from .config import (
    DEFAULT_PROVIDER_MODE,
    KNOWN_PROVIDER_MODES,
    config_to_dict,
    is_loopback_url,
    load_provider_config,
    parse_provider_config,
    require_local_endpoint,
)
from .fixture_provider import (
    FIXTURE_REGISTRY,
    list_fixture_ids,
)
from .model_capabilities import (
    capability_to_dict,
    default_capability_registry,
    find_capability,
)
from .models import (
    CandidateRejectionReason,
    PROVIDER_MODES,
    SKILL_LLM_DISCLAIMER,
    SkillLLMCandidate,
    SkillLLMProviderConfig,
    SkillLLMRequest,
    SkillLLMSanitizerResult,
    SkillLLMValidationResult,
)
from .provider import resolve_provider
from .provider_readiness import (
    READINESS_DISABLED,
    READINESS_READY,
    READINESS_REJECTED_ENDPOINT,
    READINESS_REQUIRES_OPT_IN,
    check_provider_readiness,
)
from .reporter import write_audit_files
from .safety_critique import (
    VERDICT_FAIL,
    VERDICT_OK,
    VERDICT_WARN,
    critique_candidate,
)
from .sanitizer import (
    FORBIDDEN_FRAGMENTS,
    sanitize_candidate,
)

__all__ = [
    "CandidateRejectionReason",
    "DEFAULT_PROVIDER_MODE",
    "FIXTURE_REGISTRY",
    "FORBIDDEN_FRAGMENTS",
    "KNOWN_PROVIDER_MODES",
    "NORMALIZATION_STATUS_ACCEPTED",
    "NORMALIZATION_STATUS_REJECTED",
    "PROVIDER_MODES",
    "READINESS_DISABLED",
    "READINESS_READY",
    "READINESS_REJECTED_ENDPOINT",
    "READINESS_REQUIRES_OPT_IN",
    "REPAIR_STATUS_NOT_APPLICABLE",
    "REPAIR_STATUS_REQUIRES_HUMAN_REVIEW",
    "REPAIR_STATUS_SUGGESTION_ONLY",
    "SKILL_LLM_DISCLAIMER",
    "SkillLLMCandidate",
    "SkillLLMProviderConfig",
    "SkillLLMRequest",
    "SkillLLMSanitizerResult",
    "SkillLLMValidationResult",
    "VERDICT_FAIL",
    "VERDICT_OK",
    "VERDICT_WARN",
    "audit_to_dict",
    "build_audit_bundle",
    "capability_to_dict",
    "check_provider_readiness",
    "config_to_dict",
    "critique_candidate",
    "default_capability_registry",
    "find_capability",
    "is_loopback_url",
    "list_fixture_ids",
    "load_provider_config",
    "normalization_result_to_dict",
    "normalize_candidate_payload",
    "parse_provider_config",
    "rank_candidates",
    "ranking_to_dict",
    "repair_bundle_to_dict",
    "require_local_endpoint",
    "resolve_provider",
    "run_skill_llm_pipeline",
    "sanitize_candidate",
    "suggest_repairs",
    "write_audit_files",
]
