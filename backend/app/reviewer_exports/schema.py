"""JSON Schemas for the reviewer-export tables.

Every table has a corresponding schema. Schemas are intentionally
narrow: they list the required field names + their types and pin
known enum values. Reviewers can read the schemas directly without
running the platform.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.reviewer_exports.models import (
    ALL_TABLES,
    TABLE_DRIFT_FINDINGS,
    TABLE_FIELDS,
    TABLE_GATE_HISTORY,
    TABLE_INCIDENT_INDEX,
    TABLE_PROGRAMME_HEALTH,
    TABLE_REPLAY_QUALITY,
    TABLE_REQUIREMENT_COVERAGE,
    TABLE_SUBSYSTEM_RISK,
    TABLE_TREND_SERIES,
)


_SEVERITY_VALUES: tuple[str, ...] = (
    "informational",
    "warning",
    "regression",
    "critical_regression",
)


_STRING_FIELDS_DEFAULT_NULLABLE: tuple[str, ...] = (
    "triggering_artifact",
    "evidence_origin",
    "known_limitation",
    "evidence_origin_mix",
    "history_status",
    "last_transition",
    "first_fault",
    "terminal_safety_state",
    "replay_integrity_status",
    "report_path",
    "run_id",
    "scenario_id",
    "review_completion_status",
    "evidence_status",
    "title",
    "status",
    "coverage_status",
)


def build_schema(table: str) -> dict:
    """Return the JSON Schema for the given table."""

    fields = TABLE_FIELDS[table]
    properties: dict[str, dict] = {}
    required: list[str] = []
    for field in fields:
        properties[field] = _property_schema(table, field)
        # Every field is required by name; nullability is encoded via
        # ``type: ["string", "null"]`` etc.
        required.append(field)
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": f"reviewer-export/{table}",
        "type": "object",
        "additionalProperties": False,
        "required": required,
        "properties": properties,
    }


def write_schema(table: str, *, path: Path) -> Path:
    schema = build_schema(table)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(schema, indent=2, sort_keys=True), encoding="utf-8")
    return path


def write_all_schemas(*, schemas_dir: Path) -> dict[str, Path]:
    schemas_dir.mkdir(parents=True, exist_ok=True)
    out: dict[str, Path] = {}
    for table in ALL_TABLES:
        path = schemas_dir / f"{table}.schema.json"
        out[table] = write_schema(table, path=path)
    return out


# ---------------------------------------------------------------------------
# Per-field type policy.
# ---------------------------------------------------------------------------


def _property_schema(table: str, field: str) -> dict:
    if field == "causality_claimed":
        return {"type": "boolean", "const": False}
    if field in {"row_count", "count"}:
        return {"type": "integer", "minimum": 0}
    if field in {"static_only", "missing_bag"}:
        return {"type": "boolean"}
    if field in {"score"}:
        return {"type": ["integer", "null"]}
    if field in {"sample_count", "risk_frequency", "warning_count", "failure_count", "critical_count"}:
        return {"type": "integer", "minimum": 0}
    if field in {"latest_value", "baseline_value", "delta", "current_value"}:
        return {"type": ["number", "string", "null"]}
    if field == "severity":
        return {"type": "string", "enum": list(_SEVERITY_VALUES)}
    if field == "trend_category":
        return {
            "type": "string",
            "enum": [
                "improving",
                "stable",
                "degrading",
                "volatile",
                "insufficient_history",
            ],
        }
    if field == "volatility":
        return {
            "type": "string",
            "enum": [
                "steady",
                "oscillating",
                "regressing",
                "improving",
                "unknown",
            ],
        }
    if field == "discipline_rating":
        return {
            "type": "string",
            "enum": [
                "strong",
                "acceptable",
                "weak",
                "concerning",
                "unknown",
            ],
        }
    if field == "programme_health":
        return {
            "type": "string",
            "enum": [
                "strong",
                "acceptable",
                "weak",
                "concerning",
                "critical",
            ],
        }
    if field == "discipline":
        return {
            "type": "string",
            "enum": [
                "evidence",
                "replay",
                "ci",
                "traceability",
                "runtime_qualification",
                "review_completion",
                "unknown",
            ],
        }
    if field == "drift_type":
        return {"type": "string"}
    if field == "gate_status":
        return {
            "type": "string",
            "enum": ["passed", "warning", "failed", "not_executed", "unknown"],
        }
    if field == "latest_status":
        return {
            "type": "string",
            "enum": ["passed", "warning", "failed", "not_executed", "unknown"],
        }
    if field == "highest_risk":
        return {
            "type": "string",
            "enum": ["none", "low", "moderate", "high", "critical", "unknown"],
        }
    if field == "evidence_origin":
        return {
            "type": "string",
            "enum": [
                "scenario-evidence",
                "runtime-evidence",
                "live-runtime",
                "bag-backed",
                "static-source",
                "static-workspace",
                "unknown",
            ],
        }
    if field == "bag_status":
        return {
            "type": "string",
            "enum": [
                "ready",
                "partial",
                "missing_bag",
                "static_only",
                "not_executed",
                "failed",
                "passed",
                "unknown",
            ],
        }
    if field == "confidence":
        return {
            "type": "string",
            "enum": ["high", "moderate", "low", "unknown"],
        }
    if field == "outcome":
        return {
            "type": "string",
            "enum": [
                "controlled_degradation",
                "safe_stop_success",
                "estop_latched",
                "mission_aborted",
                "recovery_success",
                "recovery_failed",
                "inconclusive",
                "unknown",
            ],
        }
    if field == "requirement_kind":
        return {"type": "string"}
    if field == "requirement_id":
        return {"type": "string"}
    if field == "mapped_tests":
        return {"type": "integer", "minimum": 0}
    if field == "mapped_artifacts":
        return {"type": "integer", "minimum": 0}
    if field == "subsystem":
        return {"type": "string"}
    if field == "representative_artifacts":
        return {"type": "string"}
    if field == "metric_name":
        return {"type": "string"}
    if field == "window":
        return {
            "type": "string",
            "enum": ["full", "rolling_3", "rolling_5"],
        }
    if field == "finding_id":
        return {"type": "string"}
    if field == "description":
        return {"type": "string"}
    if field == "affected_metric":
        return {"type": ["string", "null"]}
    if field == "incident_id":
        return {"type": "string"}
    if field == "reason":
        return {"type": "string"}
    if field == "generated_at":
        return {"type": "string"}
    if field in _STRING_FIELDS_DEFAULT_NULLABLE:
        return {"type": ["string", "null"]}
    return {"type": ["string", "null"]}
