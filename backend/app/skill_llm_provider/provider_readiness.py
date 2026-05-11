"""Provider readiness checks.

The Phase 19 readiness check answers: "If the operator flips the
opt-in flag, will the provider be ABLE to run?" Without ever
opening a socket. The check is honest: a misconfigured provider
returns ``status = NOT_CONFIGURED`` with an explanation; a remote
endpoint returns ``status = REJECTED_ENDPOINT`` so the operator
sees why the local-only policy refuses to run.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from .models import (
    PROVIDER_MODES,
    ProviderMode,
    SkillLLMProviderConfig,
)


READINESS_DISABLED: str = "disabled"
READINESS_READY: str = "ready"
READINESS_NOT_CONFIGURED: str = "not_configured"
READINESS_REJECTED_ENDPOINT: str = "rejected_endpoint"
READINESS_REQUIRES_OPT_IN: str = "requires_opt_in"


# A small allow-list of endpoints that count as "local-only". Tests
# rely on this list staying explicit + verifiable.
_LOCAL_HOSTS: tuple[str, ...] = (
    "127.0.0.1",
    "localhost",
    "::1",
    "host.docker.internal",
)


@dataclass(frozen=True)
class ProviderReadiness:
    """Readiness summary for one provider configuration."""

    provider_mode: str
    provider_name: str
    model_name: str
    endpoint: str
    enabled: bool
    endpoint_is_local_only: bool
    status: str
    notes: tuple[str, ...] = ()
    execution_allowed: bool = False


def _is_local_only(endpoint: str) -> bool:
    """Return True iff the endpoint hostname is in the local allow-list."""

    if not endpoint:
        # An empty endpoint is fine for ``DISABLED`` / ``FIXTURE``.
        return True
    parsed = urlparse(endpoint)
    host = parsed.hostname or ""
    return host.lower() in _LOCAL_HOSTS


def check_provider_readiness(config: SkillLLMProviderConfig) -> ProviderReadiness:
    """Return a deterministic readiness summary for ``config``.

    The function never opens a socket and never invokes the
    provider. It inspects the configuration and reports what would
    happen if the operator flipped the opt-in flag.
    """

    notes: list[str] = []
    mode = config.mode

    if mode not in PROVIDER_MODES:
        return ProviderReadiness(
            provider_mode=mode,
            provider_name=config.provider_name,
            model_name=config.model_name,
            endpoint=config.endpoint,
            enabled=False,
            endpoint_is_local_only=False,
            status=READINESS_NOT_CONFIGURED,
            notes=(f"unknown provider_mode {mode!r}",),
        )

    if mode == ProviderMode.DISABLED.value:
        return ProviderReadiness(
            provider_mode=mode,
            provider_name=config.provider_name,
            model_name=config.model_name,
            endpoint=config.endpoint,
            enabled=False,
            endpoint_is_local_only=True,
            status=READINESS_DISABLED,
            notes=("provider is disabled by configuration",),
        )

    if mode == ProviderMode.FIXTURE.value:
        ready = bool(config.provider_name)
        if not ready:
            notes.append("fixture provider name missing")
        return ProviderReadiness(
            provider_mode=mode,
            provider_name=config.provider_name,
            model_name=config.model_name,
            endpoint=config.endpoint,
            enabled=True,
            endpoint_is_local_only=True,
            status=READINESS_READY if ready else READINESS_NOT_CONFIGURED,
            notes=tuple(notes),
            execution_allowed=ready,
        )

    # Local providers: ``local_http`` / ``ollama`` / ``llama_cpp``.
    local_only = _is_local_only(config.endpoint)
    if not local_only:
        notes.append(
            f"endpoint {config.endpoint!r} is not in the local-only allow-list"
        )
        return ProviderReadiness(
            provider_mode=mode,
            provider_name=config.provider_name,
            model_name=config.model_name,
            endpoint=config.endpoint,
            enabled=config.enabled,
            endpoint_is_local_only=False,
            status=READINESS_REJECTED_ENDPOINT,
            notes=tuple(notes),
            execution_allowed=False,
        )

    if not config.enabled:
        notes.append("provider gated behind requires_opt_in")
        return ProviderReadiness(
            provider_mode=mode,
            provider_name=config.provider_name,
            model_name=config.model_name,
            endpoint=config.endpoint,
            enabled=False,
            endpoint_is_local_only=True,
            status=READINESS_REQUIRES_OPT_IN,
            notes=tuple(notes),
            execution_allowed=False,
        )

    if not config.model_name:
        notes.append("model_name is empty")
        return ProviderReadiness(
            provider_mode=mode,
            provider_name=config.provider_name,
            model_name=config.model_name,
            endpoint=config.endpoint,
            enabled=True,
            endpoint_is_local_only=True,
            status=READINESS_NOT_CONFIGURED,
            notes=tuple(notes),
            execution_allowed=False,
        )

    return ProviderReadiness(
        provider_mode=mode,
        provider_name=config.provider_name,
        model_name=config.model_name,
        endpoint=config.endpoint,
        enabled=True,
        endpoint_is_local_only=True,
        status=READINESS_READY,
        notes=tuple(notes),
        execution_allowed=True,
    )


def readiness_to_dict(readiness: ProviderReadiness) -> dict[str, object]:
    return {
        "provider_mode": readiness.provider_mode,
        "provider_name": readiness.provider_name,
        "model_name": readiness.model_name,
        "endpoint": readiness.endpoint,
        "enabled": readiness.enabled,
        "endpoint_is_local_only": readiness.endpoint_is_local_only,
        "execution_allowed": readiness.execution_allowed,
        "status": readiness.status,
        "notes": list(readiness.notes),
    }


__all__ = [
    "READINESS_DISABLED",
    "READINESS_NOT_CONFIGURED",
    "READINESS_READY",
    "READINESS_REJECTED_ENDPOINT",
    "READINESS_REQUIRES_OPT_IN",
    "ProviderReadiness",
    "check_provider_readiness",
    "readiness_to_dict",
]
