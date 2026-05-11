"""Typed models for the Phase 11 reviewer-export layer.

The layer is **read-only** with respect to upstream artefacts. Every
exporter consumes the loaded payloads (programme review, replay
analytics, incident index, reliability impact) and emits CSV +
JSONL rows that obey a stable, schema-backed shape.

Honesty rules (preserved from prior phases):

* static-only stays static-only;
* missing-bag stays missing-bag;
* ``causality_claimed`` is always ``false``;
* every reviewer-facing report carries the verbatim certification
  disclaimer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional


# ---------------------------------------------------------------------------
# Table identifiers + canonical field lists.
# ---------------------------------------------------------------------------


TABLE_PROGRAMME_HEALTH = "programme_health"
TABLE_TREND_SERIES = "trend_series"
TABLE_DRIFT_FINDINGS = "drift_findings"
TABLE_SUBSYSTEM_RISK = "subsystem_risk"
TABLE_GATE_HISTORY = "gate_history"
TABLE_REPLAY_QUALITY = "replay_quality"
TABLE_INCIDENT_INDEX = "incident_index"
TABLE_REQUIREMENT_COVERAGE = "requirement_coverage"


ALL_TABLES: tuple[str, ...] = (
    TABLE_PROGRAMME_HEALTH,
    TABLE_TREND_SERIES,
    TABLE_DRIFT_FINDINGS,
    TABLE_SUBSYSTEM_RISK,
    TABLE_GATE_HISTORY,
    TABLE_REPLAY_QUALITY,
    TABLE_INCIDENT_INDEX,
    TABLE_REQUIREMENT_COVERAGE,
)


TABLE_FIELDS: dict[str, tuple[str, ...]] = {
    TABLE_PROGRAMME_HEALTH: (
        "generated_at",
        "programme_health",
        "discipline",
        "discipline_rating",
        "reason",
        "triggering_artifact",
        "evidence_origin",
        "known_limitation",
    ),
    TABLE_TREND_SERIES: (
        "metric_name",
        "window",
        "trend_category",
        "latest_value",
        "baseline_value",
        "delta",
        "sample_count",
        "history_status",
        "evidence_origin_mix",
    ),
    TABLE_DRIFT_FINDINGS: (
        "finding_id",
        "drift_type",
        "severity",
        "description",
        "affected_metric",
        "current_value",
        "baseline_value",
        "triggering_artifact",
        "evidence_origin",
    ),
    TABLE_SUBSYSTEM_RISK: (
        "subsystem",
        "risk_frequency",
        "highest_risk",
        "warning_count",
        "failure_count",
        "critical_count",
        "representative_artifacts",
        "causality_claimed",
    ),
    TABLE_GATE_HISTORY: (
        "gate_status",
        "count",
        "latest_status",
        "volatility",
        "last_transition",
        "history_status",
    ),
    TABLE_REPLAY_QUALITY: (
        "incident_id",
        "score",
        "coverage_status",
        "confidence",
        "bag_status",
        "evidence_status",
        "review_completion_status",
        "evidence_origin",
        "static_only",
        "missing_bag",
    ),
    TABLE_INCIDENT_INDEX: (
        "incident_id",
        "run_id",
        "scenario_id",
        "severity",
        "outcome",
        "evidence_status",
        "first_fault",
        "terminal_safety_state",
        "replay_integrity_status",
        "report_path",
    ),
    TABLE_REQUIREMENT_COVERAGE: (
        "requirement_id",
        "requirement_kind",
        "category_tier",
        "title",
        "status",
        "mapped_tests",
        "mapped_artifacts",
        "coverage_status",
    ),
}


# ---------------------------------------------------------------------------
# Loaded artefacts.
# ---------------------------------------------------------------------------


@dataclass
class LoadedReviewerInputs:
    """Loaded source documents that the exporters consume.

    Each field is optional; missing inputs degrade the export
    deterministically (empty rows for tables that depended on the
    absent input). The loader records warnings rather than raising.
    """

    programme_review: Optional[dict] = None
    programme_review_path: Optional[Path] = None
    governance_dashboard: Optional[dict] = None
    governance_dashboard_path: Optional[Path] = None
    trend_report: Optional[dict] = None
    trend_report_path: Optional[Path] = None
    drift_report: Optional[dict] = None
    drift_report_path: Optional[Path] = None
    subsystem_risk_report: Optional[dict] = None
    subsystem_risk_report_path: Optional[Path] = None
    gate_history: Optional[dict] = None
    gate_history_path: Optional[Path] = None
    replay_quality_index: Optional[dict] = None
    replay_quality_index_path: Optional[Path] = None
    incident_index: Optional[dict] = None
    incident_index_path: Optional[Path] = None
    impact_reports: list[dict] = field(default_factory=list)
    impact_report_paths: list[Path] = field(default_factory=list)
    traceability: Optional[dict] = None
    traceability_path: Optional[Path] = None
    warnings: list[str] = field(default_factory=list)


@dataclass
class TableExport:
    """One exported table — the structured rows + the destination paths."""

    name: str
    rows: list[dict]
    fields: tuple[str, ...]
    csv_path: Path
    jsonl_path: Path
    schema_path: Path

    def as_manifest_entry(self) -> dict:
        return {
            "name": self.name,
            "row_count": len(self.rows),
            "fields": list(self.fields),
            "csv_path": str(self.csv_path),
            "jsonl_path": str(self.jsonl_path),
            "schema_path": str(self.schema_path),
        }


@dataclass
class ReviewerExport:
    export_id: str
    generated_at_utc: str
    bundle_dir: Path
    tables: list[TableExport] = field(default_factory=list)
    notebook_path: Optional[Path] = None
    summary_path: Optional[Path] = None
    manifest_path: Optional[Path] = None
    warnings: list[str] = field(default_factory=list)
    source_artifacts: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "export_id": self.export_id,
            "generated_at_utc": self.generated_at_utc,
            "bundle_dir": str(self.bundle_dir),
            "tables": [t.as_manifest_entry() for t in self.tables],
            "notebook_path": str(self.notebook_path) if self.notebook_path else "",
            "summary_path": str(self.summary_path) if self.summary_path else "",
            "manifest_path": str(self.manifest_path) if self.manifest_path else "",
            "warnings": list(self.warnings),
            "source_artifacts": list(self.source_artifacts),
        }


# ---------------------------------------------------------------------------
# Disclaimers.
# ---------------------------------------------------------------------------


REVIEWER_EXPORT_DISCLAIMER: str = (
    "This reviewer export is generated from available engineering "
    "evidence. It does not represent safety certification or "
    "regulatory approval."
)


DEFAULT_KNOWN_LIMITATIONS: tuple[str, ...] = (
    "The platform is **not** safety-certified. The reviewer export "
    "is an engineering evidence packaging.",
    "The export is read-only with respect to upstream artefacts; it "
    "never invents data and never infers causality.",
    "Static-only evidence stays static-only across the export. "
    "Missing-bag stays missing-bag.",
    "When a source artefact is missing, the corresponding table is "
    "still emitted with zero rows; the manifest records the absence.",
    "The reviewer notebook loads CSV files from the neighbour "
    "``../csv/`` directory using only the Python standard library "
    "(and pandas / matplotlib via optional guarded imports).",
)
