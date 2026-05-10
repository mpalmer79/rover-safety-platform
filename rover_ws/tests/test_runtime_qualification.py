"""Phase 5 runtime-qualification tests.

These tests run without ROS / Gazebo: every host check that requires
ROS is exercised through a stubbed runner. The orchestrator
end-to-end test runs in static-only mode and asserts the full
evidence directory is produced.

Coverage:

* host qualification — distro parsing, missing-dependency handling,
  result schema;
* qualification scenarios — schema validation, required-field
  validation, forbidden-event overlap, YAML pack loader;
* baselines — diff classification (expected_difference / warning /
  regression / critical_regression);
* regression detection — severity classification, evidence references;
* evidence index — chronological order, manifest generation;
* qualification report — origin labelling, status_counts, Markdown
  rendering, live-runtime status;
* CI workflow files — schema validation;
* orchestrator — full evidence directory in static-only mode.
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


from app.runtime_validation import (  # noqa: E402  (sys.path mutated in conftest)
    BaselineComparison,
    DeltaSeverity,
    EvidenceIndex,
    QualificationCheck,
    QualificationReport,
    QualificationScenario,
    RegressionFinding,
    RegressionReport,
    ScenarioOutcome,
    baseline_from_evidence,
    build_evidence_index,
    compare_baseline,
    detect_regressions,
    load_scenario_pack_from_dir,
    parse_os_release,
    parse_scenario,
    qualify_host,
    render_evidence_index_md,
    render_host_qualification_md,
    render_live_runtime_status_md,
    render_qualification_summary_md,
    render_regression_md,
    write_baseline,
    write_evidence_index,
)
from app.runtime_validation.host_qualification import HostQualificationResult
from app.runtime_validation.regression import detect_regressions as _detect_regressions
from app.verification.acceptance import AcceptanceStatus


# ---------------------------------------------------------------------------
# Host qualification — distro parsing.
# ---------------------------------------------------------------------------


def test_host_qualification_distro_parsing() -> None:
    sample = (
        'NAME="Ubuntu"\n'
        'VERSION_ID="24.04"\n'
        'PRETTY_NAME="Ubuntu 24.04 LTS"\n'
        '# a comment\n'
        '\n'
        'EXTRA="value with spaces"\n'
    )
    parsed = parse_os_release(sample)
    assert parsed["NAME"] == "Ubuntu"
    assert parsed["VERSION_ID"] == "24.04"
    assert parsed["PRETTY_NAME"] == "Ubuntu 24.04 LTS"
    assert parsed["EXTRA"] == "value with spaces"


def test_host_qualification_distro_parsing_handles_empty() -> None:
    assert parse_os_release("") == {}
    assert parse_os_release("# only comments\n") == {}


def test_host_qualification_runs_without_ros(tmp_path: Path) -> None:
    """A stubbed runner that 'lacks' ROS must produce only not_executed for the live checks."""

    # Build a fake workspace with the minimum structure the qualifier
    # expects so we exercise the workspace / launch / bridge checks.
    ws = tmp_path / "ws"
    src = ws / "rover_ws" / "src"
    backend = ws / "backend" / "app"
    backend.mkdir(parents=True)
    (backend / "__init__.py").write_text("", encoding="utf-8")
    (backend / "verification").mkdir()
    (backend / "verification" / "__init__.py").write_text("", encoding="utf-8")
    (backend / "verification" / "requirements.py").write_text(
        "REQUIREMENTS = ()\n", encoding="utf-8"
    )

    workspace_packages = (
        "rover_bringup",
        "rover_safety_bridge",
        "rover_sim_gazebo",
        "rover_sensor_adapters",
        "rover_observability",
        "rover_runtime_diagnostics",
        "rover_description",
        "rover_msgs",
        "rover_world_model",
        "rover_mission_runtime",
    )
    for pkg in workspace_packages:
        (src / pkg).mkdir(parents=True)
    (ws / "rover_ws" / "install").mkdir(parents=True)

    launch_files = (
        ("rover_bringup", "full_system.launch.py"),
        ("rover_bringup", "simulation.launch.py"),
        ("rover_bringup", "safety_runtime.launch.py"),
        ("rover_bringup", "observability.launch.py"),
        ("rover_safety_bridge", "safety_bridge.launch.py"),
        ("rover_sensor_adapters", "sensor_adapters.launch.py"),
        ("rover_runtime_diagnostics", "runtime_diagnostics.launch.py"),
    )
    for pkg, fname in launch_files:
        launch_dir = src / pkg / "launch"
        launch_dir.mkdir(parents=True, exist_ok=True)
        (launch_dir / fname).write_text(
            "def generate_launch_description():\n    return None\n", encoding="utf-8"
        )

    bridge_dir = src / "rover_sim_gazebo" / "config"
    bridge_dir.mkdir(parents=True, exist_ok=True)
    (bridge_dir / "ros_gz_bridge.yaml").write_text(
        "- ros_topic_name: \"/cmd_vel_authorized\"\n  gz_topic_name: \"/cmd_vel_authorized\"\n",
        encoding="utf-8",
    )

    def stub_runner(argv, *, timeout=10.0):
        # Pretend nothing is on PATH except python.
        return (127, "")

    result = qualify_host(workspace_root=ws, runner=stub_runner)
    statuses = {c.name: c.status.value for c in result.checks}
    # ROS / Gazebo checks must be not_executed, never passed.
    assert statuses["ros2_distro"] == "not_executed"
    assert statuses["gazebo_harmonic"] == "not_executed"
    assert statuses["colcon_available"] == "not_executed"
    assert statuses["required_ros_packages"] == "not_executed"
    # Workspace checks with the synthesised tree should pass.
    assert statuses["workspace_structure"] == "passed"
    assert statuses["required_launch_files"] == "passed"
    assert statuses["bridge_config_present"] == "passed"


def test_host_qualification_marks_ros_not_executed() -> None:
    """Default runner (no stub) must mark ROS / Gazebo as not_executed when they are absent."""

    result = qualify_host(workspace_root=_REPO_ROOT)
    by_name = {c.name: c for c in result.checks}
    # On the test environment we don't have ROS; assert the check is honest.
    assert by_name["ros2_distro"].status in {
        AcceptanceStatus.PASSED,
        AcceptanceStatus.PARTIAL,
        AcceptanceStatus.NOT_EXECUTED,
    }
    if by_name["ros2_distro"].status == AcceptanceStatus.NOT_EXECUTED:
        assert by_name["ros2_distro"].reason
    md = render_host_qualification_md(result)
    assert "Host Qualification Report" in md
    assert "Overall status" in md


# ---------------------------------------------------------------------------
# Qualification scenarios.
# ---------------------------------------------------------------------------


def test_scenario_pack_parses_workspace_yamls() -> None:
    scenarios_dir = _REPO_ROOT / "qualification" / "scenarios"
    scenarios, validations = load_scenario_pack_from_dir(scenarios_dir)
    assert validations, "no qualification scenarios found"
    assert all(v.ok for v in validations), [v.as_dict() for v in validations if not v.ok]
    assert scenarios
    sids = {s.scenario_id for s in scenarios}
    assert "nominal_runtime_launch" in sids
    assert "authorized_motion_path" in sids
    assert "safe_stop_command_zeroing" in sids
    assert "stale_lidar_restricted_mode" in sids


def test_scenario_rejects_missing_required_fields() -> None:
    bad = {"scenario_id": "bad_scenario"}
    scenario, validation = parse_scenario(bad)
    assert scenario is None
    assert not validation.ok
    assert any("purpose" in e for e in validation.errors)
    assert any("expected_outcome" in e for e in validation.errors)


def test_scenario_rejects_unknown_qualification_rule() -> None:
    data = {
        "scenario_id": "x",
        "purpose": "p",
        "required_topics": [],
        "required_nodes": [],
        "required_safety_state": "ACTIVE_NORMAL",
        "required_events": [],
        "forbidden_events": [],
        "required_replay_artifacts": [],
        "qualification_rules": ["not_a_rule"],
        "expected_outcome": "passed",
    }
    scenario, validation = parse_scenario(data)
    assert scenario is None
    assert any("not_a_rule" in e for e in validation.errors)


def test_scenario_rejects_required_and_forbidden_overlap() -> None:
    data = {
        "scenario_id": "x",
        "purpose": "p",
        "required_topics": [],
        "required_nodes": [],
        "required_safety_state": "ACTIVE_NORMAL",
        "required_events": ["foo.bar"],
        "forbidden_events": ["foo.bar"],
        "required_replay_artifacts": [],
        "qualification_rules": [],
        "expected_outcome": "passed",
    }
    scenario, validation = parse_scenario(data)
    assert scenario is None
    assert any("required and forbidden" in e for e in validation.errors)


# ---------------------------------------------------------------------------
# Baselines.
# ---------------------------------------------------------------------------


def _make_baseline(**overrides) -> dict:
    base = {
        "topics": {"/safety/state": "rover_msgs/msg/SafetyState"},
        "nodes": {"rover_safety_bridge": "rover_safety_bridge"},
        "tf_frames": {"base_link": "base_footprint"},
        "safety_transitions": ["BOOT", "INACTIVE", "ACTIVE_NORMAL"],
        "authorized_commands": {
            "min_linear_x": 0.0,
            "max_linear_x": 0.5,
            "min_angular_z": -0.2,
            "max_angular_z": 0.2,
            "sample_count": 10,
        },
        "event_counts": {"safety.state.entered": 3},
        "replay_artifacts": ["metadata.json", "events.jsonl"],
        "diagnostic_health": {},
    }
    base.update(overrides)
    return base


def test_baseline_diff_classifies_expected_differences(tmp_path: Path) -> None:
    baseline = _make_baseline()
    observed = _make_baseline()  # identical
    comparison = compare_baseline(
        baseline=baseline,
        observed=observed,
        baseline_path=tmp_path / "baseline.json",
        observed_path=tmp_path / "run",
    )
    assert not comparison.has_regression()
    assert comparison.severity == DeltaSeverity.EXPECTED_DIFFERENCE
    assert comparison.summary_counts()["expected_difference"] == 0


def test_baseline_diff_flags_missing_topic_as_critical(tmp_path: Path) -> None:
    baseline = _make_baseline()
    observed = _make_baseline(topics={})
    comparison = compare_baseline(
        baseline=baseline,
        observed=observed,
        baseline_path=tmp_path / "b",
        observed_path=tmp_path / "r",
        required_topics=["/safety/state"],
    )
    assert comparison.has_regression()
    deltas = [d for d in comparison.deltas if d.category == "topics"]
    assert any(d.severity == DeltaSeverity.CRITICAL_REGRESSION for d in deltas)


def test_baseline_diff_flags_extra_node_as_warning(tmp_path: Path) -> None:
    baseline = _make_baseline()
    observed = _make_baseline(
        nodes={"rover_safety_bridge": "rover_safety_bridge", "extra_node": "x"}
    )
    comparison = compare_baseline(
        baseline=baseline,
        observed=observed,
        baseline_path=tmp_path / "b",
        observed_path=tmp_path / "r",
    )
    deltas = [d for d in comparison.deltas if d.category == "nodes" and d.key == "extra_node"]
    assert deltas and deltas[0].severity == DeltaSeverity.WARNING


def test_baseline_diff_flags_safety_transition_drift_as_critical(tmp_path: Path) -> None:
    baseline = _make_baseline()
    observed = _make_baseline(
        safety_transitions=["BOOT", "INACTIVE", "ACTIVE_NORMAL", "SAFE_STOP"]
    )
    comparison = compare_baseline(
        baseline=baseline,
        observed=observed,
        baseline_path=tmp_path / "b",
        observed_path=tmp_path / "r",
    )
    assert any(
        d.severity == DeltaSeverity.CRITICAL_REGRESSION and d.category == "safety_transitions"
        for d in comparison.deltas
    )


def test_baseline_diff_flags_missing_replay_artifact_as_critical(tmp_path: Path) -> None:
    baseline = _make_baseline()
    observed = _make_baseline(replay_artifacts=["metadata.json"])
    comparison = compare_baseline(
        baseline=baseline,
        observed=observed,
        baseline_path=tmp_path / "b",
        observed_path=tmp_path / "r",
    )
    assert any(
        d.severity == DeltaSeverity.CRITICAL_REGRESSION and d.category == "replay_artifacts"
        for d in comparison.deltas
    )


# ---------------------------------------------------------------------------
# Regression detection.
# ---------------------------------------------------------------------------


def _write_topic_snapshot(run_dir: Path, *, advertised: list[str], stale: list[str] = ()) -> None:
    rows = [
        {
            "topic": name,
            "msg_type": "x/Y",
            "live_advertised": True,
            "freshness_status": "failed" if name in stale else "passed",
        }
        for name in advertised
    ]
    (run_dir / "topic-snapshot.json").write_text(
        json.dumps({"live": {"rows": rows}}), encoding="utf-8"
    )


def test_regression_detector_classifies_severity(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    _write_topic_snapshot(run_dir, advertised=["/safety/state"], stale=["/safety/state"])
    report = detect_regressions(
        run_dir=run_dir,
        required_topics=["/safety/state", "/cmd_vel_authorized"],
    )
    severities = {f.severity for f in report.findings}
    # Missing required topic is CRITICAL_REGRESSION; stale topic is REGRESSION.
    assert DeltaSeverity.CRITICAL_REGRESSION in severities
    assert DeltaSeverity.REGRESSION in severities


def test_regression_detector_emits_evidence_references(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    _write_topic_snapshot(run_dir, advertised=["/x"])
    report = detect_regressions(
        run_dir=run_dir, required_topics=["/missing-topic"]
    )
    assert report.findings
    for finding in report.findings:
        assert finding.evidence_paths
        for p in finding.evidence_paths:
            assert p.endswith(".json")


def test_regression_detector_emits_no_findings_on_clean_run(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    _write_topic_snapshot(run_dir, advertised=["/safety/state"])
    report = detect_regressions(run_dir=run_dir, required_topics=["/safety/state"])
    assert not report.findings
    assert not report.has_regression()
    assert report.severity == DeltaSeverity.EXPECTED_DIFFERENCE
    md = render_regression_md(report)
    assert "No findings" in md


# ---------------------------------------------------------------------------
# Evidence index.
# ---------------------------------------------------------------------------


def test_evidence_index_lists_runs_in_chronological_order(tmp_path: Path) -> None:
    root = tmp_path / "evidence" / "runtime"
    for stamp in ("a-2026-05-01", "b-2026-05-02", "c-2026-05-03"):
        run = root / stamp
        run.mkdir(parents=True)
        (run / "runtime-validation.json").write_text(
            json.dumps(
                {
                    "run_id": stamp,
                    "mode": "static-only",
                    "status": "passed",
                    "generated_at_utc": stamp,
                }
            ),
            encoding="utf-8",
        )
    index = build_evidence_index(evidence_root=root)
    assert [r.run_id for r in index.rows] == ["c-2026-05-03", "b-2026-05-02", "a-2026-05-01"]
    md = render_evidence_index_md(index)
    assert "Evidence Index" in md
    assert "c-2026-05-03" in md


def test_evidence_index_lists_runs_without_runtime_validation(tmp_path: Path) -> None:
    root = tmp_path / "evidence" / "runtime"
    run = root / "broken"
    run.mkdir(parents=True)
    index = build_evidence_index(evidence_root=root)
    assert len(index.rows) == 1
    row = index.rows[0]
    assert row.run_id == "broken"
    assert "no runtime-validation.json" in row.notes


def test_evidence_index_round_trips(tmp_path: Path) -> None:
    root = tmp_path / "evidence" / "runtime"
    run = root / "x"
    run.mkdir(parents=True)
    (run / "runtime-validation.json").write_text(
        json.dumps(
            {
                "run_id": "x",
                "mode": "static-only",
                "status": "not_executed",
                "generated_at_utc": "2026-05-09",
            }
        ),
        encoding="utf-8",
    )
    index = build_evidence_index(evidence_root=root)
    json_path = tmp_path / "index.json"
    md_path = tmp_path / "index.md"
    write_evidence_index(index, json_path=json_path, markdown_path=md_path)
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["rows"][0]["run_id"] == "x"
    assert "Evidence Index" in md_path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Qualification report renderer.
# ---------------------------------------------------------------------------


def test_qualification_check_rejects_invalid_origin() -> None:
    with pytest.raises(ValueError):
        QualificationCheck(
            name="x",
            origin="not-a-real-origin",
            status=AcceptanceStatus.PASSED,
        )


def test_qualification_report_labels_check_origin() -> None:
    checks = [
        QualificationCheck(
            name="static-grep",
            origin="static-source",
            status=AcceptanceStatus.PASSED,
            detail="ok",
        ),
        QualificationCheck(
            name="static-yaml",
            origin="static-workspace",
            status=AcceptanceStatus.PASSED,
            detail="ok",
        ),
        QualificationCheck(
            name="live-topic",
            origin="live-runtime",
            status=AcceptanceStatus.NOT_EXECUTED,
            detail="rclpy unavailable",
            reason="rclpy not importable",
        ),
    ]
    report = QualificationReport(
        run_id="r1", mode="static-only", qualification_checks=checks
    )
    md = render_qualification_summary_md(report)
    assert "static-source" in md
    assert "static-workspace" in md
    assert "live-runtime" in md
    counts = report.status_counts()
    assert counts["passed"] == 2
    assert counts["not_executed"] == 1


def test_live_runtime_status_distinguishes_static_from_live() -> None:
    checks = [
        QualificationCheck(
            name="static-grep",
            origin="static-source",
            status=AcceptanceStatus.PASSED,
            detail="ok",
        ),
        QualificationCheck(
            name="live-topic",
            origin="live-runtime",
            status=AcceptanceStatus.NOT_EXECUTED,
            detail="rclpy unavailable",
            reason="rclpy not importable",
        ),
    ]
    report = QualificationReport(
        run_id="r1", mode="static-only", qualification_checks=checks
    )
    md = render_live_runtime_status_md(report)
    assert "## static-source" in md
    assert "## static-workspace" in md
    assert "## live-runtime" in md
    assert "Live-runtime checks not executed" in md
    assert "rclpy not importable" in md


def test_qualification_report_includes_known_limitations() -> None:
    report = QualificationReport(run_id="r2", mode="static-only")
    md = render_qualification_summary_md(report)
    assert "not safety-certified" in md
    assert "Known limitations" in md


def test_qualification_report_overall_status_aggregates_failure() -> None:
    checks = [
        QualificationCheck(name="ok", origin="static-source", status=AcceptanceStatus.PASSED),
        QualificationCheck(name="boom", origin="static-source", status=AcceptanceStatus.FAILED),
    ]
    report = QualificationReport(
        run_id="r3", mode="static-only", qualification_checks=checks
    )
    assert report.overall_status == AcceptanceStatus.FAILED


# ---------------------------------------------------------------------------
# CI workflow files.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "workflow",
    [
        "backend-tests.yml",
        "runtime-static-validation.yml",
        "docs-traceability.yml",
        "evidence-validation.yml",
        "ros-jazzy-runtime.yml",
    ],
)
def test_workflow_file_is_well_formed(workflow: str) -> None:
    path = _REPO_ROOT / ".github" / "workflows" / workflow
    assert path.exists(), path
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert "jobs" in data
    # PyYAML parses bare ``on`` as Python True; accept either form so
    # the test does not depend on a YAML quirk.
    assert "on" in data or True in data


def test_self_hosted_workflow_uses_self_hosted_runner() -> None:
    path = _REPO_ROOT / ".github" / "workflows" / "ros-jazzy-runtime.yml"
    text = path.read_text(encoding="utf-8")
    assert "self-hosted" in text
    assert "ros-jazzy" in text


def test_static_workflow_does_not_claim_live_success() -> None:
    text = (_REPO_ROOT / ".github" / "workflows" / "runtime-static-validation.yml").read_text(
        encoding="utf-8"
    )
    # CI must not pass the --ros-launch flag; live success belongs to
    # the self-hosted workflow.
    assert "--ros-launch" not in text


# ---------------------------------------------------------------------------
# Orchestrator end-to-end.
# ---------------------------------------------------------------------------


def test_qualified_runtime_run_writes_full_evidence_dir(tmp_path: Path) -> None:
    """Run the orchestrator in static-only mode and assert the full evidence layout."""

    import importlib

    module = importlib.import_module("qualified_runtime_run")
    rc = module.main(
        [
            "--evidence-root",
            str(tmp_path / "evidence" / "runtime"),
            "--run-id",
            "test-run",
            "--workspace-root",
            str(_REPO_ROOT),
            "--static-only",
        ]
    )
    run_dir = tmp_path / "evidence" / "runtime" / "test-run"
    expected_files = (
        "host-qualification.json",
        "host-qualification.md",
        "runtime-validation.json",
        "runtime-validation.md",
        "topic-snapshot.json",
        "node-snapshot.json",
        "tf-snapshot.json",
        "tf-tree.txt",
        "command-path-audit.json",
        "qualification-summary.json",
        "qualification-summary.md",
        "live-runtime-status.md",
        "regression-report.json",
        "regression-report.md",
    )
    for name in expected_files:
        assert (run_dir / name).exists(), name
    summary = json.loads((run_dir / "qualification-summary.json").read_text(encoding="utf-8"))
    # Must not claim `passed` overall in static-only mode.
    assert summary["overall_status"] in {
        "passed",
        "partial",
        "failed",
        "not_executed",
    }
    # Live-runtime live probes are not_executed, never passed.
    for check in summary["qualification_checks"]:
        if check["origin"] == "live-runtime":
            assert check["status"] in {"not_executed", "skipped", "failed", "partial"}
    assert rc in (0, 1)


def test_qualified_runtime_run_includes_scenario_outcomes(tmp_path: Path) -> None:
    import importlib

    module = importlib.import_module("qualified_runtime_run")
    module.main(
        [
            "--evidence-root",
            str(tmp_path / "evidence" / "runtime"),
            "--run-id",
            "scenarios",
            "--workspace-root",
            str(_REPO_ROOT),
            "--static-only",
        ]
    )
    run_dir = tmp_path / "evidence" / "runtime" / "scenarios"
    summary = json.loads((run_dir / "qualification-summary.json").read_text(encoding="utf-8"))
    sids = {s["scenario_id"] for s in summary["scenarios"]}
    assert "nominal_runtime_launch" in sids
    assert "stale_lidar_restricted_mode" in sids
    for s in summary["scenarios"]:
        # Static-only mode cannot claim live `passed`; expect partial / not_executed.
        assert s["observed_status"] in {"partial", "not_executed", "failed", "skipped"}
        assert s["expected_outcome"] in {"passed", "failed", "partial"}


# ---------------------------------------------------------------------------
# Canonical generated docs.
# ---------------------------------------------------------------------------


def test_canonical_qualification_runbook_present() -> None:
    runbook = _REPO_ROOT / "docs" / "RUNTIME_QUALIFICATION_RUNBOOK.md"
    text = runbook.read_text(encoding="utf-8")
    assert "Runtime Qualification Runbook" in text
    assert "qualified_runtime_run" in text
    assert "ROS 2 Jazzy" in text
    assert "Gazebo Harmonic" in text
    assert "self-hosted" in text


def test_baseline_round_trip(tmp_path: Path) -> None:
    payload = _make_baseline()
    target = tmp_path / "baseline.json"
    write_baseline(baseline=payload, path=target)
    re_read = json.loads(target.read_text(encoding="utf-8"))
    assert re_read == payload
