"""Tests for the safety transition audit."""

from __future__ import annotations

import json
from pathlib import Path

from app.domain.identifiers import RunId, SequentialIdGenerator
from app.domain.scenarios import ScenarioDefinition
from app.domain.time import ManualClock
from app.simulation.engine import SimulationEngine
from app.verification.acceptance import AcceptanceStatus
from app.verification.safety_audit import audit_safety_transitions


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
    result = audit_safety_transitions(run_dir)
    assert result.ok, result.errors
    # We expect at least BOOT->INACTIVE->ACTIVE_NORMAL.
    assert result.transition_count >= 2


def test_audit_passes_on_estop_scenario(tmp_path: Path) -> None:
    run_dir = _run("estop_latched_manual_reset_required.json", tmp_path)
    result = audit_safety_transitions(run_dir)
    assert result.ok
    assert result.final_state == "E_STOP_LATCHED"


def test_audit_passes_on_safe_stop_scenario(tmp_path: Path) -> None:
    run_dir = _run("stale_lidar_restricted_mode.json", tmp_path)
    result = audit_safety_transitions(run_dir)
    assert result.ok
    assert result.final_state == "SAFE_STOP"


def test_audit_detects_invalid_transition(tmp_path: Path) -> None:
    """Corrupt events.jsonl to inject a forbidden transition (E_STOP_LATCHED -> ACTIVE_NORMAL)
    and confirm the audit fails.
    """

    run_dir = _run("estop_latched_manual_reset_required.json", tmp_path)
    events_path = run_dir / "events.jsonl"
    rows = events_path.read_text().splitlines()
    corrupted = False
    for i, raw in enumerate(rows):
        if not raw:
            continue
        payload = json.loads(raw)
        if payload.get("event_type") == "safety_transition.entered":
            payload["safety_state"] = "ACTIVE_NORMAL"
            attrs = payload.get("attributes") or {}
            if attrs.get("from_state") == "ACTIVE_NORMAL" and attrs.get("to_state") == "E_STOP_LATCHED":
                attrs["from_state"] = "E_STOP_LATCHED"
                attrs["to_state"] = "ACTIVE_NORMAL"
                payload["attributes"] = attrs
                rows[i] = json.dumps(payload, separators=(",", ":"))
                corrupted = True
                break
    assert corrupted
    events_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    result = audit_safety_transitions(run_dir)
    assert result.status == AcceptanceStatus.FAILED
    assert any(
        "forbidden transition" in e or "E_STOP_LATCHED" in e for e in result.errors
    )


def test_audit_returns_not_executed_when_events_missing(tmp_path: Path) -> None:
    result = audit_safety_transitions(tmp_path / "no_run")
    assert result.status == AcceptanceStatus.NOT_EXECUTED
