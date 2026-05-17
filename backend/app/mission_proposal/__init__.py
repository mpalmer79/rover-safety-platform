"""External mission proposal seam: providers, sanitizer, compiler adapter."""

from __future__ import annotations

from .adapter import (
    AdapterResult,
    adapt_proposal_to_compiler_input,
    run_adapter_pipeline,
)
from .audit import (
    build_audit,
    write_audit_bundle,
)
from .mock_provider import (
    MOCK_FIXTURES,
    MockProposalProvider,
    list_mock_fixtures,
)
from .models import (
    ADAPTER_OUTCOME_COMPILED_REQUIRES_REVIEW,
    ADAPTER_OUTCOME_COMPILED_VALIDATION_PASSED,
    ADAPTER_OUTCOME_REJECTED_BY_COMPILER,
    ADAPTER_OUTCOME_REJECTED_BY_SANITIZER,
    CONFIDENCE_HIGH,
    CONFIDENCE_OVERCONFIDENT,
    MISSION_PROPOSAL_DISCLAIMER,
    MissionProposal,
    PROPOSAL_LAYER_VERSION,
    PROVIDER_MODES,
    PROVIDER_MODE_EXTERNAL_DISABLED,
    PROVIDER_MODE_MOCK,
    PROVIDER_MODE_OFFLINE_FIXTURE,
    SANITIZER_STATUS_ACCEPTED,
    SANITIZER_STATUS_REJECTED,
    SanitizerResult,
)
from .provider import (
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
    audit_schema,
    proposal_required_fields,
    proposal_schema,
)
from .validator import (
    validate_proposal,
    validate_proposal_dict,
)

__all__ = [
    "ADAPTER_OUTCOME_COMPILED_REQUIRES_REVIEW",
    "ADAPTER_OUTCOME_COMPILED_VALIDATION_PASSED",
    "ADAPTER_OUTCOME_REJECTED_BY_COMPILER",
    "ADAPTER_OUTCOME_REJECTED_BY_SANITIZER",
    "AdapterResult",
    "CONFIDENCE_HIGH",
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
    "ProposalProviderError",
    "SANITIZER_STATUS_ACCEPTED",
    "SANITIZER_STATUS_REJECTED",
    "SanitizerResult",
    "adapt_proposal_to_compiler_input",
    "audit_schema",
    "build_audit",
    "external_provider_disabled_response",
    "list_mock_fixtures",
    "proposal_required_fields",
    "proposal_schema",
    "resolve_provider",
    "run_adapter_pipeline",
    "sanitize_proposal",
    "validate_proposal",
    "validate_proposal_dict",
    "write_audit_bundle",
    "write_audit_files",
]
