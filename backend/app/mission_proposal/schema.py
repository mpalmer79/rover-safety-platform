"""JSON schema descriptors for proposals and audits.

The schemas are written in plain Python so the validator can run
without an external schema library. They are exposed for the rover
docs and for the validator CLI.
"""

from __future__ import annotations


PROPOSAL_REQUIRED_FIELDS: tuple[str, ...] = (
    "proposal_id",
    "source_text",
    "provider_name",
    "provider_mode",
    "proposed_intent",
    "proposed_location",
    "proposed_motion_style",
    "proposed_constraints",
    "proposed_recovery_policy",
    "confidence_label",
    "known_uncertainties",
    "raw_response",
)


def proposal_required_fields() -> tuple[str, ...]:
    return PROPOSAL_REQUIRED_FIELDS


def proposal_schema() -> dict:
    return {
        "title": "Mission proposal",
        "type": "object",
        "additionalProperties": False,
        "required": list(PROPOSAL_REQUIRED_FIELDS),
        "properties": {
            "proposal_id": {"type": "string"},
            "source_text": {"type": "string"},
            "provider_name": {"type": "string"},
            "provider_mode": {
                "type": "string",
                "enum": ["mock", "offline_fixture", "external_disabled"],
            },
            "proposed_intent": {"type": "string"},
            "proposed_location": {"type": "string"},
            "proposed_motion_style": {"type": "string"},
            "proposed_constraints": {
                "type": "array",
                "items": {"type": "string"},
            },
            "proposed_recovery_policy": {"type": "string"},
            "confidence_label": {
                "type": "string",
                "enum": ["low", "medium", "high", "overconfident"],
            },
            "known_uncertainties": {
                "type": "array",
                "items": {"type": "string"},
            },
            "raw_response": {"type": "string"},
        },
    }


def audit_schema() -> dict:
    return {
        "title": "Mission proposal audit",
        "type": "object",
        "required": [
            "proposal",
            "sanitizer_result",
            "compiler_input",
            "compiler_status",
            "final_outcome",
            "disclaimer",
            "generated_at_utc",
        ],
        "properties": {
            "proposal": proposal_schema(),
            "sanitizer_result": {
                "type": "object",
                "required": [
                    "status",
                    "accepted",
                    "sanitized_intent",
                    "blocked_phrases",
                    "diagnostics",
                ],
            },
            "compiler_input": {"type": "string"},
            "compiler_plan": {"type": ["object", "null"]},
            "compiler_status": {"type": "string"},
            "final_outcome": {"type": "string"},
            "disclaimer": {"type": "string"},
            "generated_at_utc": {"type": "string"},
        },
    }
