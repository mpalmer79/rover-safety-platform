"""Per-table row builders + CSV/JSONL writers.

Each ``build_*_rows`` function consumes :class:`LoadedReviewerInputs`
and returns a list of row dicts whose keys exactly match the
canonical field list in ``models.TABLE_FIELDS``. Missing inputs
yield empty lists; the manifest records the row count so reviewers
can see exactly which tables had data.

All writers are deterministic: rows are emitted in a stable order
and floating-point values are formatted with a fixed precision so
the resulting CSV is byte-stable for a given input.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable

from app.reviewer_exports.models import (
    ALL_TABLES,
    LoadedReviewerInputs,
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


# ---------------------------------------------------------------------------
# Row builders.
# ---------------------------------------------------------------------------


def build_programme_health_rows(inputs: LoadedReviewerInputs) -> list[dict]:
    review = inputs.programme_review or {}
    health = review.get("governance_health") or {}
    overall = health.get("overall", "unknown")
    generated_at = review.get("generated_at_utc", "")
    rows: list[dict] = []
    disciplines = health.get("disciplines") or []
    if not disciplines:
        rows.append(
            _normalise_row(
                TABLE_PROGRAMME_HEALTH,
                {
                    "generated_at": generated_at,
                    "programme_health": overall,
                    "discipline": "unknown",
                    "discipline_rating": "unknown",
                    "reason": "no disciplines recorded",
                    "triggering_artifact": None,
                    "evidence_origin": None,
                    "known_limitation": _first_known_limitation(review),
                },
            )
        )
        return rows
    for discipline in disciplines:
        category = str(discipline.get("category", "unknown"))
        rating = str(discipline.get("rating", "unknown"))
        reasons = discipline.get("reasons") or []
        triggers = discipline.get("triggering_artifacts") or []
        if not reasons:
            reasons = ["no reasons recorded"]
        for reason in reasons:
            rows.append(
                _normalise_row(
                    TABLE_PROGRAMME_HEALTH,
                    {
                        "generated_at": generated_at,
                        "programme_health": overall,
                        "discipline": category,
                        "discipline_rating": rating,
                        "reason": str(reason),
                        "triggering_artifact": triggers[0] if triggers else None,
                        "evidence_origin": None,
                        "known_limitation": _first_known_limitation(review),
                    },
                )
            )
    return rows


def build_trend_rows(inputs: LoadedReviewerInputs) -> list[dict]:
    trend = inputs.trend_report or {}
    series = trend.get("series") or []
    rows: list[dict] = []
    for entry in series:
        if not isinstance(entry, dict):
            continue
        observations = entry.get("observations") or []
        available_values = [
            o.get("value") for o in observations
            if isinstance(o, dict) and isinstance(o.get("value"), (int, float))
        ]
        latest_value = available_values[-1] if available_values else None
        baseline_value = available_values[0] if available_values else None
        delta = (
            latest_value - baseline_value
            if isinstance(latest_value, (int, float))
            and isinstance(baseline_value, (int, float))
            else None
        )
        origins = sorted(
            {
                o.get("evidence_origin", "unknown")
                for o in observations
                if isinstance(o, dict)
            }
        )
        origin_mix = (
            origins[0]
            if len(origins) == 1
            else "mixed_origin"
            if origins
            else "unavailable"
        )
        history_status = (
            "insufficient_history"
            if entry.get("category") == "insufficient_history"
            else "available"
        )
        for window_label, window_field in (
            ("full", "category"),
            ("rolling_3", "rolling_3"),
            ("rolling_5", "rolling_5"),
        ):
            rows.append(
                _normalise_row(
                    TABLE_TREND_SERIES,
                    {
                        "metric_name": str(entry.get("label", "unknown")),
                        "window": window_label,
                        "trend_category": str(
                            entry.get(window_field, "insufficient_history")
                        ),
                        "latest_value": _stringify_number(latest_value),
                        "baseline_value": _stringify_number(baseline_value),
                        "delta": _stringify_number(delta),
                        "sample_count": int(entry.get("window_size", 0) or 0),
                        "history_status": history_status,
                        "evidence_origin_mix": origin_mix,
                    },
                )
            )
    return rows


def build_drift_rows(inputs: LoadedReviewerInputs) -> list[dict]:
    drift = inputs.drift_report or {}
    findings = drift.get("findings") or []
    rows: list[dict] = []
    for index, entry in enumerate(findings):
        if not isinstance(entry, dict):
            continue
        rows.append(
            _normalise_row(
                TABLE_DRIFT_FINDINGS,
                {
                    "finding_id": f"drift-{index:04d}",
                    "drift_type": str(entry.get("label", "unknown")),
                    "severity": str(entry.get("severity", "informational")),
                    "description": str(entry.get("detail", "")),
                    "affected_metric": _metric_from_label(entry.get("label", "")),
                    "current_value": None,
                    "baseline_value": None,
                    "triggering_artifact": _join_paths(
                        entry.get("evidence_paths") or []
                    ),
                    "evidence_origin": None,
                },
            )
        )
    return rows


def build_subsystem_risk_rows(inputs: LoadedReviewerInputs) -> list[dict]:
    report = inputs.subsystem_risk_report or {}
    rows_in = report.get("rows") or []
    rows: list[dict] = []
    for entry in rows_in:
        if not isinstance(entry, dict):
            continue
        distribution = entry.get("severity_distribution") or {}
        warning_count = int(distribution.get("moderate", 0) or 0)
        failure_count = int(distribution.get("high", 0) or 0)
        critical_count = int(distribution.get("critical", 0) or 0)
        highest = _highest_risk(distribution)
        rows.append(
            _normalise_row(
                TABLE_SUBSYSTEM_RISK,
                {
                    "subsystem": str(entry.get("subsystem", "unknown")),
                    "risk_frequency": int(entry.get("frequency", 0) or 0),
                    "highest_risk": highest,
                    "warning_count": warning_count,
                    "failure_count": failure_count,
                    "critical_count": critical_count,
                    "representative_artifacts": _join_paths(
                        entry.get("representative_artifacts") or []
                    ),
                    "causality_claimed": False,
                },
            )
        )
    return rows


def build_gate_history_rows(inputs: LoadedReviewerInputs) -> list[dict]:
    gate = inputs.gate_history or {}
    rows: list[dict] = []
    for status_field, status in (
        ("pass_count", "passed"),
        ("warning_count", "warning"),
        ("failure_count", "failed"),
        ("not_executed_count", "not_executed"),
    ):
        rows.append(
            _normalise_row(
                TABLE_GATE_HISTORY,
                {
                    "gate_status": status,
                    "count": int(gate.get(status_field, 0) or 0),
                    "latest_status": str(gate.get("last_status", "unknown")),
                    "volatility": str(gate.get("volatility", "unknown")),
                    "last_transition": _none_if_empty(gate.get("last_transition")),
                    "history_status": (
                        "insufficient_history"
                        if not (gate.get("sequence") or [])
                        else "available"
                    ),
                },
            )
        )
    return rows


def build_replay_quality_rows(inputs: LoadedReviewerInputs) -> list[dict]:
    quality = inputs.replay_quality_index or {}
    rows_in = quality.get("rows") or []
    rows: list[dict] = []
    for entry in rows_in:
        if not isinstance(entry, dict):
            continue
        bag_status = str(entry.get("bag_status", "unknown"))
        rows.append(
            _normalise_row(
                TABLE_REPLAY_QUALITY,
                {
                    "incident_id": str(entry.get("incident_id", "unknown")),
                    "score": int(entry.get("score", 0) or 0)
                    if isinstance(entry.get("score"), (int, float))
                    else None,
                    "coverage_status": str(
                        entry.get("coverage_status", "unknown")
                    ),
                    "confidence": str(entry.get("confidence", "unknown")),
                    "bag_status": bag_status,
                    "evidence_status": str(
                        entry.get("evidence_status") or entry.get("evidence_origin", "unknown")
                    ),
                    "review_completion_status": str(
                        entry.get("review_completion_status", "not_started")
                    ),
                    "evidence_origin": str(entry.get("evidence_origin", "unknown")),
                    "static_only": bag_status == "static_only",
                    "missing_bag": bag_status == "missing_bag",
                },
            )
        )
    return rows


def build_incident_index_rows(inputs: LoadedReviewerInputs) -> list[dict]:
    index = inputs.incident_index or {}
    rows_in = index.get("rows") or []
    rows: list[dict] = []
    for entry in rows_in:
        if not isinstance(entry, dict):
            continue
        rows.append(
            _normalise_row(
                TABLE_INCIDENT_INDEX,
                {
                    "incident_id": str(entry.get("incident_id", "unknown")),
                    "run_id": _none_if_empty(entry.get("run_id")),
                    "scenario_id": _none_if_empty(entry.get("scenario_id")),
                    "severity": str(entry.get("severity", "unknown")),
                    "outcome": str(entry.get("outcome", "unknown")),
                    "evidence_status": str(entry.get("evidence_status", "unknown")),
                    "first_fault": _none_if_empty(entry.get("first_fault")),
                    "terminal_safety_state": _none_if_empty(
                        entry.get("terminal_safety_state")
                    ),
                    "replay_integrity_status": _none_if_empty(
                        entry.get("replay_integrity_status")
                    ),
                    "report_path": _none_if_empty(entry.get("report_path")),
                },
            )
        )
    return rows


def build_requirement_coverage_rows(inputs: LoadedReviewerInputs) -> list[dict]:
    matrix = inputs.traceability or {}
    rows_in = matrix.get("rows") or []
    rows: list[dict] = []
    for entry in rows_in:
        if not isinstance(entry, dict):
            continue
        rows.append(
            _normalise_row(
                TABLE_REQUIREMENT_COVERAGE,
                {
                    "requirement_id": str(entry.get("requirement_id", "unknown")),
                    "requirement_kind": str(entry.get("kind", "unknown")),
                    "category_tier": str(entry.get("category_tier", "core")),
                    "title": str(entry.get("title", "")),
                    "status": str(entry.get("status", "unknown")),
                    "mapped_tests": len(entry.get("test_refs") or []),
                    "mapped_artifacts": len(entry.get("evidence_paths") or []),
                    "coverage_status": _coverage_status(entry),
                },
            )
        )
    return rows


# ---------------------------------------------------------------------------
# Writers.
# ---------------------------------------------------------------------------


def write_csv(table: str, rows: list[dict], *, path: Path) -> Path:
    fields = TABLE_FIELDS[table]
    path.parent.mkdir(parents=True, exist_ok=True)
    # ``newline=""`` keeps CSV writes identical across platforms; we
    # also force LF line endings so the output is byte-stable for
    # tests.
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=list(fields),
            lineterminator="\n",
            extrasaction="ignore",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _csv_value(row.get(field)) for field in fields})
    return path


def write_jsonl(table: str, rows: list[dict], *, path: Path) -> Path:
    fields = TABLE_FIELDS[table]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            payload = {field: row.get(field) for field in fields}
            fh.write(json.dumps(payload, sort_keys=True))
            fh.write("\n")
    return path


# ---------------------------------------------------------------------------
# Helpers.
# ---------------------------------------------------------------------------


def _normalise_row(table: str, row: dict) -> dict:
    """Project ``row`` onto the canonical field list."""

    fields = TABLE_FIELDS[table]
    out = {}
    for field in fields:
        value = row.get(field)
        out[field] = value
    return out


def _stringify_number(value) -> Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return round(float(value), 4)
    return None


def _csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return format(value, ".4f").rstrip("0").rstrip(".")
    return str(value)


def _join_paths(items: Iterable[Any]) -> str:
    paths = [str(p) for p in items if p]
    if not paths:
        return ""
    return "; ".join(paths)


def _none_if_empty(value: Any) -> Any:
    if value in (None, "", []):
        return None
    return value


def _highest_risk(distribution: dict[str, Any]) -> str:
    for level in ("critical", "high", "moderate", "low", "none"):
        try:
            count = int(distribution.get(level, 0) or 0)
        except (TypeError, ValueError):
            count = 0
        if count > 0:
            return level
    return "unknown"


def _metric_from_label(label: str) -> Any:
    if not label:
        return None
    if "[" in label and "]" in label:
        return label[: label.index("[")]
    return label


def _coverage_status(entry: dict) -> str:
    tests = len(entry.get("test_refs") or [])
    artefacts = len(entry.get("evidence_paths") or [])
    if tests == 0 and artefacts == 0:
        return "unmapped"
    if tests > 0 and artefacts > 0:
        return "covered"
    if tests > 0:
        return "tests_only"
    return "evidence_only"


def _first_known_limitation(payload: dict) -> Any:
    limitations = payload.get("known_limitations") or []
    if not limitations:
        return None
    if isinstance(limitations[0], str):
        return limitations[0]
    return None


# ---------------------------------------------------------------------------
# Public composition.
# ---------------------------------------------------------------------------


_TABLE_BUILDERS = {
    "programme_health": build_programme_health_rows,
    "trend_series": build_trend_rows,
    "drift_findings": build_drift_rows,
    "subsystem_risk": build_subsystem_risk_rows,
    "gate_history": build_gate_history_rows,
    "replay_quality": build_replay_quality_rows,
    "incident_index": build_incident_index_rows,
    "requirement_coverage": build_requirement_coverage_rows,
}


def build_table_rows(table: str, inputs: LoadedReviewerInputs) -> list[dict]:
    builder = _TABLE_BUILDERS[table]
    return builder(inputs)


def build_all_tables(inputs: LoadedReviewerInputs) -> dict[str, list[dict]]:
    return {table: build_table_rows(table, inputs) for table in ALL_TABLES}
