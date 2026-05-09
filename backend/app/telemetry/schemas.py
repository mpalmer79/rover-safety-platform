"""Schema validation for emitted events.

The schema check is intentionally explicit. We do not depend on Pydantic
or jsonschema; this keeps the core dependency-free and the validator
auditable in a single short file.
"""

from __future__ import annotations

from typing import Any

from app.domain.enums import EventCategory, EventSeverity


EVENT_REQUIRED_FIELDS: tuple[str, ...] = (
    "timestamp",
    "run_id",
    "scenario_id",
    "event_id",
    "event_type",
    "severity",
    "subsystem",
    "node",
    "lifecycle_state",
    "safety_state",
    "source_topic",
    "confidence_score",
    "requested_motion",
    "final_motion",
    "reason_code",
    "message",
)

EVENT_OPTIONAL_FIELDS: tuple[str, ...] = (
    "sim_time_ns",
    "correlation_id",
    "parent_event_id",
    "tags",
    "attributes",
)

ALLOWED_EVENT_CATEGORIES: frozenset[str] = frozenset(c.value for c in EventCategory)
ALLOWED_SEVERITIES: frozenset[str] = frozenset(s.value for s in EventSeverity)


class EventSchemaError(ValueError):
    """Raised when a serialized event does not conform to the schema."""


def validate_event_dict(payload: dict[str, Any]) -> None:
    """Validate a serialized event payload.

    Raises :class:`EventSchemaError` with a precise message for the first
    violation encountered. Designed for use in CI replay validators.
    """

    if not isinstance(payload, dict):
        raise EventSchemaError(f"event must be a dict, got {type(payload).__name__}")

    for field in EVENT_REQUIRED_FIELDS:
        if field not in payload:
            raise EventSchemaError(f"event missing required field: {field!r}")

    severity = payload.get("severity")
    if severity not in ALLOWED_SEVERITIES:
        raise EventSchemaError(f"unknown severity: {severity!r}")

    event_type = payload.get("event_type", "")
    if not isinstance(event_type, str) or "." not in event_type:
        raise EventSchemaError(f"event_type must be dotted, got {event_type!r}")
    category = event_type.split(".", 1)[0]
    if category not in ALLOWED_EVENT_CATEGORIES:
        raise EventSchemaError(f"unknown event category: {category!r}")

    confidence = payload.get("confidence_score")
    if confidence is not None and not (
        isinstance(confidence, (int, float)) and 0.0 <= float(confidence) <= 1.0
    ):
        raise EventSchemaError(
            f"confidence_score must be in [0.0, 1.0] when set, got {confidence!r}"
        )

    for required_str in ("run_id", "scenario_id", "event_id", "subsystem", "node", "reason_code", "message"):
        value = payload.get(required_str)
        if not isinstance(value, str) or not value:
            raise EventSchemaError(f"{required_str!r} must be a non-empty string")
