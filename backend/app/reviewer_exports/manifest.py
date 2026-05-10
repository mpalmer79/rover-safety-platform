"""Reviewer-export manifest writer.

The manifest is the single source of truth for a reviewer who wants
to know what is in the export bundle. Row counts come straight from
the per-table exports; missing-source warnings come from the loader.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from app.reviewer_exports.models import (
    DEFAULT_KNOWN_LIMITATIONS,
    LoadedReviewerInputs,
    REVIEWER_EXPORT_DISCLAIMER,
    ReviewerExport,
    TableExport,
)


def write_manifest(
    export: ReviewerExport,
    *,
    inputs: LoadedReviewerInputs,
    path: Path,
) -> Path:
    """Write the manifest JSON to ``path``."""

    manifest = build_manifest_payload(export, inputs=inputs)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    export.manifest_path = path
    return path


def build_manifest_payload(
    export: ReviewerExport,
    *,
    inputs: LoadedReviewerInputs,
) -> dict:
    """Compose the manifest dict (no I/O)."""

    return {
        "export_id": export.export_id,
        "generated_at": export.generated_at_utc,
        "source_artifacts": list(export.source_artifacts),
        "tables": {
            table.name: table.as_manifest_entry() for table in export.tables
        },
        "row_counts": {table.name: len(table.rows) for table in export.tables},
        "schema_paths": {
            table.name: str(table.schema_path) for table in export.tables
        },
        "csv_paths": {
            table.name: str(table.csv_path) for table in export.tables
        },
        "jsonl_paths": {
            table.name: str(table.jsonl_path) for table in export.tables
        },
        "notebook_path": (
            str(export.notebook_path) if export.notebook_path else ""
        ),
        "summary_path": (
            str(export.summary_path) if export.summary_path else ""
        ),
        "warnings": list(export.warnings),
        "loader_warnings": list(inputs.warnings),
        "known_limitations": list(DEFAULT_KNOWN_LIMITATIONS),
        "certification_disclaimer": REVIEWER_EXPORT_DISCLAIMER,
    }


def manifest_source_artifacts(inputs: LoadedReviewerInputs) -> list[str]:
    """Return the list of source-artefact paths the loader read.

    Only paths that resolved to a parseable input are included; missing
    inputs are surfaced via the loader warnings list.
    """

    candidates: list[Path] = []
    if inputs.programme_review is not None and inputs.programme_review_path:
        candidates.append(inputs.programme_review_path)
    if inputs.governance_dashboard is not None and inputs.governance_dashboard_path:
        candidates.append(inputs.governance_dashboard_path)
    if inputs.trend_report is not None and inputs.trend_report_path:
        candidates.append(inputs.trend_report_path)
    if inputs.drift_report is not None and inputs.drift_report_path:
        candidates.append(inputs.drift_report_path)
    if (
        inputs.subsystem_risk_report is not None
        and inputs.subsystem_risk_report_path
    ):
        candidates.append(inputs.subsystem_risk_report_path)
    if inputs.gate_history is not None and inputs.gate_history_path:
        candidates.append(inputs.gate_history_path)
    if inputs.replay_quality_index is not None and inputs.replay_quality_index_path:
        candidates.append(inputs.replay_quality_index_path)
    if inputs.incident_index is not None and inputs.incident_index_path:
        candidates.append(inputs.incident_index_path)
    if inputs.traceability is not None and inputs.traceability_path:
        candidates.append(inputs.traceability_path)
    candidates.extend(inputs.impact_report_paths)
    return [str(p) for p in candidates]
