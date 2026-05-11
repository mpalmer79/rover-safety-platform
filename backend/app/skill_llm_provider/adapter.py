"""Top-level pipeline.

Drives:

    SkillLLMRequest
      → provider.propose
      → SkillLLMProviderResult
      → (if proposed) sanitize_candidate
      → (if sanitizer accepted) Phase 15A skill validator
      → safety review + code card
      → SkillLLMGenerationResult
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping

from .config import (
    DEFAULT_PROVIDER_MODE,
    provider_disabled_response,
)
from .models import (
    CandidateConfidence,
    CandidateRejectionReason,
    CandidateSafetyStatus,
    CandidateStatus,
    PROVIDER_MODES,
    ProviderMode,
    ProviderStatus,
    SkillLLMCandidate,
    SkillLLMGenerationResult,
    SkillLLMProviderConfig,
    SkillLLMProviderResult,
    SkillLLMRequest,
    SkillLLMSanitizerResult,
    SkillLLMValidationResult,
)
from .provider import ProviderError, resolve_provider
from .sanitizer import sanitize_candidate
from .validator_bridge import run_skill_validator_bridge


# Re-export the AdapterResult name so the package __init__ can publish
# it cleanly; in this design AdapterResult is just an alias for the
# generation result.
AdapterResult = SkillLLMGenerationResult


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _empty_sanitizer_result() -> SkillLLMSanitizerResult:
    return SkillLLMSanitizerResult(
        status="not_evaluated",
        accepted=False,
        reason_codes=(),
        blocked_fragments=(),
        notes=(),
        human_review_required=False,
    )


def _empty_validator_result(skill_type: str = "") -> SkillLLMValidationResult:
    return SkillLLMValidationResult(
        invoked=False,
        accepted=False,
        diagnostics=(),
        skill_type=skill_type,
        safety_status=CandidateSafetyStatus.NOT_EVALUATED.value,
    )


def _candidate_from_payload(
    *,
    request: SkillLLMRequest,
    provider_result: SkillLLMProviderResult,
) -> SkillLLMCandidate | None:
    payload = provider_result.payload or {}
    if not isinstance(payload, Mapping):
        return None

    code = str(payload.get("code") or "")
    language = str(payload.get("language") or request.language)
    skill_type = str(payload.get("skill_type") or "")
    explanation = str(payload.get("explanation") or "")
    declared_topics = _str_tuple(payload.get("declared_topics"))
    declared_interfaces = _str_tuple(payload.get("declared_interfaces"))
    declared_safety_constraints = _str_tuple(
        payload.get("declared_safety_constraints")
    )
    confidence = str(payload.get("confidence_label") or CandidateConfidence.MEDIUM.value)
    uncertainties = _str_tuple(payload.get("known_uncertainties"))
    raw = str(payload.get("raw_provider_payload") or "")
    if not raw:
        # Some providers won't emit the field explicitly; fall back
        # to the JSON of the payload so the audit captures whatever
        # arrived.
        try:
            import json

            raw = json.dumps(dict(payload), sort_keys=True)
        except Exception:
            raw = ""

    return SkillLLMCandidate(
        candidate_id=request.request_id or "candidate",
        source_text=request.text,
        provider_mode=provider_result.provider_mode,
        provider_name=provider_result.provider_name,
        model_name=provider_result.model_name,
        language=language,
        skill_type=skill_type,
        code=code,
        explanation=explanation,
        declared_topics=declared_topics,
        declared_interfaces=declared_interfaces,
        declared_safety_constraints=declared_safety_constraints,
        confidence_label=confidence,
        known_uncertainties=uncertainties,
        raw_provider_payload=raw,
    )


def _str_tuple(value) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, (list, tuple)):
        return tuple(str(v) for v in value)
    return ()


def _disabled_result(
    *,
    request: SkillLLMRequest,
    config: SkillLLMProviderConfig,
) -> SkillLLMGenerationResult:
    provider_result = provider_disabled_response(
        request_id=request.request_id,
        source_text=request.text,
        provider_mode=config.mode,
        provider_name=config.provider_name or config.mode,
    )
    return SkillLLMGenerationResult(
        request=request,
        provider_result=provider_result,
        candidate=None,
        sanitizer_result=_empty_sanitizer_result(),
        validator_result=_empty_validator_result(),
        safety_review=None,
        code_card=None,
        final_status=CandidateStatus.NOT_CONFIGURED.value,
        rejection_reason=CandidateRejectionReason.PROVIDER_DISABLED.value,
    )


def run_skill_llm_pipeline(
    *,
    request: SkillLLMRequest,
    config: SkillLLMProviderConfig,
    allow_local_provider: bool = False,
) -> SkillLLMGenerationResult:
    """Run the full pipeline and return a structured result."""

    if config.mode == ProviderMode.DISABLED.value:
        return _disabled_result(request=request, config=config)

    try:
        provider = resolve_provider(config, allow_local_provider=allow_local_provider)
    except ProviderError as exc:
        provider_result = provider_disabled_response(
            request_id=request.request_id,
            source_text=request.text,
            provider_mode=config.mode,
            provider_name=config.provider_name or config.mode,
            reason=str(exc),
        )
        return SkillLLMGenerationResult(
            request=request,
            provider_result=provider_result,
            candidate=None,
            sanitizer_result=_empty_sanitizer_result(),
            validator_result=_empty_validator_result(),
            safety_review=None,
            code_card=None,
            final_status=CandidateStatus.NOT_CONFIGURED.value,
            rejection_reason=CandidateRejectionReason.PROVIDER_DISABLED.value,
        )

    if provider is None:
        # Should only happen for ``disabled``; handled above. Be safe.
        return _disabled_result(request=request, config=config)

    provider_result = provider.propose(
        request=request,
        config=config,
        allow_local_provider=allow_local_provider,
    )

    if provider_result.status == ProviderStatus.PROPOSED.value:
        candidate = _candidate_from_payload(
            request=request, provider_result=provider_result
        )
        if candidate is None:
            return SkillLLMGenerationResult(
                request=request,
                provider_result=provider_result,
                candidate=None,
                sanitizer_result=_empty_sanitizer_result(),
                validator_result=_empty_validator_result(),
                safety_review=None,
                code_card=None,
                final_status=CandidateStatus.SANITIZER_REJECTED.value,
                rejection_reason=CandidateRejectionReason.INVALID_PROVIDER_OUTPUT.value,
            )

        sanitizer_result = sanitize_candidate(candidate)
        validator_result, safety_review, code_card = run_skill_validator_bridge(
            candidate, sanitizer_result
        )

        if not sanitizer_result.accepted:
            return SkillLLMGenerationResult(
                request=request,
                provider_result=provider_result,
                candidate=candidate,
                sanitizer_result=sanitizer_result,
                validator_result=validator_result,
                safety_review=None,
                code_card=None,
                final_status=CandidateStatus.SANITIZER_REJECTED.value,
                rejection_reason=(
                    sanitizer_result.reason_codes[0]
                    if sanitizer_result.reason_codes
                    else CandidateRejectionReason.INVALID_PROVIDER_OUTPUT.value
                ),
            )

        if not validator_result.accepted:
            first_code = ""
            for diag in validator_result.diagnostics:
                code = diag.get("code") if isinstance(diag, Mapping) else None
                if code:
                    first_code = str(code)
                    break
            return SkillLLMGenerationResult(
                request=request,
                provider_result=provider_result,
                candidate=candidate,
                sanitizer_result=sanitizer_result,
                validator_result=validator_result,
                safety_review=None,
                code_card=None,
                final_status=CandidateStatus.VALIDATOR_REJECTED.value,
                rejection_reason=first_code
                or CandidateRejectionReason.MISSING_STOP_COMMAND.value,
            )

        return SkillLLMGenerationResult(
            request=request,
            provider_result=provider_result,
            candidate=candidate,
            sanitizer_result=sanitizer_result,
            validator_result=validator_result,
            safety_review=safety_review,
            code_card=code_card,
            final_status=CandidateStatus.ACCEPTED.value,
            rejection_reason="",
        )

    # Provider refused (not_configured / rejected_endpoint / requires_opt_in).
    if provider_result.status == ProviderStatus.REJECTED_ENDPOINT.value:
        rejection_reason = CandidateRejectionReason.REJECTED_REMOTE_ENDPOINT.value
    elif provider_result.status == ProviderStatus.REQUIRES_OPT_IN.value:
        rejection_reason = CandidateRejectionReason.REQUIRES_LOCAL_OPT_IN.value
    else:
        rejection_reason = CandidateRejectionReason.PROVIDER_DISABLED.value

    return SkillLLMGenerationResult(
        request=request,
        provider_result=provider_result,
        candidate=None,
        sanitizer_result=_empty_sanitizer_result(),
        validator_result=_empty_validator_result(),
        safety_review=None,
        code_card=None,
        final_status=CandidateStatus.NOT_CONFIGURED.value,
        rejection_reason=rejection_reason,
    )
