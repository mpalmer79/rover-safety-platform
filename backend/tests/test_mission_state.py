"""Tests for the mission state machine and transition table."""

from __future__ import annotations

import pytest

from app.mission.enums import MissionState
from app.mission.transitions import (
    ALLOWED_MISSION_TRANSITIONS,
    INVALID_MISSION_TRANSITION_REASON,
    is_mission_transition_allowed,
)


def test_required_states_present() -> None:
    expected = {
        "MISSION_IDLE",
        "MISSION_PREPARING",
        "MISSION_ACTIVE",
        "MISSION_PAUSED",
        "MISSION_RECOVERY",
        "MISSION_DEGRADED",
        "MISSION_ABORTING",
        "MISSION_ABORTED",
        "MISSION_COMPLETE",
    }
    assert {s.value for s in MissionState} == expected


@pytest.mark.parametrize(
    "from_state,to_state",
    [
        (MissionState.MISSION_IDLE, MissionState.MISSION_PREPARING),
        (MissionState.MISSION_PREPARING, MissionState.MISSION_ACTIVE),
        (MissionState.MISSION_ACTIVE, MissionState.MISSION_PAUSED),
        (MissionState.MISSION_ACTIVE, MissionState.MISSION_RECOVERY),
        (MissionState.MISSION_ACTIVE, MissionState.MISSION_DEGRADED),
        (MissionState.MISSION_ACTIVE, MissionState.MISSION_ABORTING),
        (MissionState.MISSION_ACTIVE, MissionState.MISSION_COMPLETE),
        (MissionState.MISSION_RECOVERY, MissionState.MISSION_ACTIVE),
        (MissionState.MISSION_DEGRADED, MissionState.MISSION_ACTIVE),
        (MissionState.MISSION_ABORTING, MissionState.MISSION_ABORTED),
    ],
)
def test_valid_transitions(from_state: MissionState, to_state: MissionState) -> None:
    assert is_mission_transition_allowed(from_state, to_state)


@pytest.mark.parametrize(
    "from_state,to_state",
    [
        (MissionState.MISSION_ABORTED, MissionState.MISSION_ACTIVE),
        (MissionState.MISSION_COMPLETE, MissionState.MISSION_ACTIVE),
        (MissionState.MISSION_IDLE, MissionState.MISSION_ACTIVE),
        (MissionState.MISSION_RECOVERY, MissionState.MISSION_COMPLETE),
        (MissionState.MISSION_PAUSED, MissionState.MISSION_COMPLETE),
    ],
)
def test_invalid_transitions(from_state: MissionState, to_state: MissionState) -> None:
    assert not is_mission_transition_allowed(from_state, to_state)


def test_self_transition_allowed_for_all_states() -> None:
    for state in MissionState:
        assert is_mission_transition_allowed(state, state)


def test_table_keys_complete() -> None:
    assert set(ALLOWED_MISSION_TRANSITIONS.keys()) == set(MissionState)


def test_aborted_is_terminal() -> None:
    assert ALLOWED_MISSION_TRANSITIONS[MissionState.MISSION_ABORTED] == frozenset()


def test_complete_is_terminal() -> None:
    assert ALLOWED_MISSION_TRANSITIONS[MissionState.MISSION_COMPLETE] == frozenset()
