"""llama.cpp provider stub.

Phase 15B does not execute llama.cpp. The provider validates the
opt-in policy and the endpoint, then returns a ``not_configured``
envelope. No ``llama_cpp`` import occurs anywhere in the package.
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


def llama_cpp_disabled_response(
    *, request: SkillLLMRequest, config: SkillLLMProviderConfig
) -> SkillLLMProviderResult:
    return provider_disabled_response(
        request_id=request.request_id,
        source_text=request.text,
        provider_mode=ProviderMode.LLAMA_CPP.value,
        provider_name=config.provider_name or "llama-cpp-provider",
        reason="llama.cpp execution intentionally disabled in Phase 15B",
    )


class LlamaCppProvider:
    """Opt-in policy + endpoint check; never spawns llama.cpp."""

    def __init__(self) -> None:
        self.name = "llama-cpp-provider"
        self.mode = ProviderMode.LLAMA_CPP.value

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
        return llama_cpp_disabled_response(request=request, config=config)
