"""Phase 10 programme-review tests.

The tests run without ROS, Gazebo, Foxglove, or network. They use
deterministic fixture timestamps (never wall-clock) and synthetic
incident / reliability-impact / replay-review payloads.

Coverage:

* history loader — missing dirs, malformed JSON, duplicates,
  chronological ordering;
* trend analyser — improving / degrading / stable / volatile /
  insufficient_history, determinism, rolling windows;
* drift detector — score critical / regression, missing-bag
  growth, static-only growth, unknown-file growth, insufficient
  history is informational;
* governance health — strong when all disciplines pass,
  concerning on repeat failures, triggering artefacts recorded;
* freshness — fresh / stale / unknown, supplied reference time
  drives the result, no wall-clock side-effects;
* subsystem risk — frequency, severity ranking, no causal claims;
* coverage evolution — origin preservation, mixed origin labelling,
  static-only stays static-only;
* gate history — outcome counts, volatility, unknown when no data;
* aggregate report — labels insufficient history, never fails on
  partial history;
* CI workflow shape — github-hosted, dispatch-supported.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

import pytest
import yaml


_REPO_ROOT = Path(__file__).resolve().parents[2]
_TOOLS_DIR = _REPO_ROOT / "rover_ws" / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))


from app.programme_review import (  # noqa: E402
    DriftSeverity,
    FreshnessStatus,
    GateVolatility,
    GovernanceHealth,
    PROGRAMME_CERTIFICATION_DISCLAIMER,
    TrendCategory,
    aggregate_subsystem_risk,
    assess_freshness,
    assess_governance_health,
    build_coverage_evolution,
    build_gate_history,
    build_programme_review,
    build_trend_report,
    detect_drift,
    load_history,
    write_programme_review_bundle,
)
from app.programme_review.history_loader import (  # noqa: E402
    DEFAULT_INCIDENTS_ROOT,
)
from app.programme_review.trend_analysis import (  # noqa: E402
    build_series_from_payloads,
)


# ---------------------------------------------------------------------------
# Fixture helpers — write synthetic upstream artefacts.
# ---------------------------------------------------------------------------


def _ts(year: int = 2026, month: int = 5, day: int = 1, hour: int = 0) -> str:
    return datetime(year, month, day, hour, tzinfo=timezone.utc).isoformat(
        timespec="seconds"
    )


def _write_reliability_impact(
    root: Path,
    *,
    name: str,
    generated_at: str = "",
    gate_status: str = "passed",
    risks: Optional[list[dict]] = None,
    subsystems: Optional[list[str]] = None,
    requirement_ids: Optional[list[str]] = None,
    unknown_files: int = 0,
) -> Path:
    bundle = root / name
    bundle.mkdir(parents=True, exist_ok=True)
    changed_files = [
        {"path": "backend/app/safety/supervisor.py", "subsystem": "safety", "change_type": "modified"}
    ]
    for i in range(unknown_files):
        changed_files.append(
            {"path": f"random/{i}.txt", "subsystem": "unknown", "change_type": "modified"}
        )
    payload = {
        "generated_at_utc": generated_at or _ts(),
        "head_ref": f"head/{name}",
        "base_ref": "origin/main",
        "fixture_mode": True,
        "gate_decision": {"status": gate_status, "failures": [], "warnings": []},
        "assessment": {"overall_risk": "moderate", "risks": risks or []},
        "source_change": {
            "base_ref": "origin/main",
            "head_ref": f"head/{name}",
            "source": "fixture",
            "changed_files": changed_files,
        },
        "subsystem_impacts": [
            {
                "subsystem": s,
                "is_safety_critical": s in {"safety", "mission", "motion"},
                "changed_files": [],
            }
            for s in (subsystems or ["safety"])
        ],
        "requirement_impacts": [
            {"subsystem": "safety", "requirement_ids": list(requirement_ids or []), "notes": ""}
        ],
        "evidence_impacts": [
            {
                "subsystem": "safety",
                "requirement_ids": list(requirement_ids or []),
                "recommended_tools": ["tools/audit_command_path.py"],
                "recommended_artifacts": ["evidence/scenarios/"],
                "notes": "",
            }
        ],
        "analytics_delta": {"severity": "neutral", "entries": [], "summary_counts": {}},
    }
    (bundle / "impact-report.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )
    return bundle


def _write_replay_review(
    incidents_root: Path,
    *,
    incident_id: str,
    generated_at: str = "",
    bag_status: str = "missing_bag",
    evidence_origin: str = "scenario-evidence",
    coverage_status: str = "missing_bag",
    review_completion_status: str = "not_started",
    score: Optional[int] = None,
    status_counts: Optional[dict] = None,
) -> Path:
    bundle = incidents_root / incident_id
    bundle.mkdir(parents=True, exist_ok=True)
    payload = {
        "incident_id": incident_id,
        "scenario_id": f"scn-{incident_id}",
        "generated_at_utc": generated_at or _ts(),
        "bag_status": bag_status,
        "replay_execution_status": bag_status,
        "evidence_origin": evidence_origin,
        "coverage_status": coverage_status,
        "review_completion_status": review_completion_status,
        "status_counts": status_counts or {"passed": 5, "failed": 0, "warning": 0},
        "quality_score": score if score is not None else 0,
    }
    (bundle / "replay-review-report.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )
    return bundle


def _write_incident_report(
    incidents_root: Path,
    *,
    incident_id: str,
    review_completion_status: str = "not_started",
    generated_at: str = "",
) -> Path:
    bundle = incidents_root / incident_id
    bundle.mkdir(parents=True, exist_ok=True)
    payload = {
        "incident_id": incident_id,
        "generated_at_utc": generated_at or _ts(),
        "review_completion_status": review_completion_status,
    }
    (bundle / "incident-report.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )
    return bundle


def _write_analytics_report(
    path: Path,
    *,
    generated_at: str,
    scores: list[int],
) -> Path:
    payload = {
        "generated_at_utc": generated_at,
        "incident_count": len(scores),
        "scores": [
            {"incident_id": f"inc-{i}", "score": s, "blocking_gaps": []}
            for i, s in enumerate(scores)
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _write_qualification_summary(
    runtime_root: Path,
    *,
    run_id: str,
    generated_at: str,
    passed: int = 8,
    failed: int = 0,
) -> Path:
    bundle = runtime_root / run_id
    bundle.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_id": run_id,
        "generated_at_utc": generated_at,
        "overall_status": "failed" if failed else "passed",
        "status_counts": {"passed": passed, "failed": failed, "warning": 0, "not_executed": 0},
    }
    (bundle / "qualification-summary.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )
    return bundle


# ---------------------------------------------------------------------------
# History loader.
# ---------------------------------------------------------------------------


def test_history_loader_handles_missing_dir(tmp_path: Path) -> None:
    history = load_history(
        reliability_impact_roots=[tmp_path / "ghost"],
        replay_analytics_paths=[tmp_path / "ghost.json"],
        runtime_evidence_root=tmp_path / "ghost-runtime",
        incidents_root=tmp_path / "ghost-incidents",
    )
    assert history.counts() == {
        "reliability_impact": 0,
        "replay_analytics": 0,
        "runtime_qualification": 0,
        "replay_review": 0,
        "incident": 0,
    }


def test_history_loader_isolates_malformed_report(tmp_path: Path) -> None:
    impact_root = tmp_path / "ri"
    good = _write_reliability_impact(
        impact_root, name="good", generated_at=_ts(day=2)
    )
    bad = impact_root / "bad"
    bad.mkdir()
    (bad / "impact-report.json").write_text("{ not json", encoding="utf-8")
    history = load_history(
        reliability_impact_roots=[impact_root],
        replay_analytics_paths=[tmp_path / "missing-analytics.json"],
        runtime_evidence_root=tmp_path / "ghost",
        incidents_root=tmp_path / "ghost-incidents",
    )
    assert len(history.reliability_impact) == 1
    assert any("did not parse" in w for w in history.warnings)


def test_history_loader_orders_by_generated_at(tmp_path: Path) -> None:
    impact_root = tmp_path / "ri"
    _write_reliability_impact(
        impact_root, name="b", generated_at=_ts(day=2)
    )
    _write_reliability_impact(
        impact_root, name="a", generated_at=_ts(day=1)
    )
    history = load_history(
        reliability_impact_roots=[impact_root],
        replay_analytics_paths=[tmp_path / "missing.json"],
        runtime_evidence_root=tmp_path / "ghost",
        incidents_root=tmp_path / "ghost-incidents",
    )
    assert [r.record_id for r in history.reliability_impact] == [
        "origin/main..head/a",
        "origin/main..head/b",
    ]


def test_history_loader_detects_duplicates(tmp_path: Path) -> None:
    impact_root = tmp_path / "ri"
    _write_reliability_impact(
        impact_root, name="a", generated_at=_ts(day=1)
    )
    # Second bundle with the same head_ref (so the same record_id).
    bundle = impact_root / "a-twin"
    bundle.mkdir()
    payload = {
        "generated_at_utc": _ts(day=2),
        "head_ref": "head/a",
        "base_ref": "origin/main",
        "gate_decision": {"status": "passed"},
        "subsystem_impacts": [],
        "requirement_impacts": [],
        "evidence_impacts": [],
        "source_change": {
            "base_ref": "origin/main",
            "head_ref": "head/a",
            "source": "fixture",
            "changed_files": [],
        },
        "assessment": {"overall_risk": "none", "risks": []},
        "analytics_delta": {"severity": "neutral", "entries": []},
    }
    (bundle / "impact-report.json").write_text(json.dumps(payload), encoding="utf-8")
    history = load_history(
        reliability_impact_roots=[impact_root],
        replay_analytics_paths=[tmp_path / "missing.json"],
        runtime_evidence_root=tmp_path / "ghost",
        incidents_root=tmp_path / "ghost-incidents",
    )
    assert any("duplicate" in w for w in history.warnings)
    for record in history.reliability_impact:
        if record.record_id == "origin/main..head/a":
            assert "duplicate_record_id" in record.notes


def test_history_loader_loads_replay_review_and_incident(tmp_path: Path) -> None:
    incidents_root = tmp_path / "incidents"
    _write_replay_review(
        incidents_root, incident_id="x", generated_at=_ts(day=1)
    )
    _write_incident_report(
        incidents_root, incident_id="x", generated_at=_ts(day=1)
    )
    history = load_history(
        reliability_impact_roots=[tmp_path / "ghost"],
        replay_analytics_paths=[tmp_path / "missing.json"],
        runtime_evidence_root=tmp_path / "ghost",
        incidents_root=incidents_root,
    )
    assert history.counts()["replay_review"] == 1
    assert history.counts()["incident"] == 1


# ---------------------------------------------------------------------------
# Trend analysis.
# ---------------------------------------------------------------------------


def _series_from(values: list[Optional[float]]):
    """Build a TrendSeries directly from a list of values (timestamps shaped per index)."""

    from app.programme_review.models import HistoryRecord

    records = [
        HistoryRecord(
            record_type="x",
            source_path=Path("/dev/null"),
            payload={},
            generated_at_utc=_ts(day=i + 1),
            record_id=f"r{i}",
        )
        for i in range(len(values))
    ]
    return build_series_from_payloads(
        label="x", records=records, value_resolver=lambda r: values[int(r.record_id[1:])]
    )


def test_trend_improving() -> None:
    series = _series_from([10.0, 20.0, 30.0])
    assert series.category == TrendCategory.IMPROVING


def test_trend_degrading() -> None:
    series = _series_from([60.0, 40.0, 20.0])
    assert series.category == TrendCategory.DEGRADING


def test_trend_stable() -> None:
    series = _series_from([50.0, 51.0, 49.0])
    assert series.category == TrendCategory.STABLE


def test_trend_volatile() -> None:
    series = _series_from([20.0, 70.0, 20.0, 70.0])
    assert series.category == TrendCategory.VOLATILE


def test_trend_insufficient_history() -> None:
    series = _series_from([50.0])
    assert series.category == TrendCategory.INSUFFICIENT_HISTORY


def test_trend_insufficient_history_when_all_unavailable() -> None:
    series = _series_from([None, None, None])
    assert series.category == TrendCategory.INSUFFICIENT_HISTORY


def test_trend_rolling_windows() -> None:
    series = _series_from([60.0, 55.0, 50.0, 45.0, 30.0])
    assert series.category == TrendCategory.DEGRADING
    # Rolling-3 over the last 3 values (50, 45, 30) is degrading.
    assert series.rolling_3 == TrendCategory.DEGRADING


def test_trend_is_deterministic() -> None:
    a = _series_from([10.0, 20.0, 30.0])
    b = _series_from([10.0, 20.0, 30.0])
    assert a.category == b.category
    assert a.rolling_3 == b.rolling_3
    assert a.rolling_5 == b.rolling_5


# ---------------------------------------------------------------------------
# Drift detection.
# ---------------------------------------------------------------------------


def _history_with_analytics_scores(
    tmp_path: Path, *, scores_per_run: list[list[int]]
):
    impact_root = tmp_path / "ri"
    for idx in range(len(scores_per_run)):
        _write_reliability_impact(
            impact_root, name=f"r{idx}", generated_at=_ts(day=idx + 1)
        )
    analytics_paths: list[Path] = []
    for idx, scores in enumerate(scores_per_run):
        path = tmp_path / f"analytics-{idx}.json"
        _write_analytics_report(
            path, generated_at=_ts(day=idx + 1), scores=scores
        )
        analytics_paths.append(path)
    history = load_history(
        reliability_impact_roots=[impact_root],
        replay_analytics_paths=analytics_paths,
        runtime_evidence_root=tmp_path / "ghost",
        incidents_root=tmp_path / "ghost-incidents",
    )
    return history


def test_drift_replay_score_critical(tmp_path: Path) -> None:
    history = _history_with_analytics_scores(
        tmp_path, scores_per_run=[[80, 90, 100], [40, 30, 20]]
    )
    trend = build_trend_report(history)
    report = detect_drift(history=history, trend_report=trend)
    assert report.severity == DriftSeverity.CRITICAL_REGRESSION
    assert any(
        f.label == "analytics_score_critical_drop" for f in report.findings
    )


def test_drift_replay_score_regression(tmp_path: Path) -> None:
    history = _history_with_analytics_scores(
        tmp_path, scores_per_run=[[80, 80, 80], [70, 65, 60]]
    )
    trend = build_trend_report(history)
    report = detect_drift(history=history, trend_report=trend)
    assert any(
        f.label == "analytics_score_regression" for f in report.findings
    )


def test_drift_insufficient_history_is_informational(tmp_path: Path) -> None:
    history = _history_with_analytics_scores(
        tmp_path, scores_per_run=[[80, 80, 80]]
    )
    trend = build_trend_report(history)
    report = detect_drift(history=history, trend_report=trend)
    # Only the score detector should fire informational.
    assert all(
        f.severity == DriftSeverity.INFORMATIONAL
        for f in report.findings
    )


def test_drift_increasing_missing_bag(tmp_path: Path) -> None:
    incidents_root = tmp_path / "incidents"
    _write_replay_review(
        incidents_root,
        incident_id="a",
        generated_at=_ts(day=1),
        bag_status="ready",
        evidence_origin="bag-backed",
    )
    _write_replay_review(
        incidents_root,
        incident_id="b",
        generated_at=_ts(day=2),
        bag_status="missing_bag",
        evidence_origin="scenario-evidence",
    )
    history = load_history(
        reliability_impact_roots=[tmp_path / "ghost"],
        replay_analytics_paths=[tmp_path / "ghost.json"],
        runtime_evidence_root=tmp_path / "ghost",
        incidents_root=incidents_root,
    )
    trend = build_trend_report(history)
    report = detect_drift(history=history, trend_report=trend)
    assert any(
        f.label == "missing_bag_frequency_increasing" for f in report.findings
    )


def test_drift_increasing_static_only(tmp_path: Path) -> None:
    incidents_root = tmp_path / "incidents"
    _write_replay_review(
        incidents_root,
        incident_id="a",
        generated_at=_ts(day=1),
        bag_status="ready",
    )
    _write_replay_review(
        incidents_root,
        incident_id="b",
        generated_at=_ts(day=2),
        bag_status="static_only",
    )
    history = load_history(
        reliability_impact_roots=[tmp_path / "ghost"],
        replay_analytics_paths=[tmp_path / "ghost.json"],
        runtime_evidence_root=tmp_path / "ghost",
        incidents_root=incidents_root,
    )
    trend = build_trend_report(history)
    report = detect_drift(history=history, trend_report=trend)
    assert any(
        f.label == "static_only_dependency_increasing" for f in report.findings
    )


def test_drift_growing_unknown_file_count(tmp_path: Path) -> None:
    impact_root = tmp_path / "ri"
    _write_reliability_impact(impact_root, name="r1", generated_at=_ts(day=1), unknown_files=0)
    _write_reliability_impact(impact_root, name="r2", generated_at=_ts(day=2), unknown_files=5)
    history = load_history(
        reliability_impact_roots=[impact_root],
        replay_analytics_paths=[tmp_path / "ghost.json"],
        runtime_evidence_root=tmp_path / "ghost",
        incidents_root=tmp_path / "ghost-incidents",
    )
    trend = build_trend_report(history)
    report = detect_drift(history=history, trend_report=trend)
    assert any(
        f.label == "unknown_file_count_growing" for f in report.findings
    )


# ---------------------------------------------------------------------------
# Governance health.
# ---------------------------------------------------------------------------


def test_governance_strong_when_all_disciplines_pass(tmp_path: Path) -> None:
    impact_root = tmp_path / "ri"
    incidents_root = tmp_path / "incidents"
    runtime_root = tmp_path / "runtime"
    _write_reliability_impact(
        impact_root,
        name="r1",
        generated_at=_ts(day=1),
        gate_status="passed",
        requirement_ids=["REQ-SAFE-001", "REQ-SAFE-002", "REQ-SAFE-003", "REQ-SAFE-004", "REQ-SAFE-005"],
    )
    _write_replay_review(
        incidents_root,
        incident_id="x",
        generated_at=_ts(day=1),
        bag_status="ready",
        evidence_origin="bag-backed",
    )
    _write_incident_report(
        incidents_root,
        incident_id="x",
        review_completion_status="completed",
        generated_at=_ts(day=1),
    )
    _write_qualification_summary(
        runtime_root, run_id="r1", generated_at=_ts(day=1), passed=10, failed=0
    )
    history = load_history(
        reliability_impact_roots=[impact_root],
        replay_analytics_paths=[tmp_path / "ghost.json"],
        runtime_evidence_root=runtime_root,
        incidents_root=incidents_root,
    )
    trend = build_trend_report(history)
    report = detect_drift(history=history, trend_report=trend)
    assessment = assess_governance_health(history=history, drift_report=report)
    assert assessment.overall == GovernanceHealth.STRONG


def test_governance_concerning_on_repeat_failures(tmp_path: Path) -> None:
    impact_root = tmp_path / "ri"
    for i in range(3):
        _write_reliability_impact(
            impact_root,
            name=f"r{i}",
            generated_at=_ts(day=i + 1),
            gate_status="failed",
        )
    history = load_history(
        reliability_impact_roots=[impact_root],
        replay_analytics_paths=[tmp_path / "ghost.json"],
        runtime_evidence_root=tmp_path / "ghost",
        incidents_root=tmp_path / "ghost-incidents",
    )
    trend = build_trend_report(history)
    drift = detect_drift(history=history, trend_report=trend)
    health = assess_governance_health(history=history, drift_report=drift)
    assert health.overall in {GovernanceHealth.CONCERNING, GovernanceHealth.WEAK}


def test_governance_records_triggering_artifacts(tmp_path: Path) -> None:
    impact_root = tmp_path / "ri"
    _write_reliability_impact(
        impact_root, name="r1", generated_at=_ts(day=1), gate_status="failed"
    )
    history = load_history(
        reliability_impact_roots=[impact_root],
        replay_analytics_paths=[tmp_path / "ghost.json"],
        runtime_evidence_root=tmp_path / "ghost",
        incidents_root=tmp_path / "ghost-incidents",
    )
    trend = build_trend_report(history)
    drift = detect_drift(history=history, trend_report=trend)
    health = assess_governance_health(history=history, drift_report=drift)
    ci = next(d for d in health.disciplines if d.category.value == "ci")
    assert ci.reasons


# ---------------------------------------------------------------------------
# Freshness.
# ---------------------------------------------------------------------------


def test_freshness_fresh_when_recent(tmp_path: Path) -> None:
    impact_root = tmp_path / "ri"
    _write_reliability_impact(
        impact_root, name="r1", generated_at=_ts(day=1)
    )
    history = load_history(
        reliability_impact_roots=[impact_root],
        replay_analytics_paths=[tmp_path / "ghost.json"],
        runtime_evidence_root=tmp_path / "ghost",
        incidents_root=tmp_path / "ghost-incidents",
    )
    report = assess_freshness(
        history=history,
        reference_time_utc=datetime(2026, 5, 2, tzinfo=timezone.utc),
    )
    assert all(e.status == FreshnessStatus.FRESH for e in report.entries)


def test_freshness_stale_when_older_than_threshold(tmp_path: Path) -> None:
    impact_root = tmp_path / "ri"
    _write_reliability_impact(
        impact_root, name="r1", generated_at=_ts(day=1)
    )
    history = load_history(
        reliability_impact_roots=[impact_root],
        replay_analytics_paths=[tmp_path / "ghost.json"],
        runtime_evidence_root=tmp_path / "ghost",
        incidents_root=tmp_path / "ghost-incidents",
    )
    report = assess_freshness(
        history=history,
        reference_time_utc=datetime(2027, 1, 1, tzinfo=timezone.utc),
    )
    assert any(e.status == FreshnessStatus.STALE for e in report.entries)


def test_freshness_unknown_when_no_timestamp(tmp_path: Path) -> None:
    impact_root = tmp_path / "ri"
    bundle = impact_root / "r1"
    bundle.mkdir(parents=True)
    payload = {
        "head_ref": "h",
        "base_ref": "origin/main",
        "gate_decision": {"status": "passed"},
        "subsystem_impacts": [],
        "requirement_impacts": [],
        "evidence_impacts": [],
        "source_change": {
            "base_ref": "origin/main",
            "head_ref": "h",
            "source": "fixture",
            "changed_files": [],
        },
        "assessment": {"overall_risk": "none", "risks": []},
        "analytics_delta": {"severity": "neutral"},
    }
    (bundle / "impact-report.json").write_text(json.dumps(payload), encoding="utf-8")
    history = load_history(
        reliability_impact_roots=[impact_root],
        replay_analytics_paths=[tmp_path / "ghost.json"],
        runtime_evidence_root=tmp_path / "ghost",
        incidents_root=tmp_path / "ghost-incidents",
    )
    report = assess_freshness(
        history=history,
        reference_time_utc=datetime(2026, 5, 2, tzinfo=timezone.utc),
    )
    assert all(e.status == FreshnessStatus.UNKNOWN for e in report.entries)


def test_freshness_uses_supplied_now(tmp_path: Path) -> None:
    impact_root = tmp_path / "ri"
    _write_reliability_impact(
        impact_root, name="r1", generated_at=_ts(day=1)
    )
    history = load_history(
        reliability_impact_roots=[impact_root],
        replay_analytics_paths=[tmp_path / "ghost.json"],
        runtime_evidence_root=tmp_path / "ghost",
        incidents_root=tmp_path / "ghost-incidents",
    )
    fresh = assess_freshness(
        history=history,
        reference_time_utc=datetime(2026, 5, 2, tzinfo=timezone.utc),
    )
    stale = assess_freshness(
        history=history,
        reference_time_utc=datetime(2027, 5, 2, tzinfo=timezone.utc),
    )
    assert fresh.entries[0].status == FreshnessStatus.FRESH
    assert stale.entries[0].status == FreshnessStatus.STALE


# ---------------------------------------------------------------------------
# Subsystem risk.
# ---------------------------------------------------------------------------


def _ri_with_risks(
    impact_root: Path,
    *,
    name: str,
    generated_at: str,
    subsystems: list[str],
    risk_level: str,
):
    return _write_reliability_impact(
        impact_root,
        name=name,
        generated_at=generated_at,
        subsystems=subsystems,
        risks=[
            {
                "label": f"risk[{name}]",
                "level": risk_level,
                "rationale": "fixture",
            }
        ],
    )


def test_subsystem_risk_counts_frequency(tmp_path: Path) -> None:
    impact_root = tmp_path / "ri"
    _ri_with_risks(impact_root, name="a", generated_at=_ts(day=1), subsystems=["safety"], risk_level="low")
    _ri_with_risks(impact_root, name="b", generated_at=_ts(day=2), subsystems=["safety", "mission"], risk_level="moderate")
    _ri_with_risks(impact_root, name="c", generated_at=_ts(day=3), subsystems=["mission"], risk_level="moderate")
    history = load_history(
        reliability_impact_roots=[impact_root],
        replay_analytics_paths=[tmp_path / "ghost.json"],
        runtime_evidence_root=tmp_path / "ghost",
        incidents_root=tmp_path / "ghost-incidents",
    )
    report = aggregate_subsystem_risk(history)
    by_subsystem = {row.subsystem: row for row in report.rows}
    assert by_subsystem["safety"].frequency == 2
    assert by_subsystem["mission"].frequency == 2


def test_subsystem_risk_records_repeat_regressions(tmp_path: Path) -> None:
    impact_root = tmp_path / "ri"
    _ri_with_risks(impact_root, name="a", generated_at=_ts(day=1), subsystems=["safety"], risk_level="high")
    _ri_with_risks(impact_root, name="b", generated_at=_ts(day=2), subsystems=["safety"], risk_level="critical")
    history = load_history(
        reliability_impact_roots=[impact_root],
        replay_analytics_paths=[tmp_path / "ghost.json"],
        runtime_evidence_root=tmp_path / "ghost",
        incidents_root=tmp_path / "ghost-incidents",
    )
    report = aggregate_subsystem_risk(history)
    row = next(r for r in report.rows if r.subsystem == "safety")
    assert row.repeat_regression_count == 2


def test_subsystem_risk_ranks_by_severity(tmp_path: Path) -> None:
    impact_root = tmp_path / "ri"
    _ri_with_risks(impact_root, name="a", generated_at=_ts(day=1), subsystems=["mission"], risk_level="low")
    _ri_with_risks(impact_root, name="b", generated_at=_ts(day=2), subsystems=["safety"], risk_level="critical")
    history = load_history(
        reliability_impact_roots=[impact_root],
        replay_analytics_paths=[tmp_path / "ghost.json"],
        runtime_evidence_root=tmp_path / "ghost",
        incidents_root=tmp_path / "ghost-incidents",
    )
    report = aggregate_subsystem_risk(history)
    # safety must come first because it carries a critical risk.
    assert report.rows[0].subsystem == "safety"


def test_subsystem_risk_never_infers_causality(tmp_path: Path) -> None:
    """The aggregator records observations but never claims causal links.

    Verified by checking the row API: there is no ``cause`` field and
    the representative_artifacts list is bounded by the actual
    artefact paths.
    """

    impact_root = tmp_path / "ri"
    _ri_with_risks(impact_root, name="a", generated_at=_ts(day=1), subsystems=["safety"], risk_level="critical")
    history = load_history(
        reliability_impact_roots=[impact_root],
        replay_analytics_paths=[tmp_path / "ghost.json"],
        runtime_evidence_root=tmp_path / "ghost",
        incidents_root=tmp_path / "ghost-incidents",
    )
    report = aggregate_subsystem_risk(history)
    row = report.rows[0]
    # ``representative_artifacts`` cites real paths and is bounded by
    # the actual artefact list (≤ 3).
    assert len(row.representative_artifacts) <= 3
    payload = row.as_dict()
    assert "cause" not in payload
    assert "blame" not in payload


# ---------------------------------------------------------------------------
# Coverage evolution.
# ---------------------------------------------------------------------------


def test_coverage_evolution_preserves_origin(tmp_path: Path) -> None:
    incidents_root = tmp_path / "incidents"
    _write_replay_review(
        incidents_root,
        incident_id="x",
        generated_at=_ts(day=1),
        bag_status="ready",
        evidence_origin="bag-backed",
    )
    history = load_history(
        reliability_impact_roots=[tmp_path / "ghost"],
        replay_analytics_paths=[tmp_path / "ghost.json"],
        runtime_evidence_root=tmp_path / "ghost",
        incidents_root=incidents_root,
    )
    report = build_coverage_evolution(history)
    assert report.entries[0].evidence_origin == "bag-backed"


def test_coverage_evolution_labels_mixed_origin(tmp_path: Path) -> None:
    incidents_root = tmp_path / "incidents"
    _write_replay_review(
        incidents_root, incident_id="a", generated_at=_ts(day=1), evidence_origin="bag-backed"
    )
    _write_replay_review(
        incidents_root, incident_id="b", generated_at=_ts(day=2), evidence_origin="scenario-evidence"
    )
    history = load_history(
        reliability_impact_roots=[tmp_path / "ghost"],
        replay_analytics_paths=[tmp_path / "ghost.json"],
        runtime_evidence_root=tmp_path / "ghost",
        incidents_root=incidents_root,
    )
    report = build_coverage_evolution(history)
    assert report.origin_mix_label == "mixed_origin"


def test_coverage_evolution_static_only_stays_static_only(tmp_path: Path) -> None:
    incidents_root = tmp_path / "incidents"
    _write_replay_review(
        incidents_root,
        incident_id="x",
        generated_at=_ts(day=1),
        bag_status="static_only",
        evidence_origin="scenario-evidence",
    )
    history = load_history(
        reliability_impact_roots=[tmp_path / "ghost"],
        replay_analytics_paths=[tmp_path / "ghost.json"],
        runtime_evidence_root=tmp_path / "ghost",
        incidents_root=incidents_root,
    )
    report = build_coverage_evolution(history)
    assert report.origin_mix_label == "static_only_only"
    assert report.entries[0].bag_status == "static_only"


# ---------------------------------------------------------------------------
# Gate history.
# ---------------------------------------------------------------------------


def test_gate_history_counts_outcomes(tmp_path: Path) -> None:
    impact_root = tmp_path / "ri"
    _write_reliability_impact(impact_root, name="a", generated_at=_ts(day=1), gate_status="passed")
    _write_reliability_impact(impact_root, name="b", generated_at=_ts(day=2), gate_status="warning")
    _write_reliability_impact(impact_root, name="c", generated_at=_ts(day=3), gate_status="failed")
    history = load_history(
        reliability_impact_roots=[impact_root],
        replay_analytics_paths=[tmp_path / "ghost.json"],
        runtime_evidence_root=tmp_path / "ghost",
        incidents_root=tmp_path / "ghost-incidents",
    )
    report = build_gate_history(history)
    assert report.pass_count == 1
    assert report.warning_count == 1
    assert report.failure_count == 1


def test_gate_history_volatility_steady(tmp_path: Path) -> None:
    impact_root = tmp_path / "ri"
    for i in range(3):
        _write_reliability_impact(
            impact_root, name=f"r{i}", generated_at=_ts(day=i + 1), gate_status="passed"
        )
    history = load_history(
        reliability_impact_roots=[impact_root],
        replay_analytics_paths=[tmp_path / "ghost.json"],
        runtime_evidence_root=tmp_path / "ghost",
        incidents_root=tmp_path / "ghost-incidents",
    )
    report = build_gate_history(history)
    assert report.volatility == GateVolatility.STEADY


def test_gate_history_volatility_oscillating(tmp_path: Path) -> None:
    impact_root = tmp_path / "ri"
    statuses = ["passed", "failed", "passed", "failed"]
    for i, status in enumerate(statuses):
        _write_reliability_impact(
            impact_root, name=f"r{i}", generated_at=_ts(day=i + 1), gate_status=status
        )
    history = load_history(
        reliability_impact_roots=[impact_root],
        replay_analytics_paths=[tmp_path / "ghost.json"],
        runtime_evidence_root=tmp_path / "ghost",
        incidents_root=tmp_path / "ghost-incidents",
    )
    report = build_gate_history(history)
    assert report.volatility in {GateVolatility.OSCILLATING, GateVolatility.REGRESSING}


def test_gate_history_unknown_when_no_data(tmp_path: Path) -> None:
    history = load_history(
        reliability_impact_roots=[tmp_path / "ghost"],
        replay_analytics_paths=[tmp_path / "ghost.json"],
        runtime_evidence_root=tmp_path / "ghost",
        incidents_root=tmp_path / "ghost-incidents",
    )
    report = build_gate_history(history)
    assert report.volatility == GateVolatility.UNKNOWN
    assert report.last_status == "unknown"


# ---------------------------------------------------------------------------
# Programme review aggregate.
# ---------------------------------------------------------------------------


def test_report_labels_insufficient_history(tmp_path: Path) -> None:
    impact_root = tmp_path / "ri"
    _write_reliability_impact(impact_root, name="r1", generated_at=_ts(day=1))
    history = load_history(
        reliability_impact_roots=[impact_root],
        replay_analytics_paths=[tmp_path / "ghost.json"],
        runtime_evidence_root=tmp_path / "ghost",
        incidents_root=tmp_path / "ghost-incidents",
    )
    review = build_programme_review(
        history=history,
        reference_time_utc=datetime(2026, 5, 2, tzinfo=timezone.utc),
    )
    for series in review.trend_report.series:
        if series.window_size <= 1:
            assert series.category == TrendCategory.INSUFFICIENT_HISTORY


def test_report_labels_mixed_origin(tmp_path: Path) -> None:
    incidents_root = tmp_path / "incidents"
    _write_replay_review(incidents_root, incident_id="a", evidence_origin="bag-backed", generated_at=_ts(day=1))
    _write_replay_review(incidents_root, incident_id="b", evidence_origin="scenario-evidence", generated_at=_ts(day=2))
    history = load_history(
        reliability_impact_roots=[tmp_path / "ghost"],
        replay_analytics_paths=[tmp_path / "ghost.json"],
        runtime_evidence_root=tmp_path / "ghost",
        incidents_root=incidents_root,
    )
    review = build_programme_review(
        history=history,
        reference_time_utc=datetime(2026, 5, 3, tzinfo=timezone.utc),
    )
    assert review.coverage_evolution.origin_mix_label == "mixed_origin"


def test_report_does_not_fail_on_partial_history(tmp_path: Path) -> None:
    history = load_history(
        reliability_impact_roots=[tmp_path / "ghost"],
        replay_analytics_paths=[tmp_path / "ghost.json"],
        runtime_evidence_root=tmp_path / "ghost",
        incidents_root=tmp_path / "ghost-incidents",
    )
    review = build_programme_review(
        history=history,
        reference_time_utc=datetime(2026, 5, 2, tzinfo=timezone.utc),
    )
    # No history -> no findings, but the function must return a valid
    # ProgrammeReview rather than raising.
    assert review.gate_history.volatility == GateVolatility.UNKNOWN
    assert review.drift_report.severity in {DriftSeverity.INFORMATIONAL}


def test_bundle_written_to_disk(tmp_path: Path) -> None:
    impact_root = tmp_path / "ri"
    _write_reliability_impact(impact_root, name="r1", generated_at=_ts(day=1))
    history = load_history(
        reliability_impact_roots=[impact_root],
        replay_analytics_paths=[tmp_path / "ghost.json"],
        runtime_evidence_root=tmp_path / "ghost",
        incidents_root=tmp_path / "ghost-incidents",
    )
    review = build_programme_review(
        history=history,
        reference_time_utc=datetime(2026, 5, 2, tzinfo=timezone.utc),
    )
    out_dir = tmp_path / "out"
    write_programme_review_bundle(review, out_dir=out_dir)
    expected_files = (
        "index.json",
        "programme-health.json",
        "trend-report.json",
        "drift-report.json",
        "subsystem-risk-report.json",
        "governance-dashboard.json",
        "freshness-report.json",
        "coverage-evolution.json",
        "gate-history.json",
        "programme-review.json",
        "programme-review.md",
    )
    for name in expected_files:
        assert (out_dir / name).exists(), name
    md_text = (out_dir / "programme-review.md").read_text(encoding="utf-8")
    assert PROGRAMME_CERTIFICATION_DISCLAIMER in md_text
    assert "safety-certified" in md_text


# ---------------------------------------------------------------------------
# CI workflow.
# ---------------------------------------------------------------------------


def test_programme_workflow_is_github_hosted() -> None:
    path = _REPO_ROOT / ".github" / "workflows" / "programme-review.yml"
    text = path.read_text(encoding="utf-8")
    assert "ubuntu-24.04" in text
    assert "self-hosted" not in text


def test_programme_workflow_supports_dispatch() -> None:
    path = _REPO_ROOT / ".github" / "workflows" / "programme-review.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    triggers = data.get("on") or data.get(True) or {}
    assert "workflow_dispatch" in triggers


def test_programme_workflow_uploads_artifacts() -> None:
    path = _REPO_ROOT / ".github" / "workflows" / "programme-review.yml"
    text = path.read_text(encoding="utf-8")
    assert "upload-artifact" in text
    assert "programme-review/" in text


# ---------------------------------------------------------------------------
# CLI smoke.
# ---------------------------------------------------------------------------


def _import_cli(name: str):
    import importlib

    return importlib.import_module(name)


def test_cli_generate_programme_review(tmp_path: Path) -> None:
    impact_root = tmp_path / "ri"
    _write_reliability_impact(impact_root, name="r1", generated_at=_ts(day=1))
    cli = _import_cli("generate_programme_review")
    rc = cli.main(
        [
            "--reliability-impact-root",
            str(impact_root),
            "--replay-analytics",
            str(tmp_path / "missing.json"),
            "--runtime-evidence-root",
            str(tmp_path / "ghost"),
            "--incidents-root",
            str(tmp_path / "ghost-incidents"),
            "--reference-time",
            "2026-05-02T00:00:00Z",
            "--output",
            str(tmp_path / "out"),
        ]
    )
    assert rc == 0
    assert (tmp_path / "out" / "programme-review.md").exists()


def test_cli_analyze_reliability_trends(tmp_path: Path) -> None:
    impact_root = tmp_path / "ri"
    _write_reliability_impact(impact_root, name="r1", generated_at=_ts(day=1))
    cli = _import_cli("analyze_reliability_trends")
    rc = cli.main(
        [
            "--reliability-impact-root",
            str(impact_root),
            "--replay-analytics",
            str(tmp_path / "ghost.json"),
            "--runtime-evidence-root",
            str(tmp_path / "ghost"),
            "--incidents-root",
            str(tmp_path / "ghost-incidents"),
            "--output",
            str(tmp_path / "out"),
        ]
    )
    assert rc == 0
    assert (tmp_path / "out" / "trend-report.json").exists()


def test_cli_detect_reliability_drift(tmp_path: Path) -> None:
    impact_root = tmp_path / "ri"
    _write_reliability_impact(impact_root, name="r1", generated_at=_ts(day=1))
    cli = _import_cli("detect_reliability_drift")
    rc = cli.main(
        [
            "--reliability-impact-root",
            str(impact_root),
            "--replay-analytics",
            str(tmp_path / "ghost.json"),
            "--incidents-root",
            str(tmp_path / "ghost-incidents"),
            "--output",
            str(tmp_path / "out"),
        ]
    )
    assert rc == 0
    assert (tmp_path / "out" / "drift-report.json").exists()


def test_cli_review_governance_health(tmp_path: Path) -> None:
    impact_root = tmp_path / "ri"
    _write_reliability_impact(impact_root, name="r1", generated_at=_ts(day=1))
    cli = _import_cli("review_governance_health")
    rc = cli.main(
        [
            "--reliability-impact-root",
            str(impact_root),
            "--replay-analytics",
            str(tmp_path / "ghost.json"),
            "--runtime-evidence-root",
            str(tmp_path / "ghost"),
            "--incidents-root",
            str(tmp_path / "ghost-incidents"),
            "--output",
            str(tmp_path / "out"),
        ]
    )
    assert rc == 0
    assert (tmp_path / "out" / "programme-health.json").exists()


def test_cli_review_evidence_freshness(tmp_path: Path) -> None:
    impact_root = tmp_path / "ri"
    _write_reliability_impact(impact_root, name="r1", generated_at=_ts(day=1))
    cli = _import_cli("review_evidence_freshness")
    rc = cli.main(
        [
            "--reliability-impact-root",
            str(impact_root),
            "--replay-analytics",
            str(tmp_path / "ghost.json"),
            "--runtime-evidence-root",
            str(tmp_path / "ghost"),
            "--incidents-root",
            str(tmp_path / "ghost-incidents"),
            "--reference-time",
            "2026-05-02T00:00:00Z",
            "--output",
            str(tmp_path / "out"),
        ]
    )
    assert rc == 0
    assert (tmp_path / "out" / "freshness-report.json").exists()


# ---------------------------------------------------------------------------
# Determinism + honesty rules.
# ---------------------------------------------------------------------------


def test_aggregate_review_is_deterministic(tmp_path: Path) -> None:
    impact_root = tmp_path / "ri"
    _write_reliability_impact(impact_root, name="r1", generated_at=_ts(day=1))
    _write_reliability_impact(impact_root, name="r2", generated_at=_ts(day=2))
    history = load_history(
        reliability_impact_roots=[impact_root],
        replay_analytics_paths=[tmp_path / "ghost.json"],
        runtime_evidence_root=tmp_path / "ghost",
        incidents_root=tmp_path / "ghost-incidents",
    )
    reference = datetime(2026, 5, 3, tzinfo=timezone.utc)
    a = build_programme_review(history=history, reference_time_utc=reference)
    b = build_programme_review(history=history, reference_time_utc=reference)
    a_dict = a.as_dict()
    b_dict = b.as_dict()
    assert a_dict == b_dict


def test_loader_warnings_never_fail_aggregation(tmp_path: Path) -> None:
    """Malformed inputs do not raise; the aggregator still returns a report."""

    impact_root = tmp_path / "ri"
    bad = impact_root / "bad"
    bad.mkdir(parents=True)
    (bad / "impact-report.json").write_text("not json", encoding="utf-8")
    history = load_history(
        reliability_impact_roots=[impact_root],
        replay_analytics_paths=[tmp_path / "ghost.json"],
        runtime_evidence_root=tmp_path / "ghost",
        incidents_root=tmp_path / "ghost-incidents",
    )
    review = build_programme_review(
        history=history,
        reference_time_utc=datetime(2026, 5, 2, tzinfo=timezone.utc),
    )
    # Loader warning is preserved on the review.
    assert any("did not parse" in w for w in review.warnings)


def test_evidence_origin_survives_aggregation(tmp_path: Path) -> None:
    incidents_root = tmp_path / "incidents"
    _write_replay_review(
        incidents_root,
        incident_id="x",
        generated_at=_ts(day=1),
        evidence_origin="bag-backed",
    )
    history = load_history(
        reliability_impact_roots=[tmp_path / "ghost"],
        replay_analytics_paths=[tmp_path / "ghost.json"],
        runtime_evidence_root=tmp_path / "ghost",
        incidents_root=incidents_root,
    )
    review = build_programme_review(
        history=history,
        reference_time_utc=datetime(2026, 5, 2, tzinfo=timezone.utc),
    )
    assert review.coverage_evolution.entries[0].evidence_origin == "bag-backed"


def test_subsystem_risk_payload_does_not_include_blame() -> None:
    """Sanity: the model dataclass has no causal field."""

    from app.programme_review.models import SubsystemRiskRow

    row = SubsystemRiskRow(
        subsystem="safety",
        frequency=1,
        severity_distribution={"high": 1},
        repeat_regression_count=1,
        gate_failure_count=0,
        unresolved_warning_count=1,
    )
    payload = row.as_dict()
    assert "cause" not in payload
    assert "blame" not in payload


def test_canonical_programme_review_committed() -> None:
    """The canonical bundle ships under programme-review/."""

    canonical = _REPO_ROOT / "programme-review" / "programme-review.json"
    if not canonical.exists():
        pytest.skip("canonical programme-review not generated in this checkout")
    payload = json.loads(canonical.read_text(encoding="utf-8"))
    assert "governance_health" in payload
    assert "drift_report" in payload
