"""Ollama provider stub.

Phase 15B does not call Ollama. The provider validates the opt-in
policy and the endpoint (must be loopback), then returns a
``not_configured`` envelope. The provider deliberately imports
nothing from the ``ollama`` SDK; a future phase that does will
have to update the dependency boundary tests.
"""

from __future__ import annotations

from .config import provider_disabled_response
from .models import (
    ProviderMode,
    SkillLLMProviderConfig,
    SkillLLMProviderResult,
    SkillLLMRequest,
)
from .provider import evaluate_local_opt_in


def ollama_disabled_response(
    *, request: SkillLLMRequest, config: SkillLLMProviderConfig
) -> SkillLLMProviderResult:
    return provider_disabled_response(
        request_id=request.request_id,
        source_text=request.text,
        provider_mode=ProviderMode.OLLAMA.value,
        provider_name=config.provider_name or "ollama-provider",
        reason=(
            "ollama provider intentionally disabled in Phase 15B; "
            "a future phase must wire it up with explicit operator opt-in"
        ),
    )


class OllamaProvider:
    """Opt-in policy + endpoint check; never invokes Ollama."""

    def __init__(self) -> None:
        self.name = "ollama-provider"
        self.mode = ProviderMode.OLLAMA.value

    def propose(
        self,
        *,
        request: SkillLLMRequest,
        config: SkillLLMProviderConfig,
        allow_local_provider: bool,
    ) -> SkillLLMProviderResult:
        policy = evaluate_local_opt_in(
            request=request,
            config=config,
            allow_local_provider=allow_local_provider,
        )
        if policy is not None:
            return policy
        return ollama_disabled_response(request=request, config=config)
