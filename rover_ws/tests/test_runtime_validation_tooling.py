"""Phase 4 runtime-validation tests.

These tests exercise the static-only path of every probe and the
orchestrator. They run on a workstation that has neither rclpy nor
Gazebo, so they intentionally do not import the live-mode helpers.

Tests pin:

* the structural contract of ``EXPECTED_TOPICS``, ``EXPECTED_NODES``,
  and ``EXPECTED_FRAMES``;
* the per-probe static-mode aggregate status against the current
  workspace artefacts;
* the orchestrator output: presence of every required evidence file,
  the canonical Markdown report, and the honest-status invariant
  (no ``passed`` for live-only checks in static-only mode).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


_TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))


from app.runtime_validation import (  # noqa: E402  (sys.path mutated in conftest)
    EXPECTED_FRAMES,
    EXPECTED_NODES,
    EXPECTED_ROOT_FRAME,
    EXPECTED_TOPICS,
    EvidenceLayout,
    RUNTIME_EVIDENCE_FILES,
    RuntimeCheck,
    RuntimeReport,
    StaticValidationResult,
    render_runtime_report_md,
    run_static_validation,
)
from app.runtime_validation.report_renderer import render_known_limitations_md
from app.verification.acceptance import AcceptanceStatus


# ---------------------------------------------------------------------------
# Library: declared expectations.
# ---------------------------------------------------------------------------


def test_expected_topics_have_well_formed_metadata() -> None:
    assert EXPECTED_TOPICS, "EXPECTED_TOPICS must not be empty"
    seen: set[str] = set()
    for topic in EXPECTED_TOPICS:
        assert topic.name.startswith("/"), topic.name
        assert "/msg/" in topic.msg_type, topic.msg_type
        assert topic.expected_period_ms > 0, topic.name
        assert topic.freshness_window_ms == -1 or topic.freshness_window_ms > 0
        assert topic.name not in seen, f"duplicate topic {topic.name}"
        seen.add(topic.name)


def test_required_safety_topics_present() -> None:
    names = {t.name for t in EXPECTED_TOPICS if t.required}
    for required_name in (
        "/cmd_vel_authorized",
        "/safety/state",
        "/safety/events",
        "/scan",
        "/imu",
        "/odom",
        "/tf",
        "/tf_static",
        "/system/health",
    ):
        assert required_name in names, required_name


def test_expected_nodes_cover_safety_simulation_and_observability() -> None:
    names = {n.node_name for n in EXPECTED_NODES}
    assert "rover_safety_bridge" in names
    assert "ros_gz_bridge" in names
    assert "robot_state_publisher" in names
    assert "rover_runtime_summary" in names
    assert "rover_event_recorder" in names


def test_expected_tf_frames_include_runtime_root() -> None:
    names = {f.name for f in EXPECTED_FRAMES}
    assert EXPECTED_ROOT_FRAME in names
    assert "base_footprint" in names
    assert "base_link" in names
    assert "lidar_link" in names
    runtime_root = next(f for f in EXPECTED_FRAMES if f.name == EXPECTED_ROOT_FRAME)
    assert runtime_root.parent is None
    assert runtime_root.is_static is False


def test_evidence_layout_enforces_known_filenames(tmp_path: Path) -> None:
    layout = EvidenceLayout(root=tmp_path, run_id="r1").ensure()
    assert layout.run_dir.exists()
    for name in RUNTIME_EVIDENCE_FILES:
        assert layout.path(name).parent == layout.run_dir
    with pytest.raises(ValueError):
        layout.path("not-an-allowed-file.json")


# ---------------------------------------------------------------------------
# Static workspace validator.
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def test_static_validator_passes_on_current_workspace(repo_root: Path) -> None:
    result = run_static_validation(workspace_root=repo_root)
    assert isinstance(result, StaticValidationResult)
    fail = [c for c in result.checks if c.status == AcceptanceStatus.FAILED]
    assert not fail, [c.as_dict() for c in fail]
    # The aggregate must be at least PASSED (not FAILED). It may be
    # PARTIAL if any optional sub-check is short.
    assert result.status in {
        AcceptanceStatus.PASSED,
        AcceptanceStatus.NOT_EXECUTED,
        AcceptanceStatus.PARTIAL,
    }


def test_static_validator_safety_invariant_passes(repo_root: Path) -> None:
    result = run_static_validation(workspace_root=repo_root)
    invariant = next(
        c for c in result.checks
        if c.name == "safety_bridge_authority_invariant"
    )
    assert invariant.status == AcceptanceStatus.PASSED, invariant.as_dict()


# ---------------------------------------------------------------------------
# Per-probe static-mode tests.
# ---------------------------------------------------------------------------


def _run_probe_main(module_name: str, argv: list[str]) -> int:
    import importlib

    module = importlib.import_module(module_name)
    return module.main(argv)


@pytest.fixture
def evidence_root(tmp_path: Path) -> Path:
    return tmp_path / "evidence" / "runtime"


def _common_argv(
    *,
    repo_root: Path,
    evidence_root: Path,
    run_id: str,
) -> list[str]:
    return [
        "--evidence-root",
        str(evidence_root),
        "--run-id",
        run_id,
        "--workspace-root",
        str(repo_root),
        "--static-only",
    ]


def test_topic_probe_static_mode_lists_expected_topics(
    repo_root: Path, evidence_root: Path
) -> None:
    rc = _run_probe_main(
        "topic_probe",
        _common_argv(
            repo_root=repo_root, evidence_root=evidence_root, run_id="t1"
        ),
    )
    snapshot = json.loads(
        (evidence_root / "t1" / "topic-snapshot.json").read_text(encoding="utf-8")
    )
    rows = snapshot["static"]["rows"]
    declared = {r["topic"] for r in rows if r["declared_in_workspace"]}
    for required in (
        "/cmd_vel_authorized",
        "/safety/state",
        "/safety/events",
        "/scan",
    ):
        assert required in declared, required
    assert rc != 0  # static-only must not claim "passed" overall
    assert snapshot["mode"] == "static-only"


def test_topic_probe_static_mode_marks_live_checks_not_executed(
    repo_root: Path, evidence_root: Path
) -> None:
    _run_probe_main(
        "topic_probe",
        _common_argv(
            repo_root=repo_root, evidence_root=evidence_root, run_id="t2"
        ),
    )
    snapshot = json.loads(
        (evidence_root / "t2" / "topic-snapshot.json").read_text(encoding="utf-8")
    )
    rows = snapshot["static"]["rows"]
    for row in rows:
        assert row["live_advertised_status"] == "not_executed"
        assert row["type_match_status"] == "not_executed"
        # never claim passed for a live check in static-only mode
        assert row["live_advertised"] is False


def test_tf_probe_static_mode_passes_against_workspace_urdf(
    repo_root: Path, evidence_root: Path
) -> None:
    _run_probe_main(
        "tf_probe",
        _common_argv(
            repo_root=repo_root, evidence_root=evidence_root, run_id="tf1"
        ),
    )
    snapshot = json.loads(
        (evidence_root / "tf1" / "tf-snapshot.json").read_text(encoding="utf-8")
    )
    static = snapshot["static"]
    assert not static["static_failures"], static["static_failures"]
    rows = static["rows"]
    base_footprint = next(r for r in rows if r["frame"] == "base_footprint")
    assert base_footprint["declared_in_urdf"] is True
    # Parent edge for base_footprint (odom -> base_footprint) is
    # published at runtime, so the static parent-match must be skipped
    # rather than failed.
    assert base_footprint["parent_match_status"] == "skipped"
    assert (evidence_root / "tf1" / "tf-tree.txt").exists()


def test_command_path_probe_static_mode_passes(
    repo_root: Path, evidence_root: Path
) -> None:
    rc = _run_probe_main(
        "command_path_probe",
        _common_argv(
            repo_root=repo_root, evidence_root=evidence_root, run_id="cp1"
        ),
    )
    snapshot = json.loads(
        (evidence_root / "cp1" / "command-path-audit.json").read_text(encoding="utf-8")
    )
    invariants = snapshot["static"]["invariants"]
    by_name = {i["name"]: i["status"] for i in invariants}
    assert by_name["authorized_publisher_present"] == "passed"
    assert by_name["authorized_publisher_is_safety_bridge"] == "passed"
    assert by_name["raw_cmd_vel_not_published_by_workspace"] == "passed"
    assert by_name["bridge_yaml_does_not_route_cmd_vel"] == "passed"
    assert rc == 0  # command-path is statically verifiable end-to-end


def test_launch_smoke_static_mode_passes(
    repo_root: Path, evidence_root: Path
) -> None:
    _run_probe_main(
        "launch_smoke_test",
        _common_argv(
            repo_root=repo_root, evidence_root=evidence_root, run_id="ls1"
        ),
    )
    snapshot = json.loads(
        (evidence_root / "ls1" / "node-snapshot.json").read_text(encoding="utf-8")
    )
    static = snapshot["static"]
    assert static["launch_file_present"] is True
    assert not static["static_failures"], static["static_failures"]
    assert (evidence_root / "ls1" / "launch-log.txt").exists()


def test_runtime_capture_static_mode_runs_deterministic_engine(
    repo_root: Path, evidence_root: Path, tmp_path: Path
) -> None:
    runs_root = tmp_path / "runs" / "runtime"
    rc = _run_probe_main(
        "runtime_capture",
        [
            *_common_argv(
                repo_root=repo_root, evidence_root=evidence_root, run_id="cap1"
            ),
            "--scenario",
            "stale_lidar_restricted_mode",
            "--runs-root",
            str(runs_root),
        ],
    )
    out = json.loads(
        (
            evidence_root / "cap1" / "runtime-capture-stale_lidar_restricted_mode.json"
        ).read_text(encoding="utf-8")
    )
    assert out["scenario"] == "stale_lidar_restricted_mode"
    assert out["static"]["status"] == "passed", out["static"]
    assert rc == 0


# ---------------------------------------------------------------------------
# Orchestrator: end-to-end static-only run.
# ---------------------------------------------------------------------------


def test_orchestrator_static_only_writes_every_evidence_file(
    repo_root: Path, evidence_root: Path
) -> None:
    rc = _run_probe_main(
        "live_runtime_validator",
        _common_argv(
            repo_root=repo_root, evidence_root=evidence_root, run_id="orch1"
        ),
    )
    run_dir = evidence_root / "orch1"
    for name in RUNTIME_EVIDENCE_FILES:
        assert (run_dir / name).exists(), name
    json_path = run_dir / "runtime-validation.json"
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    # No live check may report `passed` in static-only mode.
    for check in payload["checks"]:
        if check["name"] in {
            "launch_smoke_test",
            "topic_probe",
            "tf_probe",
        }:
            assert check["status"] in {
                "not_executed",
                "skipped",
                "failed",
                "partial",
            }, check
    # The aggregate status is not_executed (or partial / failed) in this
    # environment because rclpy is not available; it is never `passed`.
    assert payload["status"] != "passed"
    # Markdown was rendered.
    md = (run_dir / "runtime-validation.md").read_text(encoding="utf-8")
    assert "Runtime Validation Report" in md
    assert "not safety-certified" in md
    assert rc != 0  # non-zero because aggregate isn't "passed"


def test_runtime_report_distinguishes_status_categories() -> None:
    checks = [
        RuntimeCheck(name="x", status=AcceptanceStatus.PASSED, detail="ok"),
        RuntimeCheck(
            name="y",
            status=AcceptanceStatus.NOT_EXECUTED,
            detail="needs Jazzy",
            reason="rclpy unavailable",
        ),
        RuntimeCheck(name="z", status=AcceptanceStatus.FAILED, detail="boom"),
    ]
    report = RuntimeReport(run_id="r1", mode="static-only", checks=checks)
    counts = report.status_counts()
    assert counts["passed"] == 1
    assert counts["failed"] == 1
    assert counts["not_executed"] == 1
    md = render_runtime_report_md(report)
    assert "`passed`" in md
    assert "`failed`" in md
    assert "`not_executed`" in md
    assert "rclpy unavailable" in md
    # Aggregate prefers FAILED over PASSED / NOT_EXECUTED.
    assert report.status == AcceptanceStatus.FAILED


def test_runtime_report_includes_known_limitations() -> None:
    report = RuntimeReport(run_id="r2", mode="static-only", checks=[])
    md = render_runtime_report_md(report)
    assert "Known limitations" in md
    assert "not safety-certified" in md
    standalone = render_known_limitations_md(report)
    assert "Known limitations" in standalone
    assert "Run id: `r2`" in standalone


def test_canonical_runtime_report_in_docs_is_present() -> None:
    """The repo ships a canonical static-only runtime report.

    The orchestrator is invoked with ``--canonical-report`` from CI;
    this test guards against accidental deletion.
    """

    repo_root = Path(__file__).resolve().parents[2]
    canonical = repo_root / "docs" / "RUNTIME_VALIDATION_REPORT.md"
    text = canonical.read_text(encoding="utf-8")
    assert "Runtime Validation Report" in text
    assert "not safety-certified" in text


def test_canonical_runtime_runbook_in_docs_is_present() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    runbook = repo_root / "docs" / "RUNTIME_VALIDATION_RUNBOOK.md"
    text = runbook.read_text(encoding="utf-8")
    assert "Runtime Validation Runbook" in text
    assert "ROS 2 Jazzy" in text
    assert "Gazebo" in text
    assert "ros2 launch rover_bringup full_system.launch.py" in text
    assert "live_runtime_validator" in text
