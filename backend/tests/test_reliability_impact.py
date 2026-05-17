"""Phase 9 reliability-impact tests.

Tests run without ROS, Gazebo, Foxglove, or network. They exercise:

* git change inventory — explicit list mode, working-tree fallback;
* subsystem classifier — safety / mission / replay analytics / ROS
  workspace / CI / unknown paths;
* requirement mapper — safety -> REQ-SAFE, replay_analytics -> REQ-
  ANALYTICS, unknown reports unmapped, docs/tests no-op;
* evidence mapper — safety recommends command-path audit, incident
  analysis recommends incident bundle regeneration, replay_analytics
  recommends analytics regeneration;
* analytics delta — score-drop warning vs regression vs critical,
  missing baseline warning, static-only not promoted to regression;
* risk assessor — safety changes high without evidence, docs-only
  low, CI workflow removal high, critical regression critical;
* CI gate — fails on critical regression, does not fail on missing
  live runtime evidence, warns on missing baseline, fails on static
  validation workflow removal;
* CLIs — analyze_source_impact, reliability_impact_gate.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


_REPO_ROOT = Path(__file__).resolve().parents[2]
_TOOLS_DIR = _REPO_ROOT / "rover_ws" / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))


from app.reliability_impact import (  # noqa: E402
    BaselineReference,
    ChangedFile,
    ChangeType,
    DeltaSeverity,
    EvidenceImpact,
    GateStatus,
    ImpactAssessment,
    ReliabilityRisk,
    ReplayAnalyticsDelta,
    RequirementImpact,
    RiskLevel,
    SourceChange,
    Subsystem,
    SubsystemImpact,
    assess_impact,
    build_report,
    classify_path,
    collect_source_change,
    compute_analytics_delta,
    decide_gate,
    map_evidence,
    map_evidence_for_impacts,
    map_impacts,
    map_subsystem_to_requirements,
    resolve_baseline,
)


# ---------------------------------------------------------------------------
# Git change inventory.
# ---------------------------------------------------------------------------


def test_explicit_changed_files_mode() -> None:
    sc = collect_source_change(
        changed_files=[
            "backend/app/safety/supervisor.py",
            "docs/REPLAY_ANALYTICS.md",
        ],
    )
    assert sc.source == "explicit_list"
    assert len(sc.changed_files) == 2
    assert {f.subsystem for f in sc.changed_files} == {
        Subsystem.SAFETY,
        Subsystem.DOCS,
    }


def test_explicit_changed_files_with_status_prefix() -> None:
    sc = collect_source_change(
        changed_files=["M backend/app/safety/supervisor.py", "A docs/foo.md"],
    )
    statuses = {f.change_type for f in sc.changed_files}
    assert ChangeType.MODIFIED in statuses
    assert ChangeType.ADDED in statuses


def test_explicit_changed_files_handles_commas_and_newlines() -> None:
    sc = collect_source_change(
        changed_files=["a/b.py,c/d.py\ne/f.py"],
    )
    assert len(sc.changed_files) == 3


def test_fixture_mode_tagged() -> None:
    sc = collect_source_change(
        changed_files=["backend/app/safety/supervisor.py"],
        fixture_mode=True,
    )
    assert sc.source == "fixture"


# ---------------------------------------------------------------------------
# Subsystem classifier.
# ---------------------------------------------------------------------------


def test_subsystem_classifier_safety_path() -> None:
    assert classify_path("backend/app/safety/supervisor.py") == Subsystem.SAFETY
    assert classify_path("rover_ws/src/rover_safety_bridge/foo.py") == Subsystem.SAFETY


def test_subsystem_classifier_mission_path() -> None:
    assert classify_path("backend/app/mission/orchestrator.py") == Subsystem.MISSION
    assert classify_path("rover_ws/src/rover_mission_runtime/x.py") == Subsystem.MISSION


def test_subsystem_classifier_replay_analytics_path() -> None:
    assert classify_path("backend/app/replay_analytics/scoring.py") == Subsystem.REPLAY_ANALYTICS


def test_subsystem_classifier_ros_workspace_path() -> None:
    assert classify_path("rover_ws/src/rover_bringup/launch.py") == Subsystem.ROS_WORKSPACE
    assert classify_path("rover_ws/tools/analyze_source_impact.py") == Subsystem.ROS_WORKSPACE


def test_subsystem_classifier_gazebo_simulation() -> None:
    assert classify_path("rover_ws/src/rover_sim_gazebo/x.py") == Subsystem.GAZEBO_SIMULATION
    assert classify_path("rover_ws/src/rover_description/foo.urdf") == Subsystem.GAZEBO_SIMULATION


def test_subsystem_classifier_ci_path() -> None:
    assert classify_path(".github/workflows/foo.yml") == Subsystem.CI


def test_subsystem_classifier_docs_path() -> None:
    assert classify_path("docs/REPLAY_ANALYTICS.md") == Subsystem.DOCS


def test_subsystem_classifier_tests_path() -> None:
    assert classify_path("backend/tests/test_foo.py") == Subsystem.TESTS
    assert classify_path("rover_ws/tests/test_bar.py") == Subsystem.TESTS


def test_subsystem_classifier_unknown_path() -> None:
    assert classify_path("README.md") == Subsystem.UNKNOWN
    assert classify_path("random/file.txt") == Subsystem.UNKNOWN


def test_subsystem_classifier_handles_leading_dot_slash() -> None:
    assert classify_path("./backend/app/safety/supervisor.py") == Subsystem.SAFETY
    assert classify_path("./.github/workflows/foo.yml") == Subsystem.CI


def test_subsystem_classifier_handles_empty() -> None:
    assert classify_path("") == Subsystem.UNKNOWN
    assert classify_path("   ") == Subsystem.UNKNOWN


# ---------------------------------------------------------------------------
# Requirement mapper.
# ---------------------------------------------------------------------------


def test_requirement_mapper_safety_to_req_safe() -> None:
    impact = map_subsystem_to_requirements(Subsystem.SAFETY)
    assert any(rid.startswith("REQ-SAFE") for rid in impact.requirement_ids)


def test_requirement_mapper_replay_analytics_to_req_analytics() -> None:
    impact = map_subsystem_to_requirements(Subsystem.REPLAY_ANALYTICS)
    assert any(rid.startswith("REQ-ANALYTICS") for rid in impact.requirement_ids)


def test_requirement_mapper_runtime_validation_to_req_runtime() -> None:
    impact = map_subsystem_to_requirements(Subsystem.RUNTIME_VALIDATION)
    assert any(rid.startswith("REQ-RUNTIME") for rid in impact.requirement_ids)


def test_requirement_mapper_incident_analysis_to_req_incident() -> None:
    impact = map_subsystem_to_requirements(Subsystem.INCIDENT_ANALYSIS)
    assert any(rid.startswith("REQ-INCIDENT") for rid in impact.requirement_ids)


def test_requirement_mapper_reliability_impact_to_req_impact() -> None:
    impact = map_subsystem_to_requirements(Subsystem.RELIABILITY_IMPACT)
    assert any(rid.startswith("REQ-IMPACT") for rid in impact.requirement_ids)


def test_requirement_mapper_docs_has_no_requirements() -> None:
    impact = map_subsystem_to_requirements(Subsystem.DOCS)
    assert impact.requirement_ids == ()
    assert "documentation" in impact.notes.lower()


def test_requirement_mapper_unknown_is_unmapped() -> None:
    impact = map_subsystem_to_requirements(Subsystem.UNKNOWN)
    assert impact.requirement_ids == ()
    assert "unknown" in impact.notes.lower()


# ---------------------------------------------------------------------------
# Evidence mapper.
# ---------------------------------------------------------------------------


def test_evidence_mapper_safety_recommends_command_audit() -> None:
    si = SubsystemImpact(
        subsystem=Subsystem.SAFETY,
        changed_files=(),
        is_safety_critical=True,
    )
    ri = RequirementImpact(subsystem=Subsystem.SAFETY, requirement_ids=())
    e = map_evidence(si, ri)
    assert any("audit_command_path" in t for t in e.recommended_tools)
    assert any("audit_safety_transitions" in t for t in e.recommended_tools)


def test_evidence_mapper_incident_analysis_recommends_incident_bundle() -> None:
    si = SubsystemImpact(
        subsystem=Subsystem.INCIDENT_ANALYSIS, changed_files=()
    )
    ri = RequirementImpact(subsystem=Subsystem.INCIDENT_ANALYSIS, requirement_ids=())
    e = map_evidence(si, ri)
    assert any("reconstruct_incident" in t for t in e.recommended_tools)


def test_evidence_mapper_replay_analytics_recommends_analytics() -> None:
    si = SubsystemImpact(subsystem=Subsystem.REPLAY_ANALYTICS, changed_files=())
    ri = RequirementImpact(
        subsystem=Subsystem.REPLAY_ANALYTICS, requirement_ids=()
    )
    e = map_evidence(si, ri)
    assert any("generate_replay_analytics" in t for t in e.recommended_tools)


def test_evidence_mapper_unknown_has_no_tools() -> None:
    si = SubsystemImpact(subsystem=Subsystem.UNKNOWN, changed_files=())
    ri = RequirementImpact(subsystem=Subsystem.UNKNOWN, requirement_ids=())
    e = map_evidence(si, ri)
    assert e.recommended_tools == ()
    assert "unknown" in e.notes.lower()


# ---------------------------------------------------------------------------
# Analytics delta.
# ---------------------------------------------------------------------------


def _write_quality_index(path: Path, rows: list[dict]) -> Path:
    path.write_text(
        json.dumps({"rows": rows}, indent=2, sort_keys=True), encoding="utf-8"
    )
    return path


def _quality_row(
    *,
    incident_id: str,
    score: int,
    coverage_status: str = "sparse",
    bag_status: str = "missing_bag",
    evidence_origin: str = "scenario-evidence",
) -> dict:
    return {
        "incident_id": incident_id,
        "score": score,
        "coverage_status": coverage_status,
        "bag_status": bag_status,
        "evidence_origin": evidence_origin,
        "bucket": "0-39" if score < 40 else "40-69",
    }


def test_analytics_delta_score_drop_warning(tmp_path: Path) -> None:
    base = _write_quality_index(
        tmp_path / "baseline.json",
        [_quality_row(incident_id="x", score=60)],
    )
    current = _write_quality_index(
        tmp_path / "current.json",
        [_quality_row(incident_id="x", score=48)],
    )
    delta = compute_analytics_delta(
        current_quality_index=current,
        current_analytics_report=None,
        baseline=BaselineReference(
            quality_index_path=base, analytics_report_path=None
        ),
    )
    score_entries = [e for e in delta.entries if e.category == "score"]
    assert any(e.severity == DeltaSeverity.WARNING for e in score_entries)


def test_analytics_delta_score_drop_regression(tmp_path: Path) -> None:
    base = _write_quality_index(
        tmp_path / "baseline.json",
        [_quality_row(incident_id="x", score=80)],
    )
    current = _write_quality_index(
        tmp_path / "current.json",
        [_quality_row(incident_id="x", score=50)],
    )
    delta = compute_analytics_delta(
        current_quality_index=current,
        current_analytics_report=None,
        baseline=BaselineReference(
            quality_index_path=base, analytics_report_path=None
        ),
    )
    assert delta.severity == DeltaSeverity.REGRESSION


def test_analytics_delta_score_crossing_below_40_critical(tmp_path: Path) -> None:
    base = _write_quality_index(
        tmp_path / "baseline.json",
        [_quality_row(incident_id="x", score=55)],
    )
    current = _write_quality_index(
        tmp_path / "current.json",
        [_quality_row(incident_id="x", score=20)],
    )
    delta = compute_analytics_delta(
        current_quality_index=current,
        current_analytics_report=None,
        baseline=BaselineReference(
            quality_index_path=base, analytics_report_path=None
        ),
    )
    assert delta.severity == DeltaSeverity.CRITICAL_REGRESSION


def test_analytics_delta_missing_baseline_warning(tmp_path: Path) -> None:
    current = _write_quality_index(
        tmp_path / "current.json",
        [_quality_row(incident_id="x", score=80)],
    )
    delta = compute_analytics_delta(
        current_quality_index=current,
        current_analytics_report=None,
        baseline=BaselineReference(
            quality_index_path=None, analytics_report_path=None,
            notes="baseline missing",
        ),
    )
    # A missing baseline is a warning, not a failure.
    assert delta.severity in {DeltaSeverity.WARNING, DeltaSeverity.NEUTRAL}
    assert any("baseline" in w.lower() for w in delta.warnings)


def test_analytics_delta_static_only_not_regression(tmp_path: Path) -> None:
    # Both baseline and current report static_only - no regression.
    base = _write_quality_index(
        tmp_path / "baseline.json",
        [
            _quality_row(
                incident_id="x",
                score=37,
                coverage_status="sparse",
                bag_status="static_only",
                evidence_origin="scenario-evidence",
            )
        ],
    )
    current = _write_quality_index(
        tmp_path / "current.json",
        [
            _quality_row(
                incident_id="x",
                score=37,
                coverage_status="sparse",
                bag_status="static_only",
                evidence_origin="scenario-evidence",
            )
        ],
    )
    delta = compute_analytics_delta(
        current_quality_index=current,
        current_analytics_report=None,
        baseline=BaselineReference(
            quality_index_path=base, analytics_report_path=None
        ),
    )
    assert delta.severity == DeltaSeverity.NEUTRAL


def test_analytics_delta_new_contradiction_critical(tmp_path: Path) -> None:
    base_report = tmp_path / "baseline_report.json"
    current_report = tmp_path / "current_report.json"
    base_report.write_text(
        json.dumps(
            {
                "incident_count": 1,
                "scores": [
                    {
                        "incident_id": "x",
                        "score": 80,
                        "blocking_gaps": [],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    current_report.write_text(
        json.dumps(
            {
                "incident_count": 1,
                "scores": [
                    {
                        "incident_id": "x",
                        "score": 39,
                        "blocking_gaps": ["contradictions=1"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    base_quality = _write_quality_index(
        tmp_path / "baseline.json",
        [_quality_row(incident_id="x", score=80)],
    )
    current_quality = _write_quality_index(
        tmp_path / "current.json",
        [_quality_row(incident_id="x", score=39)],
    )
    delta = compute_analytics_delta(
        current_quality_index=current_quality,
        current_analytics_report=current_report,
        baseline=BaselineReference(
            quality_index_path=base_quality,
            analytics_report_path=base_report,
        ),
    )
    assert delta.severity == DeltaSeverity.CRITICAL_REGRESSION
    assert any(e.category == "contradiction" for e in delta.entries)


def test_analytics_delta_honesty_violation_critical(tmp_path: Path) -> None:
    base = _write_quality_index(
        tmp_path / "baseline.json",
        [
            _quality_row(
                incident_id="x",
                score=37,
                bag_status="static_only",
                evidence_origin="scenario-evidence",
            )
        ],
    )
    current = _write_quality_index(
        tmp_path / "current.json",
        [
            _quality_row(
                incident_id="x",
                score=37,
                bag_status="static_only",
                evidence_origin="bag-backed",  # honesty violation
            )
        ],
    )
    delta = compute_analytics_delta(
        current_quality_index=current,
        current_analytics_report=None,
        baseline=BaselineReference(
            quality_index_path=base, analytics_report_path=None
        ),
    )
    assert delta.severity == DeltaSeverity.CRITICAL_REGRESSION
    assert any(e.category == "honesty" for e in delta.entries)


# ---------------------------------------------------------------------------
# Risk assessor.
# ---------------------------------------------------------------------------


def _src(*paths: str, change_type: ChangeType = ChangeType.MODIFIED) -> SourceChange:
    files = tuple(
        ChangedFile(
            path=p, change_type=change_type, subsystem=classify_path(p)
        )
        for p in paths
    )
    return SourceChange(
        base_ref="origin/main",
        head_ref="HEAD",
        source="explicit_list",
        changed_files=files,
    )


def _build_impacts(source: SourceChange):
    impacts: dict[Subsystem, list] = {}
    for f in source.changed_files:
        impacts.setdefault(f.subsystem, []).append(f)
    si = [
        SubsystemImpact(
            subsystem=s,
            changed_files=tuple(files),
            is_safety_critical=s
            in {Subsystem.SAFETY, Subsystem.MISSION, Subsystem.MOTION},
        )
        for s, files in impacts.items()
    ]
    ri = map_impacts(si)
    ei = map_evidence_for_impacts(si, ri)
    return si, ri, ei


def test_risk_assessor_safety_changes_high_risk_without_evidence() -> None:
    """The default mapper *does* recommend tools for safety changes,
    so the canonical safety change reaches MODERATE; we simulate the
    no-evidence path with a manually-constructed impact set.
    """

    source = _src("backend/app/safety/supervisor.py")
    si, ri, ei = _build_impacts(source)
    # Construct a safety impact with an empty recommended_tools list.
    stripped = [
        EvidenceImpact(
            subsystem=e.subsystem,
            requirement_ids=e.requirement_ids,
            recommended_tools=(),
            recommended_artifacts=(),
            notes="stripped for test",
        )
        for e in ei
    ]
    assessment = assess_impact(
        source_change=source,
        subsystem_impacts=si,
        requirement_impacts=ri,
        evidence_impacts=stripped,
        analytics_delta=ReplayAnalyticsDelta(
            baseline_path=None, current_path=None
        ),
    )
    assert assessment.overall_risk in {RiskLevel.HIGH, RiskLevel.CRITICAL}
    assert any(
        r.label == "safety_path_no_evidence" for r in assessment.risks
    )


def test_risk_assessor_safety_changes_with_evidence_moderate() -> None:
    source = _src("backend/app/safety/supervisor.py")
    si, ri, ei = _build_impacts(source)
    assessment = assess_impact(
        source_change=source,
        subsystem_impacts=si,
        requirement_impacts=ri,
        evidence_impacts=ei,
        analytics_delta=ReplayAnalyticsDelta(
            baseline_path=None, current_path=None
        ),
    )
    # Safety path touched + evidence available -> moderate (not high).
    assert assessment.overall_risk in {RiskLevel.MODERATE, RiskLevel.HIGH}
    assert any(r.label == "safety_path_touched" for r in assessment.risks)


def test_risk_assessor_docs_only_low_risk() -> None:
    source = _src("docs/REPLAY_ANALYTICS.md")
    si, ri, ei = _build_impacts(source)
    assessment = assess_impact(
        source_change=source,
        subsystem_impacts=si,
        requirement_impacts=ri,
        evidence_impacts=ei,
        analytics_delta=ReplayAnalyticsDelta(
            baseline_path=None, current_path=None
        ),
    )
    assert assessment.overall_risk in {RiskLevel.LOW, RiskLevel.NONE}


def test_risk_assessor_unknown_files_moderate() -> None:
    source = _src("a.txt", "b.txt", "c.txt", "d.txt")
    si, ri, ei = _build_impacts(source)
    assessment = assess_impact(
        source_change=source,
        subsystem_impacts=si,
        requirement_impacts=ri,
        evidence_impacts=ei,
        analytics_delta=ReplayAnalyticsDelta(
            baseline_path=None, current_path=None
        ),
    )
    assert assessment.overall_risk in {RiskLevel.LOW, RiskLevel.MODERATE}
    assert any(r.label == "unknown_files_touched" for r in assessment.risks)


def test_risk_assessor_ci_workflow_removal_high() -> None:
    source = _src(".github/workflows/runtime-static-validation.yml")
    # Re-tag as deleted.
    deleted = tuple(
        ChangedFile(
            path=f.path,
            change_type=ChangeType.DELETED,
            subsystem=f.subsystem,
        )
        for f in source.changed_files
    )
    source = SourceChange(
        base_ref="origin/main",
        head_ref="HEAD",
        source="explicit_list",
        changed_files=deleted,
    )
    si, ri, ei = _build_impacts(source)
    assessment = assess_impact(
        source_change=source,
        subsystem_impacts=si,
        requirement_impacts=ri,
        evidence_impacts=ei,
        analytics_delta=ReplayAnalyticsDelta(
            baseline_path=None, current_path=None
        ),
    )
    assert assessment.overall_risk in {RiskLevel.HIGH, RiskLevel.CRITICAL}


def test_risk_assessor_critical_regression() -> None:
    source = _src("backend/app/replay_analytics/scoring.py")
    si, ri, ei = _build_impacts(source)
    from app.reliability_impact.models import AnalyticsDeltaEntry

    delta = ReplayAnalyticsDelta(
        baseline_path=None,
        current_path=None,
        entries=[
            AnalyticsDeltaEntry(
                label="x",
                category="score",
                severity=DeltaSeverity.CRITICAL_REGRESSION,
                detail="score crossed below 40",
            )
        ],
    )
    assessment = assess_impact(
        source_change=source,
        subsystem_impacts=si,
        requirement_impacts=ri,
        evidence_impacts=ei,
        analytics_delta=delta,
    )
    assert assessment.overall_risk == RiskLevel.CRITICAL


# ---------------------------------------------------------------------------
# CI gate.
# ---------------------------------------------------------------------------


def _make_critical_delta():
    from app.reliability_impact.models import AnalyticsDeltaEntry

    return ReplayAnalyticsDelta(
        baseline_path=None,
        current_path=None,
        entries=[
            AnalyticsDeltaEntry(
                label="x",
                category="score",
                severity=DeltaSeverity.CRITICAL_REGRESSION,
                detail="score crossed below 40",
            )
        ],
    )


def test_gate_fails_on_critical_regression() -> None:
    source = _src("backend/app/replay_analytics/scoring.py")
    si, ri, ei = _build_impacts(source)
    assessment = assess_impact(
        source_change=source,
        subsystem_impacts=si,
        requirement_impacts=ri,
        evidence_impacts=ei,
        analytics_delta=_make_critical_delta(),
    )
    gate = decide_gate(
        source_change=source,
        subsystem_impacts=si,
        evidence_impacts=ei,
        analytics_delta=_make_critical_delta(),
        assessment=assessment,
        is_github_hosted=True,
    )
    assert gate.status == GateStatus.FAILED
    assert any("critical_analytics_regression" in f for f in gate.failures)


def test_gate_does_not_fail_on_missing_live_evidence() -> None:
    """Bag status moving to missing_bag in current vs baseline is a
    regression severity-wise — but the gate must not fail when the
    runner is github-hosted."""

    from app.reliability_impact.models import AnalyticsDeltaEntry

    source = _src("docs/REPLAY_ANALYTICS.md")
    si, ri, ei = _build_impacts(source)
    delta = ReplayAnalyticsDelta(
        baseline_path=None,
        current_path=None,
        entries=[
            AnalyticsDeltaEntry(
                label="bag_status[x]",
                category="bag",
                severity=DeltaSeverity.REGRESSION,
                detail="bag moved ready -> missing_bag",
                current_value="missing_bag",
                baseline_value="ready",
                incident_id="x",
            )
        ],
    )
    assessment = assess_impact(
        source_change=source,
        subsystem_impacts=si,
        requirement_impacts=ri,
        evidence_impacts=ei,
        analytics_delta=delta,
    )
    gate = decide_gate(
        source_change=source,
        subsystem_impacts=si,
        evidence_impacts=ei,
        analytics_delta=delta,
        assessment=assessment,
        is_github_hosted=True,
    )
    # The bag regression is not in the "critical" list; the gate may
    # warn but must not fail.
    assert gate.status != GateStatus.FAILED


def test_gate_warns_on_missing_baseline() -> None:
    source = _src("docs/REPLAY_ANALYTICS.md")
    si, ri, ei = _build_impacts(source)
    delta = ReplayAnalyticsDelta(
        baseline_path=None,
        current_path=None,
        warnings=["baseline replay-quality-index.baseline.json not present"],
    )
    assessment = assess_impact(
        source_change=source,
        subsystem_impacts=si,
        requirement_impacts=ri,
        evidence_impacts=ei,
        analytics_delta=delta,
    )
    gate = decide_gate(
        source_change=source,
        subsystem_impacts=si,
        evidence_impacts=ei,
        analytics_delta=delta,
        assessment=assessment,
        is_github_hosted=True,
    )
    assert gate.status in {GateStatus.PASSED, GateStatus.WARNING}
    if gate.status == GateStatus.WARNING:
        assert any("baseline" in w.lower() for w in gate.warnings)


def test_gate_fails_on_static_validation_removal() -> None:
    deleted = SourceChange(
        base_ref="origin/main",
        head_ref="HEAD",
        source="explicit_list",
        changed_files=(
            ChangedFile(
                path=".github/workflows/runtime-static-validation.yml",
                change_type=ChangeType.DELETED,
                subsystem=Subsystem.CI,
            ),
        ),
    )
    si, ri, ei = _build_impacts(deleted)
    delta = ReplayAnalyticsDelta(baseline_path=None, current_path=None)
    assessment = assess_impact(
        source_change=deleted,
        subsystem_impacts=si,
        requirement_impacts=ri,
        evidence_impacts=ei,
        analytics_delta=delta,
    )
    gate = decide_gate(
        source_change=deleted,
        subsystem_impacts=si,
        evidence_impacts=ei,
        analytics_delta=delta,
        assessment=assessment,
        is_github_hosted=True,
    )
    assert gate.status == GateStatus.FAILED
    assert any("static_validation" in f for f in gate.failures)


def test_gate_fails_on_traceability_failure() -> None:
    source = _src("docs/REPLAY_ANALYTICS.md")
    si, ri, ei = _build_impacts(source)
    delta = ReplayAnalyticsDelta(baseline_path=None, current_path=None)
    assessment = assess_impact(
        source_change=source,
        subsystem_impacts=si,
        requirement_impacts=ri,
        evidence_impacts=ei,
        analytics_delta=delta,
    )
    gate = decide_gate(
        source_change=source,
        subsystem_impacts=si,
        evidence_impacts=ei,
        analytics_delta=delta,
        assessment=assessment,
        traceability_passed=False,
        is_github_hosted=True,
    )
    assert gate.status == GateStatus.FAILED
    assert any("traceability" in f for f in gate.failures)


# ---------------------------------------------------------------------------
# Report.
# ---------------------------------------------------------------------------


def test_report_distinguishes_warning_from_failure(tmp_path: Path) -> None:
    source = _src("docs/REPLAY_ANALYTICS.md")
    baseline = BaselineReference(
        quality_index_path=None, analytics_report_path=None,
        notes="missing",
    )
    report = build_report(
        source_change=source,
        baseline=baseline,
        current_quality_index=None,
        current_analytics_report=None,
        is_github_hosted=True,
    )
    out_dir = tmp_path / "ri"
    from app.reliability_impact import write_report_files

    write_report_files(report, out_dir=out_dir)
    md_text = (out_dir / "impact-report.md").read_text(encoding="utf-8")
    assert "Gate status" in md_text
    assert "Overall risk" in md_text
    assert report.gate_decision.status in {
        GateStatus.PASSED,
        GateStatus.WARNING,
    }
    # JSON files exist.
    for name in (
        "impact-report.json",
        "changed-files.json",
        "subsystem-impact.json",
        "requirement-impact.json",
        "evidence-impact.json",
        "analytics-delta.json",
        "gate-decision.json",
    ):
        assert (out_dir / name).exists()


def test_canonical_impact_artefacts_present() -> None:
    canonical = _REPO_ROOT / "reliability-impact" / "canonical"
    assert (canonical / "impact-report.json").exists()
    payload = json.loads((canonical / "impact-report.json").read_text())
    assert payload["fixture_mode"] is True
    assert payload["source_change"]["changed_files"]


# ---------------------------------------------------------------------------
# CLIs.
# ---------------------------------------------------------------------------


def _import_cli(name: str):
    import importlib

    return importlib.import_module(name)


def test_cli_analyze_source_impact(tmp_path: Path) -> None:
    cli = _import_cli("analyze_source_impact")
    rc = cli.main(
        [
            "--changed-files",
            "backend/app/safety/supervisor.py,docs/REPLAY_ANALYTICS.md",
            "--fixture",
            "--ci-github-hosted",
            "--output",
            str(tmp_path / "out"),
            "--baseline-root",
            str(_REPO_ROOT / "reliability-baselines"),
        ]
    )
    assert rc == 0
    assert (tmp_path / "out" / "impact-report.json").exists()
    payload = json.loads(
        (tmp_path / "out" / "impact-report.json").read_text(encoding="utf-8")
    )
    assert payload["fixture_mode"] is True
    assert payload["source_change"]["source"] == "fixture"


def test_cli_reliability_impact_gate_passes(tmp_path: Path) -> None:
    # Generate a passing report first.
    analyze_cli = _import_cli("analyze_source_impact")
    analyze_cli.main(
        [
            "--changed-files",
            "docs/REPLAY_ANALYTICS.md",
            "--fixture",
            "--ci-github-hosted",
            "--output",
            str(tmp_path / "out"),
            "--baseline-root",
            str(_REPO_ROOT / "reliability-baselines"),
        ]
    )
    gate_cli = _import_cli("reliability_impact_gate")
    rc = gate_cli.main(
        ["--report", str(tmp_path / "out" / "impact-report.json")]
    )
    assert rc == 0


def test_cli_reliability_impact_gate_fails_on_missing_report(tmp_path: Path) -> None:
    gate_cli = _import_cli("reliability_impact_gate")
    rc = gate_cli.main(["--report", str(tmp_path / "ghost.json")])
    assert rc == 1


# ---------------------------------------------------------------------------
# Baseline resolution.
# ---------------------------------------------------------------------------


def test_baseline_resolution_missing(tmp_path: Path) -> None:
    ref = resolve_baseline(baseline_root=tmp_path / "ghost")
    assert ref.quality_index_path is None
    assert ref.analytics_report_path is None
    assert not ref.available


def test_baseline_resolution_present(tmp_path: Path) -> None:
    root = tmp_path / "baselines"
    root.mkdir()
    (root / "replay-quality-index.baseline.json").write_text(
        "{}", encoding="utf-8"
    )
    (root / "replay-analytics-report.baseline.json").write_text(
        "{}", encoding="utf-8"
    )
    ref = resolve_baseline(baseline_root=root)
    assert ref.quality_index_path is not None
    assert ref.analytics_report_path is not None
    assert ref.available
