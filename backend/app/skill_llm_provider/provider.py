"""Abstract provider interface + factory.

The factory enforces the Phase 15B safety policy:

* default mode is ``disabled``;
* ``local_http`` / ``ollama`` / ``llama_cpp`` require both
  ``allow_local_provider=True`` AND ``config.enabled=True``;
* any non-loopback endpoint is rejected by
  :func:`require_local_endpoint` before the provider is even
  instantiated.
"""

from __future__ import annotations

from typing import Protocol

from .config import (
    DEFAULT_PROVIDER_MODE,
    KNOWN_PROVIDER_MODES,
    provider_disabled_response,
    require_local_endpoint,
)
from .models import (
    ProviderMode,
    ProviderStatus,
    SkillLLMProviderConfig,
    SkillLLMProviderResult,
    SkillLLMRequest,
)


class ProviderError(RuntimeError):
    pass


class SkillLLMProvider(Protocol):
    """Provider contract.

    Implementations MUST be deterministic, offline, and side-effect
    free in this phase. They must never make a network call unless
    the operator has explicitly opted in (and even then, only to a
    loopback host).
    """

    name: str
    mode: str

    def propose(
        self,
        *,
        request: SkillLLMRequest,
        config: SkillLLMProviderConfig,
        allow_local_provider: bool,
    ) -> SkillLLMProviderResult: ...


def _opt_in_response(
    *,
    request: SkillLLMRequest,
    config: SkillLLMProviderConfig,
    reason: str,
) -> SkillLLMProviderResult:
    return SkillLLMProviderResult(
        status=ProviderStatus.REQUIRES_OPT_IN.value,
        provider_mode=config.mode,
        provider_name=config.provider_name or config.mode,
        model_name=config.model_name,
        reason=reason,
        payload={"request_id": request.request_id, "source_text": request.text},
    )


def _rejected_endpoint_response(
    *,
    request: SkillLLMRequest,
    config: SkillLLMProviderConfig,
    reason: str,
) -> SkillLLMProviderResult:
    return SkillLLMProviderResult(
        status=ProviderStatus.REJECTED_ENDPOINT.value,
        provider_mode=config.mode,
        provider_name=config.provider_name or config.mode,
        model_name=config.model_name,
        reason=reason,
        payload={"request_id": request.request_id, "source_text": request.text},
    )


def resolve_provider(
    config: SkillLLMProviderConfig,
    *,
    allow_local_provider: bool,
) -> "SkillLLMProvider | None":
    """Return the provider instance for ``config.mode``.

    Returns ``None`` for ``disabled``; the caller should emit a
    ``not_configured`` provider result. Raises :class:`ProviderError`
    when the mode is unknown.

    The local providers (``local_http``, ``ollama``, ``llama_cpp``)
    each return an instance, but their ``propose`` method will emit
    ``REQUIRES_OPT_IN`` or ``REJECTED_ENDPOINT`` envelopes when
    ``allow_local_provider`` is False or the endpoint is non-local.
    """

    mode = config.mode
    if mode not in KNOWN_PROVIDER_MODES:
        raise ProviderError(
            f"unsupported provider mode {mode!r}; expected one of {KNOWN_PROVIDER_MODES}"
        )

    if mode == ProviderMode.DISABLED.value:
        return None
    if mode == ProviderMode.FIXTURE.value:
        from .fixture_provider import FixtureProvider

        return FixtureProvider()
    if mode == ProviderMode.LOCAL_HTTP.value:
        from .local_http_provider import LocalHttpProvider

        return LocalHttpProvider()
    if mode == ProviderMode.OLLAMA.value:
        from .ollama_provider import OllamaProvider

        return OllamaProvider()
    if mode == ProviderMode.LLAMA_CPP.value:
        from .llama_cpp_provider import LlamaCppProvider

        return LlamaCppProvider()
    raise ProviderError(f"unreachable provider mode: {mode}")


def evaluate_local_opt_in(
    *,
    request: SkillLLMRequest,
    config: SkillLLMProviderConfig,
    allow_local_provider: bool,
) -> SkillLLMProviderResult | None:
    """Check the opt-in + endpoint policy for the local providers.

    Returns a ready-to-emit envelope when the policy refuses; returns
    ``None`` when the caller may proceed. The actual local providers
    never call the network — they still emit a ``not_configured``
    envelope in this phase — but the policy check runs first so the
    audit records the operator's intent honestly.
    """

    if not allow_local_provider:
        return _opt_in_response(
            request=request,
            config=config,
            reason=(
                "local LLM provider requires --allow-local-provider and "
                "an enabled config"
            ),
        )
    if not config.enabled:
        return _opt_in_response(
            request=request,
            config=config,
            reason=f"provider config is disabled (mode={config.mode})",
        )
    if config.endpoint:
        ok, reason = require_local_endpoint(config.endpoint)
        if not ok:
            return _rejected_endpoint_response(
                request=request, config=config, reason=reason
            )
    return None
