"""Phase 13 live-runtime CLI tests (rover_ws side).

These tests exercise the CLI surface of the Phase 13 tools without
requiring ROS, Gazebo, Foxglove, or a real bag. The tools must
behave honestly under the not-on-Jazzy-host fall-back: every live
run produces a coherent ``not_executed`` evidence bundle with a
structured reason — no fabrication.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


_REPO_ROOT = Path(__file__).resolve().parents[2]
_TOOLS_DIR = _REPO_ROOT / "rover_ws" / "tools"
_BACKEND_DIR = _REPO_ROOT / "backend"

for p in (_TOOLS_DIR, _BACKEND_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


def _load_cli(name: str):
    path = _TOOLS_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_cli_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


# --- live_bag_capture ----------------------------------------------------


def test_live_bag_capture_dry_run_writes_not_executed_bundle(tmp_path: Path):
    cli = _load_cli("live_bag_capture")
    plan_path = _REPO_ROOT / "live-runtime" / "scenario-plans" / "core-live-qualification.yaml"
    runner = _REPO_ROOT / "live-runtime" / "runner-profile.json"
    code = cli.main(
        [
            "--plan",
            str(plan_path),
            "--evidence-root",
            str(tmp_path),
            "--run-id",
            "test-not-executed",
            "--runner-profile",
            str(runner),
            "--dry-run",
            "--started-at",
            "2026-05-12T00:00:00+00:00",
            "--finished-at",
            "2026-05-12T00:00:00+00:00",
            "--json",
        ]
    )
    assert code == 0
    bundle = tmp_path / "test-not-executed"
    assert bundle.is_dir()
    summary = json.loads((bundle / "live-run-summary.json").read_text("utf-8"))
    assert summary["status"] == "not_executed"
    assert summary["bag_status"] == "not_executed"
    manifest = json.loads((bundle / "bag-manifest.json").read_text("utf-8"))
    assert manifest["bag_status"] == "not_executed"
    assert manifest["not_executed_reason"]


def test_live_bag_capture_does_not_run_live_without_runner_profile(tmp_path: Path):
    cli = _load_cli("live_bag_capture")
    plan_path = _REPO_ROOT / "live-runtime" / "scenario-plans" / "core-live-qualification.yaml"
    code = cli.main(
        [
            "--plan",
            str(plan_path),
            "--evidence-root",
            str(tmp_path),
            "--run-id",
            "no-runner",
            "--started-at",
            "2026-05-12T00:00:00+00:00",
            "--finished-at",
            "2026-05-12T00:00:00+00:00",
            "--json",
        ]
    )
    assert code == 0
    summary = json.loads((tmp_path / "no-runner" / "live-run-summary.json").read_text("utf-8"))
    assert summary["status"] == "not_executed"


# --- validate_live_runtime_evidence -------------------------------------


def test_validator_passes_on_clean_not_executed_bundle(tmp_path: Path):
    cli = _load_cli("live_bag_capture")
    plan_path = _REPO_ROOT / "live-runtime" / "scenario-plans" / "core-live-qualification.yaml"
    runner = _REPO_ROOT / "live-runtime" / "runner-profile.json"
    cli.main(
        [
            "--plan",
            str(plan_path),
            "--evidence-root",
            str(tmp_path),
            "--run-id",
            "clean-ne",
            "--runner-profile",
            str(runner),
            "--dry-run",
            "--started-at",
            "t",
            "--finished-at",
            "t",
        ]
    )
    validator = _load_cli("validate_live_runtime_evidence")
    code = validator.main(
        [
            "--bundle",
            str(tmp_path / "clean-ne"),
            "--json",
        ]
    )
    assert code == 0


def test_validator_fails_when_bundle_missing(tmp_path: Path):
    validator = _load_cli("validate_live_runtime_evidence")
    code = validator.main(["--bundle", str(tmp_path / "does-not-exist")])
    assert code == 1


def test_validator_fails_when_required_files_missing(tmp_path: Path):
    bundle = tmp_path / "missing-files"
    bundle.mkdir()
    (bundle / "metadata.json").write_text("{}", encoding="utf-8")
    validator = _load_cli("validate_live_runtime_evidence")
    code = validator.main(["--bundle", str(bundle)])
    assert code == 1


# --- process_live_runtime_evidence --------------------------------------


def test_process_dry_run_preserves_bag_status(tmp_path: Path):
    """A not_executed bundle must NOT trigger replay-review or analytics."""

    cli = _load_cli("live_bag_capture")
    plan_path = _REPO_ROOT / "live-runtime" / "scenario-plans" / "core-live-qualification.yaml"
    runner = _REPO_ROOT / "live-runtime" / "runner-profile.json"
    cli.main(
        [
            "--plan",
            str(plan_path),
            "--evidence-root",
            str(tmp_path),
            "--run-id",
            "process-ne",
            "--runner-profile",
            str(runner),
            "--dry-run",
            "--started-at",
            "t",
            "--finished-at",
            "t",
        ]
    )
    proc = _load_cli("process_live_runtime_evidence")
    plan = proc.plan_actions(tmp_path / "process-ne")
    assert plan["bag_status"] == "not_executed"
    assert plan["preserved_bag_status"] == "not_executed"
    steps = {a["step"]: a for a in plan["actions"]}
    # Replay-review and analytics MUST NOT qualify for a not_executed bundle.
    assert steps["replay_review_bundle"]["qualifies"] is False
    assert steps["replay_analytics"]["qualifies"] is False


# --- maturity report ----------------------------------------------------


def test_maturity_report_writer_writes_json_and_md(tmp_path: Path):
    cli = _load_cli("generate_live_runtime_maturity_report")
    out_json = tmp_path / "m.json"
    out_md = tmp_path / "m.md"
    code = cli.main(
        [
            "--evidence-root",
            str(tmp_path / "no_evidence_here"),
            "--out-json",
            str(out_json),
            "--out-md",
            str(out_md),
            "--reference-time",
            "2026-05-12T00:00:00+00:00",
            "--json",
        ]
    )
    assert code == 0
    assert out_json.exists()
    assert out_md.exists()
    payload = json.loads(out_json.read_text("utf-8"))
    assert payload["runs_total"] == 0
    assert payload["bag_counters"]["bag_backed"] == 0


# --- workflow file shape ------------------------------------------------


def test_workflow_file_self_hosted_only():
    text = (_REPO_ROOT / ".github" / "workflows" / "live-runtime-evidence.yml").read_text(
        encoding="utf-8"
    )
    assert "self-hosted" in text
    for forbidden in ("ubuntu-latest", "ubuntu-22.04", "ubuntu-24.04"):
        assert forbidden not in text


def test_workflow_dispatch_only():
    text = (_REPO_ROOT / ".github" / "workflows" / "live-runtime-evidence.yml").read_text(
        encoding="utf-8"
    )
    assert "workflow_dispatch" in text
    for forbidden in ("\n  push:", "\n  pull_request:", "\n  schedule:"):
        assert forbidden not in text
