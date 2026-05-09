"""Tests for the evidence generator, traceability matrix, and report."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.verification.acceptance import AcceptanceStatus
from app.verification.evidence import write_evidence
from app.verification.report_generator import (
    render_scenario_verification_report,
    VerificationReport,
)
from app.verification.requirements import REQUIREMENTS, RequirementsRegistry
from app.verification.scenario_verifier import (
    SCENARIO_EXPECTATIONS,
    verify_scenario,
)
from app.verification.traceability import (
    build_traceability_matrix,
    write_traceability,
)


@pytest.fixture(scope="module")
def verifications(tmp_path_factory) -> list:
    runs_root = tmp_path_factory.mktemp("verify_runs")
    out = []
    for exp in SCENARIO_EXPECTATIONS:
        out.append(verify_scenario(exp, runs_root=runs_root))
    return out


def test_write_evidence_creates_artefacts(tmp_path: Path, verifications) -> None:
    evidence_root = tmp_path / "evidence"
    for v in verifications:
        ev = write_evidence(v, evidence_root=evidence_root)
        assert ev.status == v.status
        # Every artefact path exists.
        for art in ev.artefacts:
            assert art.path.exists(), f"missing {art.path}"
        # JSON evidence is parseable.
        json_path = evidence_root / "scenarios" / v.expectation.scenario_id / "evidence.json"
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        assert payload["scenario_id"] == v.expectation.scenario_id
        assert payload["status"] in [s.value for s in AcceptanceStatus]


def test_build_traceability_matrix_covers_every_requirement(verifications) -> None:
    matrix = build_traceability_matrix(verifications=verifications)
    assert len(matrix.rows) == len(REQUIREMENTS)
    # Every requirement appears exactly once.
    seen = {row.requirement.req_id for row in matrix.rows}
    assert len(seen) == len(matrix.rows)


def test_traceability_matrix_aggregates_to_passed_when_all_scenarios_pass(verifications) -> None:
    matrix = build_traceability_matrix(verifications=verifications)
    assert matrix.overall_status == AcceptanceStatus.PASSED


def test_traceability_matrix_render_markdown_contains_headers(verifications) -> None:
    matrix = build_traceability_matrix(verifications=verifications)
    md = matrix.render_markdown()
    assert "# Traceability Matrix" in md
    assert "Requirement" in md
    assert "REQ-SAFE-001" in md
    assert "not safety-certified" in md.lower()


def test_traceability_json_round_trip(tmp_path: Path, verifications) -> None:
    matrix = build_traceability_matrix(verifications=verifications)
    json_path = tmp_path / "trace.json"
    md_path = tmp_path / "trace.md"
    write_traceability(matrix, json_path=json_path, markdown_path=md_path)
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["row_count"] == len(REQUIREMENTS)
    assert "rows" in payload


def test_report_renders_summary_and_failures(verifications) -> None:
    md = render_scenario_verification_report(verifications)
    assert "# Scenario Verification Report" in md
    assert "Overall status" in md
    # Each scenario heading appears.
    for v in verifications:
        assert f"`{v.expectation.scenario_id}`" in md
    assert "## Failed checks" in md
    assert "## Known limitations" in md


def test_report_lists_skipped_and_not_executed_when_present(tmp_path: Path) -> None:
    exp = SCENARIO_EXPECTATIONS[0]
    v_skip = verify_scenario(exp, runs_root=tmp_path / "skip", skip_reason="manual skip")
    md = render_scenario_verification_report([v_skip])
    assert "skipped" in md
    assert "manual skip" in md


def test_verification_report_status_counts(verifications) -> None:
    report = VerificationReport(
        verifications=tuple(verifications),
        generated_at_utc="2026-05-09T00:00:00+00:00",
    )
    counts = report.status_counts()
    total = sum(counts.values())
    assert total == len(verifications)
    assert all(s.value in counts for s in AcceptanceStatus)


def test_traceability_with_no_verifications_marks_scenarios_not_executed() -> None:
    matrix = build_traceability_matrix(verifications=[])
    # Requirements with scenario refs but no verification result are
    # not_executed; pure-test ones are passed (test coverage suffices
    # at this layer).
    statuses = {row.requirement.req_id: row.status for row in matrix.rows}
    assert statuses["REQ-DIAG-001"] == AcceptanceStatus.PASSED
    assert statuses["REQ-SAFE-001"] == AcceptanceStatus.NOT_EXECUTED
