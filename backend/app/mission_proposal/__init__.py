"""Phase 14B: pluggable LLM mission proposal layer (offline, mock-only).

The platform is **not safety-certified**. The proposal layer is an
offline seam that lets a future LLM propose a candidate mission
*description*. The deterministic mission compiler (Phase 14A) and
the runtime safety supervisor remain authoritative; this package
never authorises motion, never publishes actuator commands, and
never calls a real LLM API.

Public flow:

    natural-language request
      -> ProposalProvider.propose
      -> MissionProposal (raw, untrusted)
      -> sanitize_proposal
      -> SanitizerResult (accepted / rejected)
      -> adapt_proposal_to_compiler_input  (Phase 14A entry text)
      -> compile_intent (Phase 14A)
      -> ProposalAudit (read-only artefact bundle)
"""

from __future__ import annotations

from .adapter import (
    AdapterOutcome,
    AdapterResult,
    adapt_proposal_to_compiler_input,
    run_adapter_pipeline,
)
from .audit import build_audit, render_audit_markdown, write_audit_bundle
from .mock_provider import (
    MOCK_FIXTURES,
    MockProposalProvider,
    list_mock_fixtures,
)
from .models import (
    ADAPTER_OUTCOMES,
    ADAPTER_OUTCOME_ACCEPTED_BY_PROVIDER,
    ADAPTER_OUTCOME_COMPILED_REQUIRES_REVIEW,
    ADAPTER_OUTCOME_COMPILED_VALIDATION_PASSED,
    ADAPTER_OUTCOME_REJECTED_BY_COMPILER,
    ADAPTER_OUTCOME_REJECTED_BY_SANITIZER,
    CONFIDENCE_HIGH,
    CONFIDENCE_LOW,
    CONFIDENCE_MEDIUM,
    CONFIDENCE_OVERCONFIDENT,
    CONFIDENCE_LABELS,
    MISSION_PROPOSAL_DISCLAIMER,
    PROPOSAL_LAYER_VERSION,
    PROVIDER_MODES,
    PROVIDER_MODE_EXTERNAL_DISABLED,
    PROVIDER_MODE_MOCK,
    PROVIDER_MODE_OFFLINE_FIXTURE,
    SANITIZER_STATUSES,
    SANITIZER_STATUS_ACCEPTED,
    SANITIZER_STATUS_REJECTED,
    SanitizerDiagnostic,
    SanitizerResult,
    MissionProposal,
    ProposalAudit,
)
from .provider import (
    ProposalProvider,
    ProposalProviderError,
    external_provider_disabled_response,
    resolve_provider,
)
from .reporter import write_audit_files
from .sanitizer import (
    FORBIDDEN_PHRASES,
    sanitize_proposal,
)
from .schema import (
    proposal_required_fields,
    proposal_schema,
    audit_schema,
)
from .validator import (
    validate_proposal,
    validate_proposal_dict,
)


__all__ = [
    "ADAPTER_OUTCOMES",
    "ADAPTER_OUTCOME_ACCEPTED_BY_PROVIDER",
    "ADAPTER_OUTCOME_COMPILED_REQUIRES_REVIEW",
    "ADAPTER_OUTCOME_COMPILED_VALIDATION_PASSED",
    "ADAPTER_OUTCOME_REJECTED_BY_COMPILER",
    "ADAPTER_OUTCOME_REJECTED_BY_SANITIZER",
    "AdapterOutcome",
    "AdapterResult",
    "CONFIDENCE_HIGH",
    "CONFIDENCE_LABELS",
    "CONFIDENCE_LOW",
    "CONFIDENCE_MEDIUM",
    "CONFIDENCE_OVERCONFIDENT",
    "FORBIDDEN_PHRASES",
    "MISSION_PROPOSAL_DISCLAIMER",
    "MOCK_FIXTURES",
    "MissionProposal",
    "MockProposalProvider",
    "PROPOSAL_LAYER_VERSION",
    "PROVIDER_MODES",
    "PROVIDER_MODE_EXTERNAL_DISABLED",
    "PROVIDER_MODE_MOCK",
    "PROVIDER_MODE_OFFLINE_FIXTURE",
    "ProposalAudit",
    "ProposalProvider",
    "ProposalProviderError",
    "SANITIZER_STATUSES",
    "SANITIZER_STATUS_ACCEPTED",
    "SANITIZER_STATUS_REJECTED",
    "SanitizerDiagnostic",
    "SanitizerResult",
    "adapt_proposal_to_compiler_input",
    "audit_schema",
    "build_audit",
    "external_provider_disabled_response",
    "list_mock_fixtures",
    "proposal_required_fields",
    "proposal_schema",
    "render_audit_markdown",
    "resolve_provider",
    "run_adapter_pipeline",
    "sanitize_proposal",
    "validate_proposal",
    "validate_proposal_dict",
    "write_audit_bundle",
    "write_audit_files",
]
