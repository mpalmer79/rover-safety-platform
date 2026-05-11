"""Dataclasses, status constants, and the verbatim disclaimer.

The platform is **not safety-certified**. The proposal layer is
read-only with respect to robot motion. Nothing in this module
publishes commands, contacts an LLM API, or authorises movement.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


PROPOSAL_LAYER_VERSION: str = "phase14b-1"

MISSION_PROPOSAL_DISCLAIMER: str = (
    "This mission proposal is a planning artifact. It does not "
    "represent autonomous execution, safety certification, or "
    "regulatory approval."
)


# ----------------------------------------------------------------------
# Provider modes.
# ----------------------------------------------------------------------

PROVIDER_MODE_MOCK: str = "mock"
PROVIDER_MODE_OFFLINE_FIXTURE: str = "offline_fixture"
PROVIDER_MODE_EXTERNAL_DISABLED: str = "external_disabled"

PROVIDER_MODES: tuple[str, ...] = (
    PROVIDER_MODE_MOCK,
    PROVIDER_MODE_OFFLINE_FIXTURE,
    PROVIDER_MODE_EXTERNAL_DISABLED,
)


# ----------------------------------------------------------------------
# Confidence labels (chosen so an "overconfident" proposal is still
# expected to fail the sanitizer / compiler when it claims certainty
# about an unsafe action).
# ----------------------------------------------------------------------

CONFIDENCE_LOW: str = "low"
CONFIDENCE_MEDIUM: str = "medium"
CONFIDENCE_HIGH: str = "high"
CONFIDENCE_OVERCONFIDENT: str = "overconfident"

CONFIDENCE_LABELS: tuple[str, ...] = (
    CONFIDENCE_LOW,
    CONFIDENCE_MEDIUM,
    CONFIDENCE_HIGH,
    CONFIDENCE_OVERCONFIDENT,
)


# ----------------------------------------------------------------------
# Sanitizer outcome vocabulary.
# ----------------------------------------------------------------------

SANITIZER_STATUS_ACCEPTED: str = "accepted"
SANITIZER_STATUS_REJECTED: str = "rejected"

SANITIZER_STATUSES: tuple[str, ...] = (
    SANITIZER_STATUS_ACCEPTED,
    SANITIZER_STATUS_REJECTED,
)


# ----------------------------------------------------------------------
# Adapter outcome vocabulary.
# ----------------------------------------------------------------------

ADAPTER_OUTCOME_ACCEPTED_BY_PROVIDER: str = "proposal_accepted_by_provider"
ADAPTER_OUTCOME_REJECTED_BY_SANITIZER: str = "proposal_rejected_by_sanitizer"
ADAPTER_OUTCOME_REJECTED_BY_COMPILER: str = "proposal_rejected_by_compiler"
ADAPTER_OUTCOME_COMPILED_REQUIRES_REVIEW: str = "proposal_compiled_requires_review"
ADAPTER_OUTCOME_COMPILED_VALIDATION_PASSED: str = "proposal_compiled_validation_passed"

ADAPTER_OUTCOMES: tuple[str, ...] = (
    ADAPTER_OUTCOME_ACCEPTED_BY_PROVIDER,
    ADAPTER_OUTCOME_REJECTED_BY_SANITIZER,
    ADAPTER_OUTCOME_REJECTED_BY_COMPILER,
    ADAPTER_OUTCOME_COMPILED_REQUIRES_REVIEW,
    ADAPTER_OUTCOME_COMPILED_VALIDATION_PASSED,
)


# ----------------------------------------------------------------------
# Models.
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class MissionProposal:
    """One proposal emitted by a provider.

    All fields are required (see ``schema.proposal_required_fields``).
    Anything the layer downstream might need must be embedded here;
    the sanitizer, adapter, audit and reporter never re-call the
    provider.
    """

    proposal_id: str
    source_text: str
    provider_name: str
    provider_mode: str
    proposed_intent: str
    proposed_location: str
    proposed_motion_style: str
    proposed_constraints: tuple[str, ...]
    proposed_recovery_policy: str
    confidence_label: str
    known_uncertainties: tuple[str, ...]
    raw_response: str


@dataclass(frozen=True)
class SanitizerDiagnostic:
    code: str
    severity: str  # "info" | "warning" | "rejection"
    message: str
    matched_phrase: str = ""


@dataclass(frozen=True)
class SanitizerResult:
    status: str
    accepted: bool
    sanitized_intent: str
    blocked_phrases: tuple[str, ...]
    diagnostics: tuple[SanitizerDiagnostic, ...]
    notes: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ProposalAudit:
    proposal: MissionProposal
    sanitizer_result: SanitizerResult
    compiler_input: str
    compiler_plan_json: Mapping[str, object] | None
    compiler_status: str  # one of natural_language_mission.COMPILE_STATUS_* or ""
    final_outcome: str
    disclaimer: str
    generated_at_utc: str
