"""Phase 14 live runtime tool tests.

Exercises the rover_ws/tools live runtime CLIs WITHOUT requiring
ROS, Gazebo, or rosbag2 to be installed. The tests cover dry-run
and static-check-only flows, the validate tool's honesty checks,
and the bag-capture tool's not_executed fallback when ``ros2`` is
not on PATH.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


_TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))


REPO_ROOT = Path(__file__).resolve().parents[2]
SCENARIO_PLAN = REPO_ROOT / "live-runtime" / "scenario-plans" / "smoke-live-runtime.yaml"
RUNNER_TEMPLATE = REPO_ROOT / "live-runtime" / "runner-profile.template.json"
RUNNER_EXAMPLE = REPO_ROOT / "live-runtime" / "runner-profile.local.example.json"


def _run_tool(tool: str, *args: str) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(_TOOLS_DIR / tool), *args]
    return subprocess.run(  # noqa: S603 - curated command list
        cmd,
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
    )


def test_pipeline_dry_run_produces_not_executed_evidence(tmp_path: Path) -> None:
    out = tmp_path / "run-dry"
    res = _run_tool(
        "run_live_runtime_pipeline.py",
        "--scenario-plan",
        str(SCENARIO_PLAN),
        "--runner-profile",
        str(RUNNER_TEMPLATE),
        "--output",
        str(out),
        "--dry-run",
        "--json",
    )
    assert res.returncode == 0, res.stderr
    summary = json.loads(res.stdout)
    assert summary["mode"] == "dry_run"
    assert summary["status"] == "not_executed"
    assert summary["is_bag_backed"] is False
    assert (out / "evidence.json").is_file()


def test_pipeline_static_check_only_produces_static_only_evidence(
    tmp_path: Path,
) -> None:
    out = tmp_path / "run-static"
    res = _run_tool(
        "run_live_runtime_pipeline.py",
        "--scenario-plan",
        str(SCENARIO_PLAN),
        "--runner-profile",
        str(RUNNER_TEMPLATE),
        "--output",
        str(out),
        "--static-check-only",
        "--json",
    )
    assert res.returncode == 0, res.stderr
    summary = json.loads(res.stdout)
    assert summary["mode"] == "static_only"
    assert summary["is_bag_backed"] is False


def test_pipeline_falls_back_to_template_when_local_profile_missing(
    tmp_path: Path,
) -> None:
    out = tmp_path / "run-fallback"
    res = _run_tool(
        "run_live_runtime_pipeline.py",
        "--scenario-plan",
        str(SCENARIO_PLAN),
        "--runner-profile",
        str(tmp_path / "no-such.json"),
        "--runner-profile-template",
        str(RUNNER_TEMPLATE),
        "--output",
        str(out),
        "--dry-run",
        "--json",
    )
    assert res.returncode == 0, res.stderr
    summary = json.loads(res.stdout)
    assert summary["runner_profile"] == str(RUNNER_TEMPLATE)
    assert summary["is_bag_backed"] is False


def test_process_evidence_dry_run_does_not_label_bag_backed(tmp_path: Path) -> None:
    out = tmp_path / "run-proc"
    res = _run_tool(
        "process_live_runtime_evidence.py",
        "--runner-profile",
        str(RUNNER_TEMPLATE),
        "--scenario-plan",
        str(SCENARIO_PLAN),
        "--output",
        str(out),
        "--run-id",
        "run-proc",
        "--dry-run",
        "--json",
    )
    assert res.returncode == 0, res.stderr
    summary = json.loads(res.stdout)
    assert summary["mode"] == "dry_run"
    assert summary["is_bag_backed"] is False
    evidence = json.loads((out / "evidence.json").read_text(encoding="utf-8"))
    assert evidence["mode"] == "dry_run"
    assert evidence["bag_manifest"]["status"] == "not_executed"


def test_validate_passes_on_dry_run_evidence(tmp_path: Path) -> None:
    out = tmp_path / "run-vd"
    pipeline = _run_tool(
        "run_live_runtime_pipeline.py",
        "--scenario-plan",
        str(SCENARIO_PLAN),
        "--runner-profile",
        str(RUNNER_TEMPLATE),
        "--output",
        str(out),
        "--dry-run",
    )
    assert pipeline.returncode == 0, pipeline.stderr

    res = _run_tool(
        "validate_live_runtime_evidence.py",
        "--evidence-dir",
        str(out),
        "--json",
    )
    assert res.returncode == 0, res.stderr
    summary = json.loads(res.stdout)
    assert summary["status"] == "passed"


def test_validate_detects_tampered_evidence_claiming_bag_backed(
    tmp_path: Path,
) -> None:
    out = tmp_path / "run-tamper"
    pipeline = _run_tool(
        "run_live_runtime_pipeline.py",
        "--scenario-plan",
        str(SCENARIO_PLAN),
        "--runner-profile",
        str(RUNNER_TEMPLATE),
        "--output",
        str(out),
        "--dry-run",
    )
    assert pipeline.returncode == 0, pipeline.stderr

    evidence_path = out / "evidence.json"
    data = json.loads(evidence_path.read_text(encoding="utf-8"))
    # Tamper: claim bag_backed without changing the bag manifest.
    data["mode"] = "bag_backed"
    evidence_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    res = _run_tool(
        "validate_live_runtime_evidence.py",
        "--evidence-dir",
        str(out),
        "--json",
    )
    assert res.returncode != 0, res.stdout
    summary = json.loads(res.stdout)
    assert summary["status"] == "failed"
    assert any(
        "bag_backed" in f["check"] and f["status"] == "failed"
        for f in summary["findings"]
    )


def test_bag_capture_dry_run_emits_not_executed_manifest(tmp_path: Path) -> None:
    out = tmp_path / "bag-dry"
    manifest_path = tmp_path / "bag-manifest.json"
    res = _run_tool(
        "live_bag_capture.py",
        "--scenario-plan",
        str(SCENARIO_PLAN),
        "--output",
        str(out),
        "--run-id",
        "bag-dry",
        "--manifest-only",
        str(manifest_path),
        "--dry-run",
        "--json",
    )
    assert res.returncode == 0, res.stderr
    payload = json.loads(res.stdout)
    assert payload["status"] == "not_executed"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["status"] == "not_executed"


@pytest.mark.skipif(
    shutil.which("ros2") is not None,
    reason="ros2 is on PATH; the not_executed fallback only applies when missing",
)
def test_bag_capture_without_ros2_emits_not_executed_manifest(tmp_path: Path) -> None:
    out = tmp_path / "bag-no-ros"
    manifest_path = tmp_path / "bag-no-ros-manifest.json"
    res = _run_tool(
        "live_bag_capture.py",
        "--scenario-plan",
        str(SCENARIO_PLAN),
        "--output",
        str(out),
        "--run-id",
        "bag-no-ros",
        "--manifest-only",
        str(manifest_path),
        "--json",
    )
    assert res.returncode == 0, res.stderr
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["status"] == "not_executed"
    assert "ros2 CLI not on PATH" in manifest["reason"]


def test_pipeline_promote_baseline_skipped_for_dry_run(tmp_path: Path) -> None:
    out = tmp_path / "run-prom"
    baseline = tmp_path / "baseline.json"
    res = _run_tool(
        "run_live_runtime_pipeline.py",
        "--scenario-plan",
        str(SCENARIO_PLAN),
        "--runner-profile",
        str(RUNNER_TEMPLATE),
        "--output",
        str(out),
        "--maturity-baseline",
        str(baseline),
        "--dry-run",
        "--promote-baseline",
        "--json",
    )
    assert res.returncode == 0, res.stderr
    summary = json.loads(res.stdout)
    assert "left unchanged" in summary["baseline"]
    data = json.loads(baseline.read_text(encoding="utf-8"))
    assert data["status"] == "not_established"


def test_pipeline_rejects_invalid_runner_profile(tmp_path: Path) -> None:
    bad = tmp_path / "bad-profile.json"
    bad.write_text(
        json.dumps(
            {
                "runner_id": "x",
                "runner_status": "qualified",
                "qualification_status": "passed",
                "labels": ["self-hosted"],
                "host_os": "Ubuntu 24.04 LTS",
                "ros_distro": "jazzy",
                "gazebo_version": "harmonic",
                "python_version": "3.12",
                "workspace_path": "/tmp/ws",
                "bag_format": "mcap",
                "last_qualified_at": None,
                "last_qualified_run_id": None,
                "last_bag_backed_run_id": None,
                "known_limitations": [],
                "notes": [],
            }
        ),
        encoding="utf-8",
    )
    res = _run_tool(
        "run_live_runtime_pipeline.py",
        "--scenario-plan",
        str(SCENARIO_PLAN),
        "--runner-profile",
        str(bad),
        "--output",
        str(tmp_path / "out"),
        "--dry-run",
    )
    assert res.returncode == 2, res.stdout + res.stderr
    assert "runner profile validation failed" in res.stderr
