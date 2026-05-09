"""Tests for the scenario verifier and related helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.verification.acceptance import AcceptanceStatus, aggregate_status
from app.verification.scenario_verifier import (
    SCENARIO_EXPECTATIONS,
    ScenarioCheck,
    ScenarioExpectation,
    verify_scenario,
)


def test_acceptance_status_aggregation_picks_worst() -> None:
    assert aggregate_status(()) == AcceptanceStatus.NOT_EXECUTED
    assert (
        aggregate_status((AcceptanceStatus.PASSED,))
        == AcceptanceStatus.PASSED
    )
    assert (
        aggregate_status((AcceptanceStatus.PASSED, AcceptanceStatus.SKIPPED))
        == AcceptanceStatus.SKIPPED
    )
    assert (
        aggregate_status((AcceptanceStatus.PASSED, AcceptanceStatus.PARTIAL))
        == AcceptanceStatus.PARTIAL
    )
    assert (
        aggregate_status(
            (AcceptanceStatus.PARTIAL, AcceptanceStatus.FAILED)
        )
        == AcceptanceStatus.FAILED
    )
    assert (
        aggregate_status((AcceptanceStatus.PASSED, AcceptanceStatus.NOT_EXECUTED))
        == AcceptanceStatus.NOT_EXECUTED
    )


def test_scenario_expectations_cover_seven_phase_1c_and_seven_phase_2() -> None:
    assert len(SCENARIO_EXPECTATIONS) == 14
    ids = {e.scenario_id for e in SCENARIO_EXPECTATIONS}
    for required in (
        "nominal_run",
        "stale_lidar_restricted_mode",
        "odometry_divergence_safe_stop",
        "command_timeout_safe_stop",
        "bridge_disconnect_safe_stop",
        "wheel_slip_degraded_mode",
        "estop_latched_manual_reset_required",
        "nominal_waypoint_patrol",
        "waypoint_timeout_recovery",
        "degraded_sensor_navigation",
        "keepout_zone_violation",
        "restricted_mode_navigation",
        "safe_stop_during_active_mission",
        "mission_abort_after_fault_escalation",
    ):
        assert required in ids, f"missing scenario {required}"


def test_skipped_scenario_returns_skipped(tmp_path: Path) -> None:
    exp = SCENARIO_EXPECTATIONS[0]
    v = verify_scenario(
        exp,
        runs_root=tmp_path,
        skip_reason="testing skip path",
    )
    assert v.status == AcceptanceStatus.SKIPPED
    assert v.run_dir is None
    assert "testing skip path" in v.not_executed_reason


def test_missing_scenario_file_returns_not_executed(tmp_path: Path) -> None:
    bogus = ScenarioExpectation(
        scenario_file="does_not_exist.json",
        requirement_ids=("REQ-SAFE-001",),
        expected_safety_state=SCENARIO_EXPECTATIONS[0].expected_safety_state,
    )
    v = verify_scenario(bogus, runs_root=tmp_path)
    assert v.status == AcceptanceStatus.NOT_EXECUTED
    assert "missing" in v.not_executed_reason.lower()


@pytest.mark.parametrize("expectation", SCENARIO_EXPECTATIONS)
def test_each_scenario_passes_verification(expectation, tmp_path: Path) -> None:
    """Drive every Phase 1C / Phase 2 scenario and assert it passes.

    This is the most important test in the verification suite. A
    failure here means a regression in the deterministic pipeline,
    the scenario expectations, or one of the audits.
    """

    v = verify_scenario(expectation, runs_root=tmp_path)
    if v.status != AcceptanceStatus.PASSED:
        failed = [c for c in v.checks if c.status == AcceptanceStatus.FAILED]
        details = "; ".join(f"{c.name}: {c.detail}" for c in failed)
        pytest.fail(
            f"{expectation.scenario_id} verification status={v.status.value}: {details}"
        )


def test_each_check_has_a_name(tmp_path: Path) -> None:
    exp = SCENARIO_EXPECTATIONS[0]
    v = verify_scenario(exp, runs_root=tmp_path)
    assert v.checks
    for c in v.checks:
        assert isinstance(c, ScenarioCheck)
        assert c.name
