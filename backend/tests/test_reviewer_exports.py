"""Phase 11 reviewer-export tests.

Tests run without ROS, Gazebo, Foxglove, or network. Fixture
timestamps are deterministic; the layer never reads the wall
clock except via the explicit ``generated_at_utc`` argument the
tests supply.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Optional

import pytest


_REPO_ROOT = Path(__file__).resolve().parents[2]
_TOOLS_DIR = _REPO_ROOT / "rover_ws" / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))


from app.reviewer_exports import (  # noqa: E402
    ALL_TABLES,
    REVIEWER_EXPORT_DISCLAIMER,
    TABLE_FIELDS,
    build_all_tables,
    build_drift_rows,
    build_gate_history_rows,
    build_incident_index_rows,
    build_programme_health_rows,
    build_replay_quality_rows,
    build_requirement_coverage_rows,
    build_reviewer_export,
    build_subsystem_risk_rows,
    build_table_rows,
    build_trend_rows,
    load_reviewer_inputs,
    validate_export,
    write_csv,
    write_jsonl,
)
from app.reviewer_exports.models import LoadedReviewerInputs


# ---------------------------------------------------------------------------
# Fixture builders.
# ---------------------------------------------------------------------------


def _write_programme_review(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at_utc": "2026-05-12T00:00:00+00:00",
        "history_counts": {
            "reliability_impact": 1,
            "replay_analytics": 1,
            "runtime_qualification": 1,
            "replay_review": 3,
            "incident": 3,
        },
        "trend_report": {
            "series": [
                {
                    "label": "replay_quality_score",
                    "category": "stable",
                    "rolling_3": "stable",
                    "rolling_5": "stable",
                    "window_size": 3,
                    "detail": "first=80 last=85 samples=3 category=stable",
                    "observations": [
                        {
                            "timestamp": "2026-05-01T00:00:00+00:00",
                            "value": 80.0,
                            "record_id": "r1",
                            "evidence_origin": "scenario-evidence",
                        },
                        {
                            "timestamp": "2026-05-05T00:00:00+00:00",
                            "value": 85.0,
                            "record_id": "r2",
                            "evidence_origin": "scenario-evidence",
                        },
                        {
                            "timestamp": "2026-05-10T00:00:00+00:00",
                            "value": 85.0,
                            "record_id": "r3",
                            "evidence_origin": "scenario-evidence",
                        },
                    ],
                }
            ],
            "notes": [],
        },
        "drift_report": {
            "severity": "warning",
            "summary_counts": {
                "informational": 1,
                "warning": 1,
                "regression": 0,
                "critical_regression": 0,
            },
            "findings": [
                {
                    "label": "missing_bag_frequency_increasing",
                    "severity": "warning",
                    "detail": "missing_bag count moved 0 -> 1",
                    "evidence_paths": ["incidents/x/replay-review-report.json"],
                    "affected_subsystems": [],
                }
            ],
            "notes": [],
        },
        "governance_health": {
            "overall": "weak",
            "disciplines": [
                {
                    "category": "evidence",
                    "rating": "acceptable",
                    "reasons": ["replay-review coverage diversified"],
                    "triggering_artifacts": [],
                    "affected_subsystems": [],
                },
                {
                    "category": "ci",
                    "rating": "weak",
                    "reasons": ["one or more gate failures recorded"],
                    "triggering_artifacts": ["reliability-impact/canonical/impact-report.json"],
                    "affected_subsystems": [],
                },
            ],
            "notes": [],
        },
        "freshness_report": {
            "reference_time_utc": "2026-05-12T00:00:00+00:00",
            "status_counts": {"fresh": 3, "stale": 0, "unknown": 0},
            "entries": [],
            "notes": [],
        },
        "subsystem_risk_report": {
            "rows": [
                {
                    "subsystem": "safety",
                    "frequency": 2,
                    "severity_distribution": {"high": 1, "moderate": 1, "low": 0, "critical": 0, "none": 0},
                    "repeat_regression_count": 1,
                    "gate_failure_count": 0,
                    "unresolved_warning_count": 1,
                    "representative_artifacts": ["reliability-impact/canonical/impact-report.json"],
                }
            ],
            "notes": [],
        },
        "coverage_evolution": {
            "origin_mix_label": "static_only_only",
            "origin_distribution": {"scenario-evidence": 3},
            "bag_status_distribution": {"missing_bag": 2, "static_only": 1},
            "entries": [],
            "notes": [],
        },
        "gate_history": {
            "pass_count": 1,
            "warning_count": 0,
            "failure_count": 0,
            "not_executed_count": 0,
            "last_status": "passed",
            "last_transition": None,
            "volatility": "steady",
            "sequence": ["passed"],
            "notes": [],
        },
        "warnings": [],
        "known_limitations": [
            "The platform is **not** safety-certified.",
        ],
        "fixture_mode": False,
    }
    (root / "programme-review.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )
    (root / "trend-report.json").write_text(
        json.dumps(payload["trend_report"]), encoding="utf-8"
    )
    (root / "drift-report.json").write_text(
        json.dumps(payload["drift_report"]), encoding="utf-8"
    )
    (root / "subsystem-risk-report.json").write_text(
        json.dumps(payload["subsystem_risk_report"]), encoding="utf-8"
    )
    (root / "gate-history.json").write_text(
        json.dumps(payload["gate_history"]), encoding="utf-8"
    )
    (root / "governance-dashboard.json").write_text(
        json.dumps({"overall_health": "weak"}), encoding="utf-8"
    )


def _write_replay_quality(incidents_root: Path) -> None:
    analytics = incidents_root / "analytics"
    analytics.mkdir(parents=True, exist_ok=True)
    payload = {
        "rows": [
            {
                "incident_id": "canonical-stale-lidar",
                "score": 59,
                "coverage_status": "sparse",
                "confidence": "low",
                "bag_status": "missing_bag",
                "evidence_origin": "scenario-evidence",
                "evidence_status": "complete",
                "review_completion_status": "not_started",
            },
            {
                "incident_id": "canonical-static-qualification",
                "score": 37,
                "coverage_status": "sparse",
                "confidence": "low",
                "bag_status": "static_only",
                "evidence_origin": "scenario-evidence",
                "evidence_status": "static_only",
                "review_completion_status": "not_started",
            },
        ]
    }
    (analytics / "replay-quality-index.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )


def _write_incident_index(incidents_root: Path) -> None:
    incidents_root.mkdir(parents=True, exist_ok=True)
    payload = {
        "rows": [
            {
                "incident_id": "canonical-stale-lidar",
                "run_id": "stale_lidar_restricted_mode",
                "scenario_id": "stale_lidar_restricted_mode",
                "severity": "moderate",
                "outcome": "safe_stop_success",
                "evidence_status": "complete",
                "first_fault": "stale_lidar",
                "terminal_safety_state": "SAFE_STOP",
                "replay_integrity_status": "passed",
                "report_path": "incidents/canonical-stale-lidar/incident-report.json",
            },
            {
                "incident_id": "canonical-static-qualification",
                "run_id": "qualified-2026-05-10",
                "scenario_id": None,
                "severity": "informational",
                "outcome": "inconclusive",
                "evidence_status": "static_only",
                "first_fault": None,
                "terminal_safety_state": None,
                "replay_integrity_status": "-",
                "report_path": "incidents/canonical-static-qualification/incident-report.json",
            },
        ]
    }
    (incidents_root / "index.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )


def _write_reliability_impact(root: Path) -> None:
    bundle = root / "canonical"
    bundle.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at_utc": "2026-05-10T00:00:00+00:00",
        "head_ref": "head/canonical",
        "base_ref": "origin/main",
        "fixture_mode": True,
        "gate_decision": {"status": "passed", "failures": [], "warnings": []},
        "assessment": {
            "overall_risk": "moderate",
            "risks": [{"label": "safety_path_touched", "level": "moderate", "rationale": "fixture"}],
        },
        "subsystem_impacts": [
            {"subsystem": "safety", "is_safety_critical": True, "changed_files": []}
        ],
        "requirement_impacts": [
            {"subsystem": "safety", "requirement_ids": ["REQ-SAFE-001"], "notes": ""}
        ],
        "evidence_impacts": [
            {
                "subsystem": "safety",
                "requirement_ids": ["REQ-SAFE-001"],
                "recommended_tools": ["tools/audit_command_path.py"],
                "recommended_artifacts": ["evidence/scenarios/"],
                "notes": "",
            }
        ],
        "source_change": {
            "base_ref": "origin/main",
            "head_ref": "head/canonical",
            "source": "fixture",
            "changed_files": [],
        },
        "analytics_delta": {"severity": "neutral", "entries": []},
    }
    (bundle / "impact-report.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )


def _write_traceability(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at_utc": "2026-05-12T00:00:00+00:00",
        "rows": [
            {
                "requirement_id": "REQ-SAFE-001",
                "kind": "safety",
                "title": "Motion authority is centralised on the safety supervisor",
                "status": "passed",
                "test_refs": [
                    "backend/tests/test_simulation_engine.py::test_supervisor_is_only_publisher_of_authorized_motion",
                ],
                "evidence_paths": [
                    "evidence/scenarios/nominal_run/evidence.json",
                ],
            },
            {
                "requirement_id": "REQ-EXPORT-001",
                "kind": "export",
                "title": "Reviewer exports must provide CSV and JSONL outputs",
                "status": "passed",
                "test_refs": [
                    "backend/tests/test_reviewer_exports.py::test_csv_exports_are_deterministic",
                ],
                "evidence_paths": [],
            },
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_full_fixture(tmp_path: Path) -> dict:
    pr = tmp_path / "programme-review"
    inc = tmp_path / "incidents"
    ri = tmp_path / "reliability-impact"
    trace = tmp_path / "verification" / "traceability.json"
    _write_programme_review(pr)
    _write_replay_quality(inc)
    _write_incident_index(inc)
    _write_reliability_impact(ri)
    _write_traceability(trace)
    return {"pr": pr, "inc": inc, "ri": ri, "trace": trace}


def _build_canonical_export(tmp_path: Path) -> Path:
    fixture = _write_full_fixture(tmp_path)
    bundle = tmp_path / "out"
    build_reviewer_export(
        bundle_dir=bundle,
        programme_review_root=fixture["pr"],
        incidents_root=fixture["inc"],
        reliability_impact_root=fixture["ri"],
        traceability_path=fixture["trace"],
        export_id="reviewer-export-canonical",
        generated_at_utc="2026-05-12T00:00:00+00:00",
    )
    return bundle


# ---------------------------------------------------------------------------
# Loader behaviour.
# ---------------------------------------------------------------------------


def test_loader_handles_missing_optional_artifacts(tmp_path: Path) -> None:
    inputs = load_reviewer_inputs(
        programme_review_root=tmp_path / "ghost-pr",
        incidents_root=tmp_path / "ghost-incidents",
        reliability_impact_root=tmp_path / "ghost-ri",
        traceability_path=tmp_path / "ghost-trace.json",
    )
    assert inputs.programme_review is None
    assert inputs.replay_quality_index is None
    assert inputs.warnings  # all sources missing -> structured warnings


def test_loader_isolates_malformed_input(tmp_path: Path) -> None:
    pr = tmp_path / "pr"
    pr.mkdir()
    (pr / "programme-review.json").write_text("{ not json", encoding="utf-8")
    inputs = load_reviewer_inputs(
        programme_review_root=pr,
        incidents_root=tmp_path / "ghost",
        reliability_impact_root=tmp_path / "ghost",
        traceability_path=tmp_path / "ghost-trace.json",
    )
    assert inputs.programme_review is None
    assert any("did not parse" in w for w in inputs.warnings)


# ---------------------------------------------------------------------------
# Determinism.
# ---------------------------------------------------------------------------


def test_csv_exports_are_deterministic(tmp_path: Path) -> None:
    bundle_a = _build_canonical_export(tmp_path / "a")
    bundle_b = _build_canonical_export(tmp_path / "b")
    for table in ALL_TABLES:
        a = (bundle_a / "csv" / f"{table}.csv").read_text(encoding="utf-8")
        b = (bundle_b / "csv" / f"{table}.csv").read_text(encoding="utf-8")
        assert a == b, f"{table} csv drifted"


def test_jsonl_exports_are_line_delimited(tmp_path: Path) -> None:
    bundle = _build_canonical_export(tmp_path)
    for table in ALL_TABLES:
        text = (bundle / "jsonl" / f"{table}.jsonl").read_text(encoding="utf-8")
        if not text.strip():
            continue
        for line in text.splitlines():
            payload = json.loads(line)
            assert isinstance(payload, dict)


def test_all_documented_tables_emitted(tmp_path: Path) -> None:
    bundle = _build_canonical_export(tmp_path)
    for table in ALL_TABLES:
        assert (bundle / "csv" / f"{table}.csv").exists()
        assert (bundle / "jsonl" / f"{table}.jsonl").exists()
        assert (bundle / "schemas" / f"{table}.schema.json").exists()


# ---------------------------------------------------------------------------
# Honesty rules: static-only, missing-bag, causality.
# ---------------------------------------------------------------------------


def _csv_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_static_only_remains_static_only(tmp_path: Path) -> None:
    bundle = _build_canonical_export(tmp_path)
    rows = _csv_rows(bundle / "csv" / "replay_quality.csv")
    target = next(
        r for r in rows if r["incident_id"] == "canonical-static-qualification"
    )
    assert target["bag_status"] == "static_only"
    assert target["static_only"].lower() == "true"
    assert target["evidence_status"] == "static_only"


def test_missing_bag_remains_missing_bag(tmp_path: Path) -> None:
    bundle = _build_canonical_export(tmp_path)
    rows = _csv_rows(bundle / "csv" / "replay_quality.csv")
    target = next(
        r for r in rows if r["incident_id"] == "canonical-stale-lidar"
    )
    assert target["bag_status"] == "missing_bag"
    assert target["missing_bag"].lower() == "true"


def test_replay_quality_row_preserves_origin(tmp_path: Path) -> None:
    bundle = _build_canonical_export(tmp_path)
    rows = _csv_rows(bundle / "csv" / "replay_quality.csv")
    origins = {row["evidence_origin"] for row in rows}
    assert origins == {"scenario-evidence"}


def test_subsystem_risk_causality_claimed_false(tmp_path: Path) -> None:
    bundle = _build_canonical_export(tmp_path)
    rows = _csv_rows(bundle / "csv" / "subsystem_risk.csv")
    assert rows
    for row in rows:
        assert row["causality_claimed"].lower() == "false"


# ---------------------------------------------------------------------------
# Schemas + manifest + reporter.
# ---------------------------------------------------------------------------


def test_schemas_define_required_fields(tmp_path: Path) -> None:
    bundle = _build_canonical_export(tmp_path)
    for table in ALL_TABLES:
        schema = json.loads(
            (bundle / "schemas" / f"{table}.schema.json").read_text(
                encoding="utf-8"
            )
        )
        required = set(schema.get("required") or [])
        expected = set(TABLE_FIELDS[table])
        assert required == expected, table


def test_manifest_row_counts_match_files(tmp_path: Path) -> None:
    bundle = _build_canonical_export(tmp_path)
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    for table in ALL_TABLES:
        rows = _csv_rows(bundle / "csv" / f"{table}.csv")
        assert manifest["row_counts"][table] == len(rows), table


def test_manifest_contains_certification_disclaimer(tmp_path: Path) -> None:
    bundle = _build_canonical_export(tmp_path)
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["certification_disclaimer"] == REVIEWER_EXPORT_DISCLAIMER


def test_reviewer_summary_includes_disclaimer(tmp_path: Path) -> None:
    bundle = _build_canonical_export(tmp_path)
    summary = (bundle / "reviewer-export-summary.md").read_text(encoding="utf-8")
    assert REVIEWER_EXPORT_DISCLAIMER in summary
    assert "safety-certified" in summary


def test_reviewer_summary_distinguishes_origins(tmp_path: Path) -> None:
    bundle = _build_canonical_export(tmp_path)
    summary = (bundle / "reviewer-export-summary.md").read_text(encoding="utf-8")
    for marker in ("static-only", "missing-bag", "bag-backed"):
        assert marker in summary, marker


# ---------------------------------------------------------------------------
# Notebook.
# ---------------------------------------------------------------------------


def test_notebook_is_valid_json(tmp_path: Path) -> None:
    bundle = _build_canonical_export(tmp_path)
    notebook_path = bundle / "notebooks" / "reviewer_walkthrough.ipynb"
    payload = json.loads(notebook_path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    assert "cells" in payload
    assert payload.get("nbformat") == 4


def test_notebook_uses_optional_imports(tmp_path: Path) -> None:
    bundle = _build_canonical_export(tmp_path)
    notebook_path = bundle / "notebooks" / "reviewer_walkthrough.ipynb"
    payload = json.loads(notebook_path.read_text(encoding="utf-8"))
    code = "".join(
        "".join(cell.get("source", []))
        for cell in payload["cells"]
        if cell.get("cell_type") == "code"
    )
    assert "import csv" in code
    assert "try:" in code  # guard around pandas import
    assert "_HAS_PANDAS" in code


def test_notebook_does_not_require_ros(tmp_path: Path) -> None:
    bundle = _build_canonical_export(tmp_path)
    notebook_path = bundle / "notebooks" / "reviewer_walkthrough.ipynb"
    payload = json.loads(notebook_path.read_text(encoding="utf-8"))
    code = "".join(
        "".join(cell.get("source", []))
        for cell in payload["cells"]
        if cell.get("cell_type") == "code"
    )
    # The intro markdown explicitly says Foxglove is NOT required, so
    # the keyword can appear there. The runtime cells must not import
    # any ROS / Foxglove dependency.
    assert "import rclpy" not in code
    assert "rosbag2" not in code
    assert "import foxglove" not in code.lower()


def test_notebook_readme_present(tmp_path: Path) -> None:
    bundle = _build_canonical_export(tmp_path)
    readme = (bundle / "notebooks" / "README.md").read_text(encoding="utf-8")
    assert "reviewer_walkthrough.ipynb" in readme
    assert "safety-certified" in readme


# ---------------------------------------------------------------------------
# Validator.
# ---------------------------------------------------------------------------


def test_validator_passes_on_canonical_bundle(tmp_path: Path) -> None:
    bundle = _build_canonical_export(tmp_path)
    report = validate_export(bundle)
    assert report.passed, [r.as_dict() for r in report.results if not r.passed]


def test_validator_fails_when_bundle_missing(tmp_path: Path) -> None:
    report = validate_export(tmp_path / "ghost")
    assert not report.passed


def test_validator_fails_on_missing_table(tmp_path: Path) -> None:
    bundle = _build_canonical_export(tmp_path)
    (bundle / "csv" / "programme_health.csv").unlink()
    report = validate_export(bundle)
    assert not report.passed


def test_validator_fails_on_missing_disclaimer(tmp_path: Path) -> None:
    bundle = _build_canonical_export(tmp_path)
    summary = bundle / "reviewer-export-summary.md"
    summary.write_text("no disclaimer here", encoding="utf-8")
    report = validate_export(bundle)
    assert not report.passed
    assert any(
        not r.passed and r.name == "summary_includes_disclaimer"
        for r in report.results
    )


def test_validator_fails_when_causality_claimed_true(tmp_path: Path) -> None:
    bundle = _build_canonical_export(tmp_path)
    target = bundle / "csv" / "subsystem_risk.csv"
    text = target.read_text(encoding="utf-8")
    target.write_text(text.replace("false", "true"), encoding="utf-8")
    report = validate_export(bundle)
    assert not report.passed
    assert any(
        not r.passed and r.name == "subsystem_risk_causality_claimed_false"
        for r in report.results
    )


# ---------------------------------------------------------------------------
# Per-builder unit tests.
# ---------------------------------------------------------------------------


def test_build_programme_health_handles_no_disciplines() -> None:
    inputs = LoadedReviewerInputs(
        programme_review={
            "generated_at_utc": "2026-05-12T00:00:00+00:00",
            "governance_health": {"overall": "weak", "disciplines": []},
        }
    )
    rows = build_programme_health_rows(inputs)
    assert rows
    assert rows[0]["discipline"] == "unknown"


def test_build_trend_rows_emits_three_windows_per_series() -> None:
    inputs = LoadedReviewerInputs(
        trend_report={
            "series": [
                {
                    "label": "metric",
                    "category": "stable",
                    "rolling_3": "stable",
                    "rolling_5": "insufficient_history",
                    "window_size": 3,
                    "observations": [
                        {"value": 50, "evidence_origin": "scenario-evidence"},
                        {"value": 51, "evidence_origin": "scenario-evidence"},
                        {"value": 52, "evidence_origin": "scenario-evidence"},
                    ],
                }
            ]
        }
    )
    rows = build_trend_rows(inputs)
    windows = {row["window"] for row in rows}
    assert windows == {"full", "rolling_3", "rolling_5"}


def test_build_subsystem_risk_rows_carries_no_causality_field() -> None:
    inputs = LoadedReviewerInputs(
        subsystem_risk_report={
            "rows": [
                {
                    "subsystem": "safety",
                    "frequency": 1,
                    "severity_distribution": {"high": 1},
                    "repeat_regression_count": 1,
                    "gate_failure_count": 0,
                    "unresolved_warning_count": 1,
                    "representative_artifacts": [],
                }
            ]
        }
    )
    rows = build_subsystem_risk_rows(inputs)
    for row in rows:
        assert row["causality_claimed"] is False
        assert "blame" not in row
        assert "cause" not in row


def test_build_replay_quality_rows_flags_static_and_missing() -> None:
    inputs = LoadedReviewerInputs(
        replay_quality_index={
            "rows": [
                {
                    "incident_id": "x",
                    "score": 30,
                    "bag_status": "static_only",
                    "evidence_origin": "scenario-evidence",
                },
                {
                    "incident_id": "y",
                    "score": 50,
                    "bag_status": "missing_bag",
                    "evidence_origin": "scenario-evidence",
                },
            ]
        }
    )
    rows = build_replay_quality_rows(inputs)
    by_id = {row["incident_id"]: row for row in rows}
    assert by_id["x"]["static_only"] is True
    assert by_id["x"]["missing_bag"] is False
    assert by_id["y"]["missing_bag"] is True
    assert by_id["y"]["static_only"] is False


def test_build_incident_index_rows_normalises_blank_fields() -> None:
    inputs = LoadedReviewerInputs(
        incident_index={
            "rows": [
                {
                    "incident_id": "x",
                    "run_id": "",
                    "scenario_id": None,
                    "severity": "moderate",
                    "outcome": "safe_stop_success",
                    "evidence_status": "complete",
                    "first_fault": "",
                    "terminal_safety_state": "SAFE_STOP",
                    "replay_integrity_status": "passed",
                    "report_path": "incidents/x/incident-report.json",
                }
            ]
        }
    )
    rows = build_incident_index_rows(inputs)
    row = rows[0]
    assert row["run_id"] is None
    assert row["scenario_id"] is None
    assert row["first_fault"] is None
    assert row["terminal_safety_state"] == "SAFE_STOP"


def test_build_requirement_coverage_rows_classifies_status() -> None:
    inputs = LoadedReviewerInputs(
        traceability={
            "rows": [
                {
                    "requirement_id": "REQ-X",
                    "kind": "safety",
                    "title": "Title",
                    "status": "passed",
                    "test_refs": ["a"],
                    "evidence_paths": ["b"],
                },
                {
                    "requirement_id": "REQ-Y",
                    "kind": "safety",
                    "title": "Y",
                    "status": "passed",
                    "test_refs": [],
                    "evidence_paths": [],
                },
            ]
        }
    )
    rows = build_requirement_coverage_rows(inputs)
    by_id = {row["requirement_id"]: row for row in rows}
    assert by_id["REQ-X"]["coverage_status"] == "covered"
    assert by_id["REQ-Y"]["coverage_status"] == "unmapped"


def test_build_drift_rows_extracts_metric_from_label() -> None:
    inputs = LoadedReviewerInputs(
        drift_report={
            "findings": [
                {
                    "label": "missing_topic[/safety/state]",
                    "severity": "warning",
                    "detail": "fixture",
                    "evidence_paths": [],
                    "affected_subsystems": [],
                }
            ]
        }
    )
    rows = build_drift_rows(inputs)
    assert rows[0]["affected_metric"] == "missing_topic"


def test_build_gate_history_rows_emits_one_row_per_status() -> None:
    inputs = LoadedReviewerInputs(
        gate_history={
            "pass_count": 3,
            "warning_count": 1,
            "failure_count": 0,
            "not_executed_count": 0,
            "last_status": "passed",
            "last_transition": "warning -> passed",
            "volatility": "improving",
            "sequence": ["warning", "passed", "passed", "passed"],
        }
    )
    rows = build_gate_history_rows(inputs)
    statuses = {row["gate_status"]: row for row in rows}
    assert set(statuses) == {"passed", "warning", "failed", "not_executed"}
    assert statuses["passed"]["count"] == 3
    assert statuses["warning"]["count"] == 1


def test_build_all_tables_keys_match_canonical_list() -> None:
    inputs = LoadedReviewerInputs()
    tables = build_all_tables(inputs)
    assert set(tables.keys()) == set(ALL_TABLES)


# ---------------------------------------------------------------------------
# CLI smoke.
# ---------------------------------------------------------------------------


def _import_cli(name: str):
    import importlib

    return importlib.import_module(name)


def test_cli_generate_reviewer_export(tmp_path: Path) -> None:
    fixture = _write_full_fixture(tmp_path)
    cli = _import_cli("generate_reviewer_export")
    bundle = tmp_path / "out"
    rc = cli.main(
        [
            "--programme-review-root",
            str(fixture["pr"]),
            "--incidents-root",
            str(fixture["inc"]),
            "--reliability-impact-root",
            str(fixture["ri"]),
            "--traceability",
            str(fixture["trace"]),
            "--output",
            str(bundle),
            "--export-id",
            "cli-test",
            "--generated-at",
            "2026-05-12T00:00:00Z",
        ]
    )
    assert rc == 0
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["export_id"] == "cli-test"
    assert manifest["generated_at"] == "2026-05-12T00:00:00+00:00"


def test_cli_validate_reviewer_export(tmp_path: Path) -> None:
    bundle = _build_canonical_export(tmp_path)
    cli = _import_cli("validate_reviewer_export")
    rc = cli.main(["--bundle", str(bundle)])
    assert rc == 0


def test_cli_validate_fails_on_missing_bundle(tmp_path: Path) -> None:
    cli = _import_cli("validate_reviewer_export")
    rc = cli.main(["--bundle", str(tmp_path / "ghost")])
    assert rc == 1


# ---------------------------------------------------------------------------
# Workflow shape.
# ---------------------------------------------------------------------------


def test_reviewer_export_workflow_present() -> None:
    path = _REPO_ROOT / ".github" / "workflows" / "reviewer-export.yml"
    text = path.read_text(encoding="utf-8")
    assert "ubuntu-24.04" in text
    assert "self-hosted" not in text
    assert "upload-artifact" in text
    assert "reviewer-export/" in text


# ---------------------------------------------------------------------------
# Determinism / honesty: no wall-clock dependency.
# ---------------------------------------------------------------------------


def test_export_is_deterministic_given_fixed_timestamp(tmp_path: Path) -> None:
    fixture = _write_full_fixture(tmp_path / "src")
    bundle_a = tmp_path / "a"
    bundle_b = tmp_path / "b"
    build_reviewer_export(
        bundle_dir=bundle_a,
        programme_review_root=fixture["pr"],
        incidents_root=fixture["inc"],
        reliability_impact_root=fixture["ri"],
        traceability_path=fixture["trace"],
        export_id="canonical",
        generated_at_utc="2026-05-12T00:00:00+00:00",
    )
    build_reviewer_export(
        bundle_dir=bundle_b,
        programme_review_root=fixture["pr"],
        incidents_root=fixture["inc"],
        reliability_impact_root=fixture["ri"],
        traceability_path=fixture["trace"],
        export_id="canonical",
        generated_at_utc="2026-05-12T00:00:00+00:00",
    )
    manifest_a = (bundle_a / "manifest.json").read_text(encoding="utf-8")
    manifest_b = (bundle_b / "manifest.json").read_text(encoding="utf-8")
    payload_a = json.loads(manifest_a)
    payload_b = json.loads(manifest_b)
    # bundle_dir paths obviously differ, so compare row counts and
    # disclaimers explicitly.
    assert payload_a["row_counts"] == payload_b["row_counts"]
    assert (
        payload_a["certification_disclaimer"]
        == payload_b["certification_disclaimer"]
    )


def test_loader_warnings_propagate_to_summary(tmp_path: Path) -> None:
    """Run with no inputs -> summary records the loader warnings."""

    bundle = tmp_path / "out"
    build_reviewer_export(
        bundle_dir=bundle,
        programme_review_root=tmp_path / "ghost",
        incidents_root=tmp_path / "ghost-inc",
        reliability_impact_root=tmp_path / "ghost-ri",
        traceability_path=tmp_path / "ghost-trace.json",
        export_id="ghost",
        generated_at_utc="2026-05-12T00:00:00+00:00",
    )
    summary = (bundle / "reviewer-export-summary.md").read_text(encoding="utf-8")
    assert "Loader warnings" in summary
