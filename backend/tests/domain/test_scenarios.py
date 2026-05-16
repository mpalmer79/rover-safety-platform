"""Bound-violation tests for :class:`ScenarioDefinition`.

These tests pin the resource bounds enforced in ``__post_init__``: a
scenario payload posted to ``/simulation/run`` cannot configure the
simulator into a denial-of-service shape.
"""

from __future__ import annotations

import pytest

from app.domain.identifiers import ScenarioId
from app.domain.scenarios import (
    ScenarioDefinition,
    ScenarioFault,
)


def _good() -> ScenarioDefinition:
    return ScenarioDefinition(
        scenario_id=ScenarioId("s-ok"),
        duration_seconds=1.0,
        time_step_ms=100,
    )


def test_baseline_is_accepted() -> None:
    _good()


def test_duration_seconds_must_be_positive() -> None:
    with pytest.raises(ValueError):
        ScenarioDefinition(scenario_id=ScenarioId("s"), duration_seconds=0)


def test_duration_seconds_upper_bound() -> None:
    with pytest.raises(ValueError):
        ScenarioDefinition(
            scenario_id=ScenarioId("s"),
            duration_seconds=ScenarioDefinition.MAX_DURATION_SECONDS + 1.0,
        )


def test_time_step_ms_lower_bound() -> None:
    with pytest.raises(ValueError):
        ScenarioDefinition(
            scenario_id=ScenarioId("s"),
            duration_seconds=1.0,
            time_step_ms=0,
        )


def test_total_steps_upper_bound() -> None:
    # duration=3600s, time_step=1ms => 3_600_000 steps > 1_000_000
    with pytest.raises(ValueError):
        ScenarioDefinition(
            scenario_id=ScenarioId("s"),
            duration_seconds=3600.0,
            time_step_ms=1,
        )


def test_faults_count_upper_bound() -> None:
    too_many = tuple(
        ScenarioFault(
            fault_id=f"f-{i}",
            fault_type="sensor_dropout",
            target="lidar",
            activation_ms=10,
        )
        for i in range(ScenarioDefinition.MAX_FAULTS + 1)
    )
    with pytest.raises(ValueError):
        ScenarioDefinition(
            scenario_id=ScenarioId("s"),
            duration_seconds=1.0,
            faults=too_many,
        )


def test_from_dict_rejects_oversized_duration() -> None:
    with pytest.raises(ValueError):
        ScenarioDefinition.from_dict(
            {"scenario_id": "s", "duration_seconds": 9999.0}
        )
