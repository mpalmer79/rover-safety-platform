"""Phase 11 reviewer-export package.

Read-only packaging layer over Phase 10's programme review, the
Phase 8 replay analytics, the Phase 6 incident index, the Phase 9
reliability-impact bundles, and the Phase 3 traceability matrix.
Emits CSV + JSONL + JSON Schemas + a manifest + a notebook scaffold
+ a reviewer summary.

The layer never mutates upstream artefacts, never invents data,
never claims causality, and never requires ROS, Gazebo, Foxglove,
or live runtime evidence.
"""

from app.reviewer_exports.exporters import (
    build_all_tables,
    build_drift_rows,
    build_gate_history_rows,
    build_incident_index_rows,
    build_programme_health_rows,
    build_replay_quality_rows,
    build_requirement_coverage_rows,
    build_subsystem_risk_rows,
    build_table_rows,
    build_trend_rows,
    write_csv,
    write_jsonl,
)
from app.reviewer_exports.loader import load_reviewer_inputs
from app.reviewer_exports.manifest import (
    build_manifest_payload,
    manifest_source_artifacts,
    write_manifest,
)
from app.reviewer_exports.models import (
    ALL_TABLES,
    DEFAULT_KNOWN_LIMITATIONS,
    LoadedReviewerInputs,
    REVIEWER_EXPORT_DISCLAIMER,
    ReviewerExport,
    TABLE_DRIFT_FINDINGS,
    TABLE_FIELDS,
    TABLE_GATE_HISTORY,
    TABLE_INCIDENT_INDEX,
    TABLE_PROGRAMME_HEALTH,
    TABLE_REPLAY_QUALITY,
    TABLE_REQUIREMENT_COVERAGE,
    TABLE_SUBSYSTEM_RISK,
    TABLE_TREND_SERIES,
    TableExport,
)
from app.reviewer_exports.notebook import (
    build_notebook,
    write_notebook,
    write_readme,
)
from app.reviewer_exports.reporter import (
    build_reviewer_export,
    render_reviewer_summary_md,
)
from app.reviewer_exports.schema import (
    build_schema,
    write_all_schemas,
    write_schema,
)
from app.reviewer_exports.validator import (
    ValidationReport,
    ValidationResult,
    validate_export,
)

__all__ = [
    "ALL_TABLES",
    "DEFAULT_KNOWN_LIMITATIONS",
    "LoadedReviewerInputs",
    "REVIEWER_EXPORT_DISCLAIMER",
    "ReviewerExport",
    "TABLE_DRIFT_FINDINGS",
    "TABLE_FIELDS",
    "TABLE_GATE_HISTORY",
    "TABLE_INCIDENT_INDEX",
    "TABLE_PROGRAMME_HEALTH",
    "TABLE_REPLAY_QUALITY",
    "TABLE_REQUIREMENT_COVERAGE",
    "TABLE_SUBSYSTEM_RISK",
    "TABLE_TREND_SERIES",
    "TableExport",
    "ValidationReport",
    "ValidationResult",
    "build_all_tables",
    "build_drift_rows",
    "build_gate_history_rows",
    "build_incident_index_rows",
    "build_manifest_payload",
    "build_notebook",
    "build_programme_health_rows",
    "build_replay_quality_rows",
    "build_requirement_coverage_rows",
    "build_reviewer_export",
    "build_schema",
    "build_subsystem_risk_rows",
    "build_table_rows",
    "build_trend_rows",
    "load_reviewer_inputs",
    "manifest_source_artifacts",
    "render_reviewer_summary_md",
    "validate_export",
    "write_all_schemas",
    "write_csv",
    "write_jsonl",
    "write_manifest",
    "write_notebook",
    "write_readme",
    "write_schema",
]
