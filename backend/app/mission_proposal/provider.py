"""Abstract proposal-provider interface and the external-disabled shim.

External LLM providers are intentionally not implemented in Phase
14B. The :func:`resolve_provider` factory selects either the mock
provider or returns the deterministic "external disabled" record.

Adding a real external provider in a future phase MUST happen
through this seam so the sanitizer and validator paths remain
unchanged.
"""

from __future__ import annotations

from typing import Mapping, Protocol

from .models import (
    MissionProposal,
    PROVIDER_MODE_EXTERNAL_DISABLED,
    PROVIDER_MODE_MOCK,
    PROVIDER_MODE_OFFLINE_FIXTURE,
    PROVIDER_MODES,
)


class ProposalProviderError(RuntimeError):
    pass


class ProposalProvider(Protocol):
    """Minimal interface a provider must implement.

    Implementations MUST be deterministic, offline, and side-effect
    free. They must not call out to the network, must not write to
    disk except via the audit reporter, and must return a single
    :class:`MissionProposal` value per call.
    """

    name: str
    mode: str

    def propose(
        self,
        *,
        source_text: str,
        proposal_id: str,
        options: Mapping[str, object] | None = None,
    ) -> MissionProposal: ...


def external_provider_disabled_response(
    *,
    source_text: str,
    proposal_id: str,
    provider_name: str = "external-disabled-provider",
) -> dict:
    """Return the canonical 'external disabled' response.

    The CLIs and tests use this when ``--provider external`` (or any
    other unsupported mode) is requested. Callers receive a JSON
    payload rather than a raw ``MissionProposal``; this keeps the
    "disabled" message explicit and impossible to mistake for an
    accepted proposal.
    """

    return {
        "status": "not_configured",
        "reason": (
            "external LLM providers are intentionally disabled in Phase 14B"
        ),
        "proposal_id": proposal_id,
        "source_text": source_text,
        "provider_name": provider_name,
        "provider_mode": PROVIDER_MODE_EXTERNAL_DISABLED,
    }


def resolve_provider(mode: str) -> "ProposalProvider | None":
    """Resolve a provider by mode.

    Returns the mock provider for ``mock`` and ``offline_fixture``;
    returns ``None`` for ``external_disabled`` (callers should use
    :func:`external_provider_disabled_response`). Any other mode
    raises :class:`ProposalProviderError`.
    """

    from .mock_provider import MockProposalProvider  # local to avoid cycle

    if mode == PROVIDER_MODE_MOCK:
        return MockProposalProvider(use_fixtures=False)
    if mode == PROVIDER_MODE_OFFLINE_FIXTURE:
        return MockProposalProvider(use_fixtures=True)
    if mode == PROVIDER_MODE_EXTERNAL_DISABLED:
        return None
    raise ProposalProviderError(
        f"unsupported provider mode {mode!r}; expected one of {PROVIDER_MODES}"
    )
