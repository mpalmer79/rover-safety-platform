"""Local HTTP provider.

In Phase 15B this provider validates configuration + the opt-in
policy and returns a ``not_configured`` envelope. It does **not**
open a network socket, even to a loopback host. A future phase
that wants a real local HTTP call must update this provider AND
the corresponding tests.
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


def local_http_disabled_response(
    *, request: SkillLLMRequest, config: SkillLLMProviderConfig
) -> SkillLLMProviderResult:
    return provider_disabled_response(
        request_id=request.request_id,
        source_text=request.text,
        provider_mode=ProviderMode.LOCAL_HTTP.value,
        provider_name=config.provider_name or "local-http-provider",
        reason=(
            "local_http provider is policy-checked but does not perform "
            "a network call in Phase 15B"
        ),
    )


class LocalHttpProvider:
    """Opt-in policy + endpoint check; never opens a network socket."""

    def __init__(self) -> None:
        self.name = "local-http-provider"
        self.mode = ProviderMode.LOCAL_HTTP.value

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
        # Even when the operator has fully opted in, Phase 15B does
        # not make a network call. The envelope below is the
        # operator-honest "policy passed, runtime disabled" record.
        return local_http_disabled_response(request=request, config=config)
