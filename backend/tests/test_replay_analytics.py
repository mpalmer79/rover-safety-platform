"""Phase 8 replay analytics tests.

Tests run without ROS / Gazebo / Foxglove. They exercise:

* coverage analysis — deterministic metrics, unavailable handling,
  static-only / missing-bag inputs;
* quality scoring — band caps (90-100, 70-89, 40-69, 0-39),
  determinism, contradictions cap to 39, missing-metric penalty;
* trends — distribution counters, top-N ordering;
* comparison — evidence-origin preservation, deterministic ordering;
* review audit — explicit-acknowledgement-only, partial vs completed,
  inconclusive on bad shape;
* recommendations — gap-to-recommendation mapping;
* index — filterable;
* CLIs — analyze, compare, generate, audit;
* GitHub workflow — well-formed, runs on github-hosted by default.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

import yaml


_REPO_ROOT = Path(__file__).resolve().parents[2]
_TOOLS_DIR = _REPO_ROOT / "rover_ws" / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))


from app.replay_analytics import (  # noqa: E402
    ANALYTICS_CERTIFICATION_DISCLAIMER,
    CANONICAL_REVIEW_STEPS,
    LoadedReplayBundle,
    ReplayCoverageStatus,
    ReplayGapSeverity,
    ReplayQualityScore,
    ReviewCompletionStatus,
    analyze_coverage,
    audit_review,
    build_comparison,
    build_index,
    build_recommendations,
    build_trends,
    detect_gaps,
    load_replay_bundle,
    load_replay_bundles,
    quality_bucket,
    render_aggregate_report_md,
    render_comparison_md,
    render_gap_analysis_md,
    render_index_md,
    render_per_incident_report_md,
    render_quality_index_json,
    render_trends_md,
    score_replay_quality,
    write_review_audit_json,
)


# ---------------------------------------------------------------------------
# Helpers.
# ---------------------------------------------------------------------------


def _write_bundle(
    path: Path,
    *,
    incident_id: str = "test",
    evidence_status: str = "complete",
    bag_status: str = "missing_bag",
    available_topics: tuple[str, ...] = (),
    missing_topics: tuple[str, ...] = (),
    contradictions: tuple[str, ...] = (),
    markers: list[dict] | None = None,
    timeline_entries: list[dict] | None = None,
    validation_results: list[dict] | None = None,
    safety_states: tuple[str, ...] = ("ACTIVE_NORMAL", "SAFE_STOP"),
    outcome: str = "safe_stop_success",
    review_audit_payload: dict | None = None,
) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    if timeline_entries is None:
        timeline_entries = [
            {
                "category": "fault_injection",
                "event_type": "fault_injection.fired",
                "attributes": {"fault_type": "stale_lidar"},
                "evidence_origin": "scenario-evidence",
                "sim_time_ns": 1_000_000_000,
                "relative_time_ms": 0,
                "raw_reference": "evt-001",
                "source_file": "events.jsonl",
                "safety_state": "BOOT",
            },
            {
                "category": "safety_transition",
                "event_type": "safety_transition.entered",
                "attributes": {"to_state": "SAFE_STOP"},
                "evidence_origin": "scenario-evidence",
                "sim_time_ns": 2_000_000_000,
                "relative_time_ms": 1000,
                "raw_reference": "evt-002",
                "source_file": "events.jsonl",
                "safety_state": "SAFE_STOP",
            },
        ]
    incident_payload = {
        "incident_id": incident_id,
        "run_id": "rid-x",
        "scenario_id": "scn-x",
        "evidence_status": evidence_status,
        "outcome": outcome,
        "safety_states": list(safety_states),
        "contradictions": list(contradictions),
        "timeline": {
            "entries": timeline_entries,
            "first_fault_index": 0,
            "first_safety_transition_index": 1,
            "first_command_intervention_index": None,
            "terminal_index": 1,
        },
    }
    (path / "incident-report.json").write_text(json.dumps(incident_payload), encoding="utf-8")
    (path / "incident-report.md").write_text("# stub", encoding="utf-8")
    (path / "timeline.json").write_text(json.dumps(incident_payload["timeline"]), encoding="utf-8")
    (path / "timeline.md").write_text("# stub", encoding="utf-8")
    expected_topics = [
        {"name": "/safety/state", "purpose": "supervisor", "required": True},
        {"name": "/cmd_vel_authorized", "purpose": "auth", "required": True},
        {"name": "/scan", "purpose": "lidar", "required": False},
    ]
    manifest_payload = {
        "incident_id": incident_id,
        "run_id": "rid-x",
        "scenario_id": "scn-x",
        "evidence_status": evidence_status,
        "bag_status": bag_status,
        "expected_topics": expected_topics,
        "available_topics": list(available_topics),
        "missing_topics": list(missing_topics),
        "foxglove_layout_path": "foxglove/layouts/incident-review-layout.json",
        "foxglove_session_path": "foxglove-session.json",
        "timeline_marker_count": 2 if markers is None else len(markers),
        "review_steps": [],
        "known_limitations": [],
    }
    (path / "replay-review-manifest.json").write_text(
        json.dumps(manifest_payload), encoding="utf-8"
    )
    (path / "replay-review.md").write_text("# stub", encoding="utf-8")
    if validation_results is None:
        validation_results = [
            {"name": "incident_report_present", "status": "passed", "detail": "ok"},
            {"name": "timeline_present", "status": "passed", "detail": "ok"},
        ]
    report_payload = {
        "incident_id": incident_id,
        "bag_status": bag_status,
        "replay_execution_status": (
            "missing_bag"
            if bag_status == "missing_bag"
            else (
                "static_only" if bag_status == "static_only"
                else ("ready" if bag_status == "ready" else "partial")
            )
        ),
        "evidence_origin": (
            "bag-backed" if bag_status == "ready"
            else (
                "scenario-evidence" if bag_status in {"missing_bag", "static_only", "partial"}
                else "unknown"
            )
        ),
        "validation_results": validation_results,
    }
    (path / "replay-review-report.json").write_text(json.dumps(report_payload), encoding="utf-8")
    (path / "replay-review-report.md").write_text("# stub", encoding="utf-8")
    if markers is None:
        markers = [
            {
                "marker_id": "first_fault",
                "label": "First fault",
                "description": "",
                "timeline_index": 0,
                "relative_time_ms": 0,
                "sim_time_ns": 1_000_000_000,
                "source_event_id": "evt-001",
                "source_file": "events.jsonl",
                "confidence": "direct",
                "evidence_origin": "scenario-evidence",
                "alignment": "exact",
            },
            {
                "marker_id": "first_safety_transition",
                "label": "First safety",
                "description": "",
                "timeline_index": 1,
                "relative_time_ms": 1000,
                "sim_time_ns": 2_000_000_000,
                "source_event_id": "evt-002",
                "source_file": "events.jsonl",
                "confidence": "direct",
                "evidence_origin": "scenario-evidence",
                "alignment": "exact",
            },
        ]
    (path / "replay-markers.json").write_text(json.dumps(markers), encoding="utf-8")
    (path / "foxglove-session.json").write_text(json.dumps({"incident_id": incident_id}), encoding="utf-8")
    if review_audit_payload is not None:
        (path / "review-audit.json").write_text(
            json.dumps(review_audit_payload), encoding="utf-8"
        )
    return path


# ---------------------------------------------------------------------------
# Coverage analysis.
# ---------------------------------------------------------------------------


def test_coverage_metrics_are_deterministic(tmp_path: Path) -> None:
    bundle_dir = _write_bundle(tmp_path / "incidents" / "x")
    bundle = load_replay_bundle(bundle_dir)
    a = analyze_coverage(bundle)
    b = analyze_coverage(bundle)
    # Strip the timestamp before comparing - that's the only allowed
    # source of non-determinism.
    a_dict = a.as_dict()
    b_dict = b.as_dict()
    a_dict.pop("generated_at_utc", None)
    b_dict.pop("generated_at_utc", None)
    assert a_dict == b_dict


def test_coverage_unavailable_when_no_inventory(tmp_path: Path) -> None:
    bundle_dir = _write_bundle(
        tmp_path / "incidents" / "x",
        bag_status="missing_bag",
        available_topics=(),
    )
    bundle = load_replay_bundle(bundle_dir)
    cov = analyze_coverage(bundle)
    metric = cov.metric("expected_topics_present_pct")
    assert metric is not None
    assert metric.available is False
    assert metric.value is None


def test_coverage_marks_metrics_unavailable_honestly(tmp_path: Path) -> None:
    """A bundle with an empty manifest has multiple unavailable metrics."""

    bundle_dir = _write_bundle(tmp_path / "incidents" / "x")
    # Replace the report's validation_results with an empty list to
    # force replay_validation_pass_rate=unavailable.
    report_path = bundle_dir / "replay-review-report.json"
    payload = json.loads(report_path.read_text())
    payload["validation_results"] = []
    report_path.write_text(json.dumps(payload), encoding="utf-8")
    bundle = load_replay_bundle(bundle_dir)
    cov = analyze_coverage(bundle)
    metric = cov.metric("replay_validation_pass_rate")
    assert metric is not None
    assert metric.available is False


def test_coverage_static_only_aggregates_to_sparse(tmp_path: Path) -> None:
    bundle_dir = _write_bundle(
        tmp_path / "incidents" / "x",
        bag_status="static_only",
        evidence_status="static_only",
    )
    bundle = load_replay_bundle(bundle_dir)
    cov = analyze_coverage(bundle)
    assert cov.coverage_status == ReplayCoverageStatus.SPARSE


# ---------------------------------------------------------------------------
# Quality scoring.
# ---------------------------------------------------------------------------


def test_scoring_static_only_below_40(tmp_path: Path) -> None:
    bundle_dir = _write_bundle(
        tmp_path / "incidents" / "x",
        bag_status="static_only",
        evidence_status="static_only",
    )
    bundle = load_replay_bundle(bundle_dir)
    score = score_replay_quality(
        bundle=bundle, coverage=analyze_coverage(bundle)
    )
    assert score.score < 40, score.score
    assert score.confidence == "low"


def test_scoring_missing_bag_below_60(tmp_path: Path) -> None:
    bundle_dir = _write_bundle(
        tmp_path / "incidents" / "x",
        bag_status="missing_bag",
        evidence_status="complete",
    )
    bundle = load_replay_bundle(bundle_dir)
    score = score_replay_quality(
        bundle=bundle, coverage=analyze_coverage(bundle)
    )
    assert score.score < 60, score.score
    assert score.confidence == "low"


def test_scoring_complete_replay_at_or_above_90(tmp_path: Path) -> None:
    bundle_dir = _write_bundle(
        tmp_path / "incidents" / "x",
        bag_status="ready",
        evidence_status="complete",
        available_topics=("/safety/state", "/cmd_vel_authorized", "/scan"),
        missing_topics=(),
    )
    bundle = load_replay_bundle(bundle_dir)
    score = score_replay_quality(
        bundle=bundle, coverage=analyze_coverage(bundle)
    )
    assert score.score >= 90, score.score
    assert score.confidence in {"high", "moderate"}


def test_scoring_contradictions_cap_to_39(tmp_path: Path) -> None:
    bundle_dir = _write_bundle(
        tmp_path / "incidents" / "x",
        bag_status="ready",
        evidence_status="complete",
        available_topics=("/safety/state", "/cmd_vel_authorized"),
        contradictions=("clean run reports zero zeroed authorisations",),
    )
    bundle = load_replay_bundle(bundle_dir)
    score = score_replay_quality(
        bundle=bundle, coverage=analyze_coverage(bundle)
    )
    assert score.score <= 39, score.score
    assert any("contradictions" in g for g in score.blocking_gaps)


def test_scoring_is_deterministic(tmp_path: Path) -> None:
    bundle_dir = _write_bundle(
        tmp_path / "incidents" / "x",
        bag_status="ready",
        evidence_status="complete",
        available_topics=("/safety/state", "/cmd_vel_authorized"),
    )
    bundle = load_replay_bundle(bundle_dir)
    a = score_replay_quality(bundle=bundle, coverage=analyze_coverage(bundle))
    b = score_replay_quality(bundle=bundle, coverage=analyze_coverage(bundle))
    assert a.score == b.score
    assert a.coverage_status == b.coverage_status


def test_scoring_no_replay_review_returns_zero(tmp_path: Path) -> None:
    incident_dir = tmp_path / "ghost"
    incident_dir.mkdir()
    bundle = load_replay_bundle(incident_dir)
    score = score_replay_quality(
        bundle=bundle, coverage=analyze_coverage(bundle)
    )
    assert score.score == 0
    assert score.coverage_status == ReplayCoverageStatus.MISSING


def test_quality_buckets() -> None:
    assert quality_bucket(95) == "90-100"
    assert quality_bucket(80) == "70-89"
    assert quality_bucket(50) == "40-69"
    assert quality_bucket(20) == "0-39"
    assert quality_bucket(0) == "0-39"


# ---------------------------------------------------------------------------
# Trends + comparison.
# ---------------------------------------------------------------------------


def test_trends_aggregate_distributions(tmp_path: Path) -> None:
    a = _write_bundle(
        tmp_path / "incidents" / "a",
        incident_id="a",
        bag_status="missing_bag",
        evidence_status="complete",
    )
    b = _write_bundle(
        tmp_path / "incidents" / "b",
        incident_id="b",
        bag_status="static_only",
        evidence_status="static_only",
    )
    bundles = [load_replay_bundle(a), load_replay_bundle(b)]
    coverages = {x.incident_id: analyze_coverage(x) for x in bundles}
    scores = {
        x.incident_id: score_replay_quality(
            bundle=x, coverage=coverages[x.incident_id]
        )
        for x in bundles
    }
    trend = build_trends(
        bundles=bundles,
        coverages=coverages.values(),
        scores=scores.values(),
        gaps_by_incident={},
    )
    assert trend.bag_status_distribution == {"missing_bag": 1, "static_only": 1}
    assert trend.review_completion_distribution["not_started"] == 2
    assert trend.incident_count == 2


def test_comparison_preserves_evidence_origin(tmp_path: Path) -> None:
    a = _write_bundle(
        tmp_path / "incidents" / "a",
        incident_id="a",
        bag_status="ready",
        evidence_status="complete",
        available_topics=("/safety/state", "/cmd_vel_authorized"),
    )
    b = _write_bundle(
        tmp_path / "incidents" / "b",
        incident_id="b",
        bag_status="static_only",
        evidence_status="static_only",
    )
    bundles = [load_replay_bundle(a), load_replay_bundle(b)]
    coverages = {x.incident_id: analyze_coverage(x) for x in bundles}
    scores = {
        x.incident_id: score_replay_quality(
            bundle=x, coverage=coverages[x.incident_id]
        )
        for x in bundles
    }
    comparison = build_comparison(
        comparison_id="cmp",
        bundles=bundles,
        coverages=coverages,
        scores=scores,
    )
    origins = {row["evidence_origin"] for row in comparison.rows}
    assert origins == {"bag-backed", "scenario-evidence"}
    # Notes flag the origin mismatch.
    assert any("evidence_origin" in note for note in comparison.notes)


def test_comparison_orders_by_quality_score(tmp_path: Path) -> None:
    a = _write_bundle(
        tmp_path / "incidents" / "a",
        incident_id="a",
        bag_status="missing_bag",
        evidence_status="static_only",
    )
    b = _write_bundle(
        tmp_path / "incidents" / "b",
        incident_id="b",
        bag_status="ready",
        evidence_status="complete",
        available_topics=("/safety/state", "/cmd_vel_authorized"),
    )
    bundles = [load_replay_bundle(a), load_replay_bundle(b)]
    coverages = {x.incident_id: analyze_coverage(x) for x in bundles}
    scores = {
        x.incident_id: score_replay_quality(
            bundle=x, coverage=coverages[x.incident_id]
        )
        for x in bundles
    }
    comparison = build_comparison(
        comparison_id="cmp",
        bundles=bundles,
        coverages=coverages,
        scores=scores,
    )
    assert comparison.rows[0]["incident_id"] == "b"
    assert comparison.rows[1]["incident_id"] == "a"


# ---------------------------------------------------------------------------
# Review audit.
# ---------------------------------------------------------------------------


def test_review_audit_absent_metadata_is_not_started(tmp_path: Path) -> None:
    bundle_dir = _write_bundle(tmp_path / "incidents" / "x")
    bundle = load_replay_bundle(bundle_dir)
    audit = audit_review(bundle)
    assert audit.status == ReviewCompletionStatus.NOT_STARTED


def test_review_audit_completed_requires_explicit_flag(tmp_path: Path) -> None:
    bundle_dir = _write_bundle(
        tmp_path / "incidents" / "x",
        review_audit_payload={
            "incident_id": "x",
            "operator": "tester",
            "completed_steps": list(CANONICAL_REVIEW_STEPS),
        },
    )
    bundle = load_replay_bundle(bundle_dir)
    audit = audit_review(bundle)
    assert audit.status == ReviewCompletionStatus.COMPLETED
    assert audit.operator == "tester"


def test_review_audit_partial_when_some_steps_done(tmp_path: Path) -> None:
    bundle_dir = _write_bundle(
        tmp_path / "incidents" / "x",
        review_audit_payload={
            "incident_id": "x",
            "completed_steps": [
                "bag_status_reviewed",
                "missing_topics_reviewed",
            ],
        },
    )
    bundle = load_replay_bundle(bundle_dir)
    audit = audit_review(bundle)
    assert audit.status == ReviewCompletionStatus.PARTIAL


def test_review_audit_status_override_respected(tmp_path: Path) -> None:
    bundle_dir = _write_bundle(
        tmp_path / "incidents" / "x",
        review_audit_payload={
            "incident_id": "x",
            "completed_steps": [],
            "status_override": "completed",
        },
    )
    bundle = load_replay_bundle(bundle_dir)
    audit = audit_review(bundle)
    # Even if completed_steps is empty, the explicit override wins.
    assert audit.status == ReviewCompletionStatus.COMPLETED


def test_review_audit_inconclusive_on_bad_shape(tmp_path: Path) -> None:
    bundle_dir = _write_bundle(tmp_path / "incidents" / "x")
    (bundle_dir / "review-audit.json").write_text("[\"not\", \"a\", \"dict\"]", encoding="utf-8")
    bundle = load_replay_bundle(bundle_dir)
    audit = audit_review(bundle)
    assert audit.status == ReviewCompletionStatus.INCONCLUSIVE


# ---------------------------------------------------------------------------
# Recommendations.
# ---------------------------------------------------------------------------


def test_recommendation_for_missing_bag(tmp_path: Path) -> None:
    bundle_dir = _write_bundle(
        tmp_path / "incidents" / "x",
        bag_status="missing_bag",
    )
    bundle = load_replay_bundle(bundle_dir)
    cov = analyze_coverage(bundle)
    gaps = detect_gaps(bundle=bundle, coverage=cov)
    assert any(g.label == "missing_bag" for g in gaps)
    recs = build_recommendations(bundle=bundle, gaps=gaps)
    assert any(r.label == "capture_rosbag2" for r in recs)


def test_recommendation_for_missing_topics(tmp_path: Path) -> None:
    bundle_dir = _write_bundle(
        tmp_path / "incidents" / "x",
        bag_status="ready",
        evidence_status="complete",
        available_topics=("/safety/state",),
        missing_topics=("/cmd_vel_authorized",),
    )
    bundle = load_replay_bundle(bundle_dir)
    cov = analyze_coverage(bundle)
    gaps = detect_gaps(bundle=bundle, coverage=cov)
    assert any(g.label == "missing_topic[/cmd_vel_authorized]" for g in gaps)
    recs = build_recommendations(bundle=bundle, gaps=gaps)
    assert any(r.label == "add_topic[/cmd_vel_authorized]" for r in recs)


def test_recommendation_for_static_only(tmp_path: Path) -> None:
    bundle_dir = _write_bundle(
        tmp_path / "incidents" / "x",
        bag_status="static_only",
        evidence_status="static_only",
    )
    bundle = load_replay_bundle(bundle_dir)
    cov = analyze_coverage(bundle)
    gaps = detect_gaps(bundle=bundle, coverage=cov)
    recs = build_recommendations(bundle=bundle, gaps=gaps)
    assert any(r.label == "rerun_on_jazzy_host" for r in recs)


# ---------------------------------------------------------------------------
# Reporter + Index.
# ---------------------------------------------------------------------------


def test_per_incident_report_includes_disclaimer(tmp_path: Path) -> None:
    bundle_dir = _write_bundle(tmp_path / "incidents" / "x")
    bundle = load_replay_bundle(bundle_dir)
    cov = analyze_coverage(bundle)
    score = score_replay_quality(bundle=bundle, coverage=cov)
    audit = audit_review(bundle)
    gaps = detect_gaps(bundle=bundle, coverage=cov)
    recs = build_recommendations(bundle=bundle, gaps=gaps)
    md = render_per_incident_report_md(
        bundle=bundle,
        coverage=cov,
        score=score,
        audit=audit,
        gaps=gaps,
        recommendations=recs,
    )
    assert ANALYTICS_CERTIFICATION_DISCLAIMER in md
    assert "Coverage metrics" in md
    assert "Recommendations" in md


def test_report_distribution_by_bag_status(tmp_path: Path) -> None:
    a = _write_bundle(
        tmp_path / "incidents" / "a",
        incident_id="a",
        bag_status="missing_bag",
    )
    b = _write_bundle(
        tmp_path / "incidents" / "b",
        incident_id="b",
        bag_status="static_only",
        evidence_status="static_only",
    )
    bundles = [load_replay_bundle(a), load_replay_bundle(b)]
    coverages = {x.incident_id: analyze_coverage(x) for x in bundles}
    scores = {
        x.incident_id: score_replay_quality(
            bundle=x, coverage=coverages[x.incident_id]
        )
        for x in bundles
    }
    audits = {x.incident_id: audit_review(x) for x in bundles}
    trend = build_trends(
        bundles=bundles,
        coverages=coverages.values(),
        scores=scores.values(),
        gaps_by_incident={},
    )
    md = render_aggregate_report_md(
        bundles=bundles,
        coverages=coverages,
        scores=scores,
        audits=audits,
        trend=trend,
        recommendations_by_incident={},
    )
    assert "missing_bag" in md
    assert "static_only" in md
    assert "Bag status" in md


def test_index_filters_by_bag_status(tmp_path: Path) -> None:
    a = _write_bundle(
        tmp_path / "incidents" / "a",
        incident_id="a",
        bag_status="missing_bag",
    )
    b = _write_bundle(
        tmp_path / "incidents" / "b",
        incident_id="b",
        bag_status="static_only",
        evidence_status="static_only",
    )
    bundles = [load_replay_bundle(a), load_replay_bundle(b)]
    coverages = {x.incident_id: analyze_coverage(x) for x in bundles}
    scores = {
        x.incident_id: score_replay_quality(
            bundle=x, coverage=coverages[x.incident_id]
        )
        for x in bundles
    }
    audits = {x.incident_id: audit_review(x) for x in bundles}
    index = build_index(
        bundles=bundles,
        coverages=coverages,
        scores=scores,
        audits=audits,
    )
    static_only_rows = index.filter(bag_status="static_only")
    assert {r.incident_id for r in static_only_rows} == {"b"}


def test_index_filters_by_quality_score(tmp_path: Path) -> None:
    a = _write_bundle(
        tmp_path / "incidents" / "a",
        incident_id="a",
        bag_status="ready",
        evidence_status="complete",
        available_topics=("/safety/state", "/cmd_vel_authorized"),
    )
    b = _write_bundle(
        tmp_path / "incidents" / "b",
        incident_id="b",
        bag_status="static_only",
        evidence_status="static_only",
    )
    bundles = [load_replay_bundle(a), load_replay_bundle(b)]
    coverages = {x.incident_id: analyze_coverage(x) for x in bundles}
    scores = {
        x.incident_id: score_replay_quality(
            bundle=x, coverage=coverages[x.incident_id]
        )
        for x in bundles
    }
    audits = {x.incident_id: audit_review(x) for x in bundles}
    index = build_index(
        bundles=bundles,
        coverages=coverages,
        scores=scores,
        audits=audits,
    )
    high = index.filter(min_score=80)
    assert {r.incident_id for r in high} == {"a"}
    low = index.filter(max_score=39)
    assert {r.incident_id for r in low} == {"b"}


# ---------------------------------------------------------------------------
# CLIs.
# ---------------------------------------------------------------------------


def _import_cli(name: str):
    import importlib

    return importlib.import_module(name)


def test_cli_analyze_replay_coverage(tmp_path: Path) -> None:
    bundle_dir = _write_bundle(tmp_path / "incidents" / "x")
    cli = _import_cli("analyze_replay_coverage")
    rc = cli.main(["--incident", str(bundle_dir)])
    assert rc == 0
    assert (bundle_dir / "replay-analytics.json").exists()
    assert (bundle_dir / "replay-coverage.json").exists()
    assert (bundle_dir / "replay-quality-score.json").exists()
    assert (bundle_dir / "review-audit.json").exists()


def test_cli_compare_replay_reviews(tmp_path: Path) -> None:
    a = _write_bundle(
        tmp_path / "incidents" / "a",
        incident_id="a",
        bag_status="missing_bag",
    )
    b = _write_bundle(
        tmp_path / "incidents" / "b",
        incident_id="b",
        bag_status="static_only",
        evidence_status="static_only",
    )
    cli = _import_cli("compare_replay_reviews")
    rc = cli.main(
        [
            str(a),
            str(b),
            "--comparison-id",
            "cli-cmp",
            "--out-dir",
            str(tmp_path / "cmp"),
        ]
    )
    assert rc == 0
    assert (tmp_path / "cmp" / "cli-cmp.json").exists()
    assert (tmp_path / "cmp" / "cli-cmp.md").exists()


def test_cli_generate_replay_analytics(tmp_path: Path) -> None:
    _write_bundle(
        tmp_path / "incidents" / "a",
        incident_id="a",
        bag_status="missing_bag",
    )
    _write_bundle(
        tmp_path / "incidents" / "b",
        incident_id="b",
        bag_status="static_only",
        evidence_status="static_only",
    )
    cli = _import_cli("generate_replay_analytics")
    rc = cli.main(
        [
            "--incidents-root",
            str(tmp_path / "incidents"),
            "--analytics-root",
            str(tmp_path / "analytics"),
            "--md-index-out",
            str(tmp_path / "REPLAY_ANALYTICS_INDEX.md"),
        ]
    )
    assert rc == 0
    for name in (
        "replay-analytics-report.md",
        "replay-analytics-report.json",
        "replay-quality-index.json",
        "replay-gap-analysis.md",
        "trends/replay-trends.md",
        "trends/replay-trends.json",
        "index.json",
    ):
        assert (tmp_path / "analytics" / name).exists(), name
    assert (tmp_path / "REPLAY_ANALYTICS_INDEX.md").exists()


def test_cli_audit_replay_reviews(tmp_path: Path) -> None:
    bundle_dir = _write_bundle(tmp_path / "incidents" / "x")
    cli = _import_cli("audit_replay_reviews")
    rc = cli.main(["--incident", str(bundle_dir)])
    assert rc == 0
    assert (bundle_dir / "review-audit.json").exists()
    assert (bundle_dir / "review-audit.md").exists()


# ---------------------------------------------------------------------------
# GitHub workflow shape.
# ---------------------------------------------------------------------------


def test_analytics_workflow_well_formed() -> None:
    path = _REPO_ROOT / ".github" / "workflows" / "replay-analytics-review.yml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert "jobs" in data
    triggers = data.get("on") or data.get(True) or {}
    assert "workflow_dispatch" in triggers


# ---------------------------------------------------------------------------
# Loader.
# ---------------------------------------------------------------------------


def test_loader_handles_missing_dir(tmp_path: Path) -> None:
    bundle = load_replay_bundle(tmp_path / "ghost")
    assert bundle.warnings
    assert not bundle.has_replay_review


def test_loader_skips_analytics_subdir(tmp_path: Path) -> None:
    incidents = tmp_path / "incidents"
    _write_bundle(incidents / "real", incident_id="real")
    (incidents / "analytics").mkdir()
    (incidents / "comparisons").mkdir()
    bundles = load_replay_bundles(incidents)
    assert {b.incident_id for b in bundles} == {"real"}
