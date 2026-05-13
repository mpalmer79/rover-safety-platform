"""Regression: NaN / non-finite / non-positive speed limits must be rejected (#20).

Before the fix, ``if limit > odd.speed_limit_mps`` evaluated to False
for NaN (every comparison with NaN is False), so an attacker could
slip a NaN through the ODD validator and have the downstream layers
treat it as "within the envelope".
"""

from __future__ import annotations

from app.natural_language_mission.models import (
    CONSTRAINT_SPEED_LIMIT,
    MissionConstraint,
    OperationalDesignDomain,
)
from app.natural_language_mission.validator import validate_against_odd


def _odd() -> OperationalDesignDomain:
    return OperationalDesignDomain(profile_id="test-odd", speed_limit_mps=1.5)


def _constraint(limit_str: str) -> MissionConstraint:
    return MissionConstraint(
        constraint_id="c-1",
        constraint_kind=CONSTRAINT_SPEED_LIMIT,
        label="speed",
        parameters={"limit_mps": limit_str},
        source_clause="set speed to <limit>",
    )


def test_nan_speed_limit_is_rejected() -> None:
    diags = validate_against_odd((), (_constraint("nan"),), _odd())
    assert any(d.code == "odd_violation" for d in diags), diags


def test_inf_speed_limit_is_rejected() -> None:
    diags = validate_against_odd((), (_constraint("inf"),), _odd())
    assert any(d.code == "odd_violation" for d in diags), diags


def test_negative_speed_limit_is_rejected() -> None:
    diags = validate_against_odd((), (_constraint("-1.0"),), _odd())
    assert any(d.code == "odd_violation" for d in diags), diags


def test_zero_speed_limit_is_rejected() -> None:
    diags = validate_against_odd((), (_constraint("0"),), _odd())
    assert any(d.code == "odd_violation" for d in diags), diags


def test_in_range_limit_passes() -> None:
    diags = validate_against_odd((), (_constraint("1.0"),), _odd())
    assert not any(d.code == "odd_violation" for d in diags), diags
