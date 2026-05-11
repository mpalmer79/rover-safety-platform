"""Structural validation for proposals.

The validator only checks the shape of a proposal: required fields,
expected types, enum membership. It does NOT decide whether a
proposal is *safe* — that is the sanitizer's job — and it does NOT
decide whether it compiles — that is the Phase 14A compiler's job.
"""

from __future__ import annotations

from typing import Mapping

from .models import (
    CONFIDENCE_LABELS,
    MissionProposal,
    PROVIDER_MODES,
)
from .schema import PROPOSAL_REQUIRED_FIELDS


def _coerce_tuple(value) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if isinstance(value, (list, tuple)):
        return tuple(str(v) for v in value)
    return ()


def validate_proposal_dict(payload: Mapping) -> tuple[tuple[str, ...], MissionProposal | None]:
    """Validate a parsed JSON proposal.

    Returns ``(errors, proposal_or_none)``. ``proposal_or_none`` is
    ``None`` when ``errors`` is non-empty.
    """

    if not isinstance(payload, Mapping):
        return (("proposal must be a JSON object",), None)

    errors: list[str] = []
    for field in PROPOSAL_REQUIRED_FIELDS:
        if field not in payload:
            errors.append(f"missing required field: {field}")
    if errors:
        return (tuple(errors), None)

    provider_mode = str(payload.get("provider_mode") or "")
    if provider_mode not in PROVIDER_MODES:
        errors.append(
            f"provider_mode must be one of {PROVIDER_MODES}, got {provider_mode!r}"
        )

    confidence_label = str(payload.get("confidence_label") or "")
    if confidence_label not in CONFIDENCE_LABELS:
        errors.append(
            f"confidence_label must be one of {CONFIDENCE_LABELS}, got {confidence_label!r}"
        )

    proposal_id = str(payload.get("proposal_id") or "").strip()
    if not proposal_id:
        errors.append("proposal_id must be a non-empty string")

    source_text = str(payload.get("source_text") or "").strip()
    if not source_text:
        errors.append("source_text must be a non-empty string")

    if errors:
        return (tuple(errors), None)

    proposal = MissionProposal(
        proposal_id=proposal_id,
        source_text=source_text,
        provider_name=str(payload.get("provider_name") or ""),
        provider_mode=provider_mode,
        proposed_intent=str(payload.get("proposed_intent") or ""),
        proposed_location=str(payload.get("proposed_location") or ""),
        proposed_motion_style=str(payload.get("proposed_motion_style") or ""),
        proposed_constraints=_coerce_tuple(payload.get("proposed_constraints")),
        proposed_recovery_policy=str(payload.get("proposed_recovery_policy") or ""),
        confidence_label=confidence_label,
        known_uncertainties=_coerce_tuple(payload.get("known_uncertainties")),
        raw_response=str(payload.get("raw_response") or ""),
    )
    return ((), proposal)


def validate_proposal(proposal: MissionProposal) -> tuple[str, ...]:
    """Validate an already-constructed proposal value object."""

    errors: list[str] = []
    if not proposal.proposal_id.strip():
        errors.append("proposal_id must be non-empty")
    if proposal.provider_mode not in PROVIDER_MODES:
        errors.append(
            f"provider_mode must be one of {PROVIDER_MODES}, got {proposal.provider_mode!r}"
        )
    if proposal.confidence_label not in CONFIDENCE_LABELS:
        errors.append(
            f"confidence_label must be one of {CONFIDENCE_LABELS}"
        )
    if not proposal.source_text.strip():
        errors.append("source_text must be non-empty")
    return tuple(errors)
