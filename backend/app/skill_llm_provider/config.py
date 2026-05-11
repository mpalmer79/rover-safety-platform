"""Provider configuration loader + endpoint safety helpers.

Two key safety rules live here:

1. ``DEFAULT_PROVIDER_MODE`` is :data:`ProviderMode.DISABLED`. The
   ``disabled`` mode never returns a candidate.
2. Any URL that is not a documented loopback host is rejected, even
   when the operator passes ``--allow-local-provider``. The list of
   accepted hosts is intentionally narrow: ``localhost``,
   ``127.0.0.1``, ``::1``. Cloud SaaS endpoints are forbidden.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Mapping
from urllib.parse import urlparse

from .models import (
    PROVIDER_MODES,
    ProviderMode,
    ProviderStatus,
    SkillLLMProviderConfig,
    SkillLLMProviderResult,
)


DEFAULT_PROVIDER_MODE: str = ProviderMode.DISABLED.value
KNOWN_PROVIDER_MODES: tuple[str, ...] = PROVIDER_MODES

_LOOPBACK_HOSTS: frozenset[str] = frozenset(
    {"localhost", "127.0.0.1", "::1", "0.0.0.0"}
)

_KNOWN_CLOUD_HOST_FRAGMENTS: tuple[str, ...] = (
    "openai.com",
    "anthropic.com",
    "cohere.ai",
    "googleapis.com",
    "googlecloud.com",
    "vertex",
    "replicate.com",
    "huggingface.co",
    "perplexity.ai",
    "mistral.ai",
    "groq.com",
    "fireworks.ai",
    "together.ai",
)


def is_loopback_url(url: str) -> bool:
    """Return True if ``url`` points at a documented loopback host."""

    if not isinstance(url, str) or not url.strip():
        return False
    parsed = urlparse(url)
    if parsed.scheme not in {"http"}:
        # Local providers are HTTP only. HTTPS implies a remote host
        # in this project's context, so we reject it.
        return False
    host = (parsed.hostname or "").lower()
    if not host:
        return False
    if host in _LOOPBACK_HOSTS:
        return True
    # Belt-and-braces: explicitly reject anything that looks cloud-y.
    for fragment in _KNOWN_CLOUD_HOST_FRAGMENTS:
        if fragment in host:
            return False
    return False


def require_local_endpoint(url: str) -> tuple[bool, str]:
    """Return ``(ok, reason)`` for an endpoint policy check.

    The reason is empty when ``ok`` is True; otherwise it explains
    the policy violation so a downstream audit can record it.
    """

    if not url:
        return False, "no endpoint configured"
    if is_loopback_url(url):
        return True, ""
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme == "https":
        return False, f"https endpoint is not permitted in Phase 15B: {host or '?'}"
    if not host:
        return False, "endpoint URL is malformed"
    for fragment in _KNOWN_CLOUD_HOST_FRAGMENTS:
        if fragment in host:
            return False, f"cloud-hosted endpoint is forbidden: {host}"
    return False, (
        f"only loopback endpoints are accepted (localhost / 127.0.0.1 / ::1); got {host}"
    )


def parse_provider_config(payload: Mapping) -> SkillLLMProviderConfig:
    if not isinstance(payload, Mapping):
        raise ValueError("provider config must be a JSON object")
    mode = str(payload.get("mode", DEFAULT_PROVIDER_MODE)).strip()
    if mode not in PROVIDER_MODES:
        raise ValueError(
            f"unsupported provider mode {mode!r}; expected one of {PROVIDER_MODES}"
        )
    enabled = bool(payload.get("enabled", False))
    provider_name = str(payload.get("provider_name", mode))
    model_name = str(payload.get("model_name", ""))
    endpoint = str(payload.get("endpoint", "")).strip()
    extra = dict(payload.get("extra") or {})
    notes_raw = payload.get("notes") or ()
    if isinstance(notes_raw, str):
        notes = (notes_raw,)
    else:
        notes = tuple(str(n) for n in notes_raw)
    return SkillLLMProviderConfig(
        mode=mode,
        enabled=enabled,
        provider_name=provider_name,
        model_name=model_name,
        endpoint=endpoint,
        extra=extra,
        notes=notes,
    )


def load_provider_config(path: Path) -> SkillLLMProviderConfig:
    return parse_provider_config(
        json.loads(Path(path).read_text(encoding="utf-8"))
    )


def config_to_dict(config: SkillLLMProviderConfig) -> dict:
    return {
        "mode": config.mode,
        "enabled": config.enabled,
        "provider_name": config.provider_name,
        "model_name": config.model_name,
        "endpoint": config.endpoint,
        "extra": dict(config.extra),
        "notes": list(config.notes),
    }


def provider_disabled_response(
    *,
    request_id: str,
    source_text: str,
    provider_mode: str,
    provider_name: str = "",
    reason: str = "",
) -> SkillLLMProviderResult:
    """Construct the canonical ``not_configured`` provider envelope."""

    default_reason = "local LLM provider disabled by default"
    return SkillLLMProviderResult(
        status=ProviderStatus.NOT_CONFIGURED.value,
        provider_mode=provider_mode,
        provider_name=provider_name or f"{provider_mode}-provider",
        model_name="",
        reason=reason or default_reason,
        payload={"request_id": request_id, "source_text": source_text},
    )
