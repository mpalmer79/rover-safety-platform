"""Tests for the command-path audit."""

from __future__ import annotations

import json
from pathlib import Path

from app.domain.identifiers import RunId, SequentialIdGenerator
from app.domain.scenarios import ScenarioDefinition
from app.domain.time import ManualClock
from app.simulation.engine import SimulationEngine
from app.verification.acceptance import AcceptanceStatus
from app.verification.command_audit import audit_command_path


_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCENARIOS = _REPO_ROOT / "backend" / "scenarios"


def _run(scenario_file: str, tmp_path: Path) -> Path:
    sc = ScenarioDefinition.from_json_file(_SCENARIOS / scenario_file)
    eng = SimulationEngine(
        scenario=sc,
        runs_root=tmp_path,
        run_id=RunId(f"run-{sc.scenario_id}"),
        clock=ManualClock(),
        id_generator=SequentialIdGenerator(),
    )
    eng.run()
    return eng.recorder.run_dir


def test_audit_passes_on_nominal_run(tmp_path: Path) -> None:
    run_dir = _run("nominal_run.json", tmp_path)
    result = audit_command_path(run_dir)
    assert result.ok, result.errors
    assert result.command_count > 0


def test_audit_passes_on_safe_stop_scenario(tmp_path: Path) -> None:
    run_dir = _run("stale_lidar_restricted_mode.json", tmp_path)
    result = audit_command_path(run_dir)
    assert result.ok, result.errors
    # SAFE_STOP forces zero motion: every safe-stop authorized
    # command must carry zero linear/angular.
    assert result.zeroed_count > 0


def test_audit_passes_on_estop_scenario(tmp_path: Path) -> None:
    run_dir = _run("estop_latched_manual_reset_required.json", tmp_path)
    result = audit_command_path(run_dir)
    assert result.ok, result.errors
    # E-stop should produce a stream of zeroed commands.
    assert result.zeroed_count > 0


def test_audit_detects_non_zero_motion_in_safe_stop(tmp_path: Path) -> None:
    """Corrupt commands.jsonl to inject a non-zero authorized command
    in SAFE_STOP and confirm the audit fails.
    """

    run_dir = _run("stale_lidar_restricted_mode.json", tmp_path)
    cmds = run_dir / "commands.jsonl"
    rows = cmds.read_text().splitlines()
    corrupted = False
    for i, raw in enumerate(rows):
        if not raw:
            continue
        payload = json.loads(raw)
        auth = payload.get("authorized") or {}
        if auth.get("safety_state") == "SAFE_STOP":
            auth["linear_velocity"] = 0.5
            auth["angular_velocity"] = 0.0
            payload["authorized"] = auth
            rows[i] = json.dumps(payload, separators=(",", ":"))
            corrupted = True
            break
    assert corrupted, "test setup: no SAFE_STOP command found to corrupt"
    cmds.write_text("\n".join(rows) + "\n", encoding="utf-8")
    result = audit_command_path(run_dir)
    assert result.status == AcceptanceStatus.FAILED
    assert any("non-zero motion" in e or "authorized non-zero" in e for e in result.errors)


def test_audit_detects_unauthorized_source(tmp_path: Path) -> None:
    run_dir = _run("nominal_run.json", tmp_path)
    cmds = run_dir / "commands.jsonl"
    rows = cmds.read_text().splitlines()
    payload = json.loads(rows[0])
    payload["authorized"]["source"] = "mission.orchestrator"
    rows[0] = json.dumps(payload, separators=(",", ":"))
    cmds.write_text("\n".join(rows) + "\n", encoding="utf-8")
    result = audit_command_path(run_dir)
    assert result.status == AcceptanceStatus.FAILED
    assert any("non-supervisor source" in e for e in result.errors)


def test_audit_returns_not_executed_when_run_dir_missing(tmp_path: Path) -> None:
    result = audit_command_path(tmp_path / "does_not_exist")
    assert result.status == AcceptanceStatus.NOT_EXECUTED
