"""Dataclasses, status enums, and the verbatim disclaimer.

The platform is **not safety-certified**. The skill LLM provider is
*disabled by default*. Every field below is exposed via
:mod:`app.skill_llm_provider` so callers do not have to reach into
private modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Optional


SKILL_LLM_PROVIDER_VERSION: str = "phase15b-1"

SKILL_LLM_DISCLAIMER: str = (
    "This LLM skill candidate is a development aid only. It does "
    "not represent autonomous execution, safety certification, or "
    "regulatory approval."
)


# ---------------------------------------------------------------------
# Provider modes. ``disabled`` is the default; tests and CLIs use
# ``fixture``; the local providers (``local_http`` / ``ollama`` /
# ``llama_cpp``) require an explicit opt-in flag.
# ---------------------------------------------------------------------


class ProviderMode(str, Enum):
    DISABLED = "disabled"
    FIXTURE = "fixture"
    LOCAL_HTTP = "local_http"
    OLLAMA = "ollama"
    LLAMA_CPP = "llama_cpp"


PROVIDER_MODES: tuple[str, ...] = tuple(m.value for m in ProviderMode)


# Provider status returned alongside each provider call. Used to
# distinguish "I returned a candidate" from "I refused to run".
class ProviderStatus(str, Enum):
    READY = "ready"
    NOT_CONFIGURED = "not_configured"
    REJECTED_ENDPOINT = "rejected_endpoint"
    REQUIRES_OPT_IN = "requires_opt_in"
    PROPOSED = "proposed"


PROVIDER_STATUSES: tuple[str, ...] = tuple(s.value for s in ProviderStatus)


# ---------------------------------------------------------------------
# Candidate vocabulary.
# ---------------------------------------------------------------------


class CandidateStatus(str, Enum):
    PROPOSED = "proposed"
    SANITIZER_REJECTED = "sanitizer_rejected"
    VALIDATOR_REJECTED = "validator_rejected"
    ACCEPTED = "accepted"
    NOT_CONFIGURED = "not_configured"


CANDIDATE_STATUSES: tuple[str, ...] = tuple(s.value for s in CandidateStatus)


class CandidateSafetyStatus(str, Enum):
    SAFE_AFTER_VALIDATION = "safe_after_validation"
    GUARDED = "guarded"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"
    NOT_EVALUATED = "not_evaluated"


class CandidateRejectionReason(str, Enum):
    PROVIDER_DISABLED = "provider_disabled"
    REQUIRES_LOCAL_OPT_IN = "requires_local_opt_in"
    REJECTED_REMOTE_ENDPOINT = "rejected_remote_endpoint"
    INVALID_PROVIDER_OUTPUT = "invalid_provider_output"
    DIRECT_ACTUATOR_COMMAND = "direct_actuator_command"
    UNBOUNDED_MOTION = "unbounded_motion"
    SHELL_OR_CODE_EXECUTION = "shell_or_code_execution"
    NETWORK_ACCESS = "network_access"
    SECRET_LEAK = "secret_leak"
    SAFETY_OVERRIDE = "safety_override"
    DESTRUCTIVE_COMMAND = "destructive_command"
    DIRECT_MOTOR_CONTROL = "direct_motor_control"
    MISSING_STOP_COMMAND = "missing_stop_command"
    MISSING_TIMEOUT = "missing_timeout"
    UNBOUNDED_SPEED = "unbounded_speed"
    UNSUPPORTED_SKILL_TYPE = "unsupported_skill_type"


CANDIDATE_REJECTION_REASONS: tuple[str, ...] = tuple(
    r.value for r in CandidateRejectionReason
)


class CandidateConfidence(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    OVERCONFIDENT = "overconfident"


CONFIDENCE_LABELS: tuple[str, ...] = tuple(c.value for c in CandidateConfidence)


# ---------------------------------------------------------------------
# Models.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class SkillLLMRequest:
    request_id: str
    text: str
    language: str  # SkillLanguage value from Phase 15A
    requested_at_utc: str = ""


@dataclass(frozen=True)
class SkillLLMProviderConfig:
    """Provider configuration loaded from disk or constructed in-process."""

    mode: str  # ProviderMode value
    enabled: bool
    provider_name: str
    model_name: str
    endpoint: str
    extra: Mapping[str, object] = field(default_factory=dict)
    notes: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class SkillLLMProviderResult:
    """Raw envelope returned by a provider call.

    Carries either a structured payload (``status = ready`` or
    ``proposed``) or a deterministic ``not_configured`` /
    ``rejected_endpoint`` / ``requires_opt_in`` shape. The pipeline
    never invents fields; downstream layers read this envelope to
    decide whether to invoke the sanitizer.
    """

    status: str  # ProviderStatus value
    provider_mode: str  # ProviderMode value
    provider_name: str
    model_name: str
    reason: str
    payload: Optional[Mapping[str, object]] = None


@dataclass(frozen=True)
class SkillLLMCandidate:
    candidate_id: str
    source_text: str
    provider_mode: str  # ProviderMode value
    provider_name: str
    model_name: str
    language: str  # SkillLanguage value from Phase 15A
    skill_type: str  # SkillType value from Phase 15A, or "" if unknown
    code: str
    explanation: str
    declared_topics: tuple[str, ...]
    declared_interfaces: tuple[str, ...]
    declared_safety_constraints: tuple[str, ...]
    confidence_label: str  # CandidateConfidence value
    known_uncertainties: tuple[str, ...]
    raw_provider_payload: str


@dataclass(frozen=True)
class SkillLLMSanitizerResult:
    status: str  # "accepted" | "rejected" | "not_evaluated"
    accepted: bool
    reason_codes: tuple[str, ...]
    blocked_fragments: tuple[str, ...]
    notes: tuple[str, ...]
    human_review_required: bool


@dataclass(frozen=True)
class SkillLLMValidationResult:
    """Wraps the Phase 15A skill validator output.

    ``invoked`` is False when the sanitizer rejected the candidate
    before the validator could run; the audit then records both
    sanitizer rejection and the fact that the validator was
    intentionally skipped.
    """

    invoked: bool
    accepted: bool
    diagnostics: tuple[Mapping[str, object], ...]
    skill_type: str
    safety_status: str  # CandidateSafetyStatus value


@dataclass(frozen=True)
class SkillLLMAuditBundle:
    request: SkillLLMRequest
    provider_result: SkillLLMProviderResult
    candidate: Optional[SkillLLMCandidate]
    sanitizer_result: SkillLLMSanitizerResult
    validator_result: SkillLLMValidationResult
    safety_review: Mapping[str, object] | None
    code_card: Mapping[str, object] | None
    final_status: str  # CandidateStatus value
    rejection_reason: str
    generated_at_utc: str
    disclaimer: str = SKILL_LLM_DISCLAIMER


@dataclass(frozen=True)
class SkillLLMGenerationResult:
    """Top-level pipeline result returned by :func:`run_skill_llm_pipeline`."""

    request: SkillLLMRequest
    provider_result: SkillLLMProviderResult
    candidate: Optional[SkillLLMCandidate]
    sanitizer_result: SkillLLMSanitizerResult
    validator_result: SkillLLMValidationResult
    safety_review: Mapping[str, object] | None
    code_card: Mapping[str, object] | None
    final_status: str  # CandidateStatus value
    rejection_reason: str

    @property
    def accepted(self) -> bool:
        return self.final_status == CandidateStatus.ACCEPTED.value
