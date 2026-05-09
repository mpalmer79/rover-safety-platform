"""Tests for the safety state machine."""

from __future__ import annotations

import pytest

from app.domain.enums import SafetyState
from app.safety.transitions import (
    ALLOWED_TRANSITIONS,
    INVALID_TRANSITION_REASON,
    TransitionRequest,
    is_transition_allowed,
    validate_transition,
)


def test_all_state_values() -> None:
    expected = {
        "BOOT",
        "INACTIVE",
        "ACTIVE_NORMAL",
        "ACTIVE_RESTRICTED",
        "ACTIVE_DEGRADED",
        "SAFE_STOP",
        "E_STOP_LATCHED",
        "RECOVERY",
    }
    assert {s.value for s in SafetyState} == expected


@pytest.mark.parametrize(
    "from_state,to_state",
    [
        (SafetyState.BOOT, SafetyState.INACTIVE),
        (SafetyState.INACTIVE, SafetyState.ACTIVE_NORMAL),
        (SafetyState.ACTIVE_NORMAL, SafetyState.ACTIVE_RESTRICTED),
        (SafetyState.ACTIVE_NORMAL, SafetyState.ACTIVE_DEGRADED),
        (SafetyState.ACTIVE_RESTRICTED, SafetyState.ACTIVE_DEGRADED),
        (SafetyState.ACTIVE_DEGRADED, SafetyState.SAFE_STOP),
        (SafetyState.ACTIVE_NORMAL, SafetyState.SAFE_STOP),
        (SafetyState.ACTIVE_RESTRICTED, SafetyState.SAFE_STOP),
        (SafetyState.SAFE_STOP, SafetyState.RECOVERY),
        (SafetyState.RECOVERY, SafetyState.ACTIVE_NORMAL),
        (SafetyState.RECOVERY, SafetyState.ACTIVE_RESTRICTED),
        (SafetyState.RECOVERY, SafetyState.ACTIVE_DEGRADED),
    ],
)
def test_valid_transitions(from_state: SafetyState, to_state: SafetyState) -> None:
    assert is_transition_allowed(from_state, to_state)


@pytest.mark.parametrize(
    "from_state",
    [
        SafetyState.ACTIVE_NORMAL,
        SafetyState.ACTIVE_RESTRICTED,
        SafetyState.ACTIVE_DEGRADED,
        SafetyState.SAFE_STOP,
        SafetyState.INACTIVE,
        SafetyState.BOOT,
    ],
)
def test_any_to_estop_latched_is_allowed(from_state: SafetyState) -> None:
    assert is_transition_allowed(from_state, SafetyState.E_STOP_LATCHED)


def test_estop_latched_only_to_recovery() -> None:
    for s in SafetyState:
        if s in {SafetyState.E_STOP_LATCHED, SafetyState.RECOVERY}:
            continue
        assert not is_transition_allowed(SafetyState.E_STOP_LATCHED, s)


def test_safe_stop_does_not_self_clear_to_active() -> None:
    for s in (SafetyState.ACTIVE_NORMAL, SafetyState.ACTIVE_RESTRICTED, SafetyState.ACTIVE_DEGRADED):
        assert not is_transition_allowed(SafetyState.SAFE_STOP, s)


def test_self_transition_allowed() -> None:
    for s in SafetyState:
        assert is_transition_allowed(s, s)


def test_validate_transition_rejects_unknown() -> None:
    req = TransitionRequest(
        from_state=SafetyState.SAFE_STOP,
        to_state=SafetyState.ACTIVE_NORMAL,
        reason_code="bogus",
        message="not allowed",
    )
    result = validate_transition(req)
    assert not result.accepted
    assert result.rejection_reason == INVALID_TRANSITION_REASON


def test_validate_transition_accepts_legal() -> None:
    req = TransitionRequest(
        from_state=SafetyState.SAFE_STOP,
        to_state=SafetyState.RECOVERY,
        reason_code="operator_recovery",
        message="recovery",
    )
    result = validate_transition(req)
    assert result.accepted


def test_allowed_transitions_table_keys_complete() -> None:
    assert set(ALLOWED_TRANSITIONS.keys()) == set(SafetyState)
