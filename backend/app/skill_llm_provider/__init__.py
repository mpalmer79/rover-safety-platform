"""Phase 15B: local LLM skill candidate provider (disabled by default).

The platform is **not safety-certified**. This package adds a
*disabled-by-default*, *local-only* seam where a future local LLM
could propose robotics-skill code candidates. Every candidate
passes through:

    LLM provider (mock / fixture / local)
      → sanitizer  (forbidden-phrase chokepoint)
      → Phase 15A skill validator  (deterministic safety rules)
      → Phase 15A safety review
      → audit bundle

The deterministic validator and the runtime safety supervisor
remain authoritative. The LLM proposes, deterministic systems
decide. No cloud APIs, no external endpoints, no code execution,
no robot control.
"""

from __future__ import annotations

from .adapter import (
    AdapterResult,
    run_skill_llm_pipeline,
)
from .audit import (
    audit_to_dict,
    build_audit_bundle,
    render_llm_candidate_report_markdown,
)
from .config import (
    DEFAULT_PROVIDER_MODE,
    KNOWN_PROVIDER_MODES,
    config_to_dict,
    is_loopback_url,
    load_provider_config,
    parse_provider_config,
    provider_disabled_response,
    require_local_endpoint,
)
from .fixture_provider import (
    FIXTURE_REGISTRY,
    FixtureProvider,
    list_fixture_ids,
)
from .llama_cpp_provider import (
    LlamaCppProvider,
    llama_cpp_disabled_response,
)
from .local_http_provider import (
    LocalHttpProvider,
    local_http_disabled_response,
)
from .models import (
    CANDIDATE_REJECTION_REASONS,
    CANDIDATE_STATUSES,
    CONFIDENCE_LABELS,
    CandidateConfidence,
    CandidateRejectionReason,
    CandidateSafetyStatus,
    CandidateStatus,
    PROVIDER_MODES,
    PROVIDER_STATUSES,
    ProviderMode,
    ProviderStatus,
    SKILL_LLM_DISCLAIMER,
    SKILL_LLM_PROVIDER_VERSION,
    SkillLLMAuditBundle,
    SkillLLMCandidate,
    SkillLLMGenerationResult,
    SkillLLMProviderConfig,
    SkillLLMProviderResult,
    SkillLLMRequest,
    SkillLLMSanitizerResult,
    SkillLLMValidationResult,
)
from .ollama_provider import (
    OllamaProvider,
    ollama_disabled_response,
)
from .provider import (
    ProviderError,
    SkillLLMProvider,
    resolve_provider,
)
from .reporter import write_audit_files
from .sanitizer import (
    FORBIDDEN_FRAGMENTS,
    sanitize_candidate,
)
from .validator_bridge import (
    run_skill_validator_bridge,
)


__all__ = [
    "AdapterResult",
    "CANDIDATE_REJECTION_REASONS",
    "CANDIDATE_STATUSES",
    "CONFIDENCE_LABELS",
    "CandidateConfidence",
    "CandidateRejectionReason",
    "CandidateSafetyStatus",
    "CandidateStatus",
    "DEFAULT_PROVIDER_MODE",
    "FIXTURE_REGISTRY",
    "FORBIDDEN_FRAGMENTS",
    "FixtureProvider",
    "KNOWN_PROVIDER_MODES",
    "LlamaCppProvider",
    "LocalHttpProvider",
    "OllamaProvider",
    "PROVIDER_MODES",
    "PROVIDER_STATUSES",
    "ProviderError",
    "ProviderMode",
    "ProviderStatus",
    "SKILL_LLM_DISCLAIMER",
    "SKILL_LLM_PROVIDER_VERSION",
    "SkillLLMAuditBundle",
    "SkillLLMCandidate",
    "SkillLLMGenerationResult",
    "SkillLLMProvider",
    "SkillLLMProviderConfig",
    "SkillLLMProviderResult",
    "SkillLLMRequest",
    "SkillLLMSanitizerResult",
    "SkillLLMValidationResult",
    "audit_to_dict",
    "build_audit_bundle",
    "config_to_dict",
    "is_loopback_url",
    "list_fixture_ids",
    "llama_cpp_disabled_response",
    "load_provider_config",
    "local_http_disabled_response",
    "ollama_disabled_response",
    "parse_provider_config",
    "provider_disabled_response",
    "render_llm_candidate_report_markdown",
    "require_local_endpoint",
    "resolve_provider",
    "run_skill_llm_pipeline",
    "run_skill_validator_bridge",
    "sanitize_candidate",
    "write_audit_files",
]
