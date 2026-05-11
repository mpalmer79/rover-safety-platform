"""Adapter that funnels sanitized proposals into the Phase 14A compiler.

The adapter never executes a proposal. It calls the deterministic
mission compiler with sanitized text and bundles the result into an
:class:`AdapterResult` so the audit layer has everything it needs.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping, Optional

from app.natural_language_mission import (
    COMPILE_STATUS_AMBIGUOUS,
    COMPILE_STATUS_OK,
    COMPILE_STATUS_OK_WITH_WARNINGS,
    COMPILE_STATUS_REJECTED,
    compile_intent,
    plan_to_dict,
)

from .models import (
    ADAPTER_OUTCOME_ACCEPTED_BY_PROVIDER,
    ADAPTER_OUTCOME_COMPILED_REQUIRES_REVIEW,
    ADAPTER_OUTCOME_COMPILED_VALIDATION_PASSED,
    ADAPTER_OUTCOME_REJECTED_BY_COMPILER,
    ADAPTER_OUTCOME_REJECTED_BY_SANITIZER,
    MissionProposal,
    SanitizerResult,
)
from .sanitizer import sanitize_proposal


# Type alias for adapter outcome strings; kept as ``str`` so dataclass
# default factories don't need a custom enum.
AdapterOutcome = str


@dataclass(frozen=True)
class AdapterResult:
    proposal: MissionProposal
    sanitizer_result: SanitizerResult
    compiler_input: str
    compiler_status: str
    compiler_plan: Optional[Mapping[str, object]]
    final_outcome: AdapterOutcome


def adapt_proposal_to_compiler_input(
    proposal: MissionProposal, sanitizer_result: SanitizerResult
) -> str:
    """Return the text the compiler should receive.

    Returns an empty string when the sanitizer rejected the proposal;
    the compiler is never run on rejected text.
    """

    if not sanitizer_result.accepted:
        return ""
    return sanitizer_result.sanitized_intent


def _classify_compiler_status(status: str) -> AdapterOutcome:
    if status in (COMPILE_STATUS_OK, COMPILE_STATUS_OK_WITH_WARNINGS):
        return ADAPTER_OUTCOME_COMPILED_VALIDATION_PASSED
    if status == COMPILE_STATUS_AMBIGUOUS:
        return ADAPTER_OUTCOME_COMPILED_REQUIRES_REVIEW
    if status == COMPILE_STATUS_REJECTED:
        return ADAPTER_OUTCOME_REJECTED_BY_COMPILER
    return ADAPTER_OUTCOME_ACCEPTED_BY_PROVIDER


def run_adapter_pipeline(
    proposal: MissionProposal,
    *,
    generated_at_utc: str | None = None,
) -> AdapterResult:
    """Run sanitize -> compile and return a structured result.

    The Phase 14A compiler is the authority on whether the resulting
    mission is acceptable. The adapter only routes data and labels
    the final outcome.
    """

    timestamp = generated_at_utc or datetime.now(timezone.utc).replace(
        microsecond=0
    ).isoformat()

    sanitizer_result = sanitize_proposal(proposal)
    compiler_input = adapt_proposal_to_compiler_input(proposal, sanitizer_result)

    if not sanitizer_result.accepted:
        return AdapterResult(
            proposal=proposal,
            sanitizer_result=sanitizer_result,
            compiler_input="",
            compiler_status="",
            compiler_plan=None,
            final_outcome=ADAPTER_OUTCOME_REJECTED_BY_SANITIZER,
        )

    plan = compile_intent(
        compiler_input,
        plan_id=f"proposal-{proposal.proposal_id}",
        generated_at_utc=timestamp,
    )
    plan_dict = plan_to_dict(plan)
    outcome = _classify_compiler_status(plan.status)

    return AdapterResult(
        proposal=proposal,
        sanitizer_result=sanitizer_result,
        compiler_input=compiler_input,
        compiler_status=plan.status,
        compiler_plan=plan_dict,
        final_outcome=outcome,
    )
