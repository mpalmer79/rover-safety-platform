"""Regression: event_recorder rejects malformed run_id (#19).

The validation helpers are unit-testable without rclpy because the
regex + ``Path.resolve`` check is plain stdlib. We import them
directly and exercise the rejection contract.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


_PKG_ROOT = Path(__file__).resolve().parents[1] / "src" / "rover_observability"
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))

from rover_observability.run_id_validation import (  # noqa: E402
    InvalidRunIdError,
    validated_run_dir as _validated_run_dir,
    validated_run_id as _validated_run_id,
)


@pytest.mark.parametrize(
    "bad",
    [
        "..",
        "../etc",
        "foo/bar",
        "/abs",
        "name with space",
        "name;rm",
        "x" * 129,
        "",
        "name#frag",
    ],
)
def test_bad_run_id_is_rejected(bad: str) -> None:
    with pytest.raises(InvalidRunIdError):
        _validated_run_id(bad)


@pytest.mark.parametrize(
    "good",
    ["run-1", "abc_123", "ABCabc", "x", "a" * 128, "1234"],
)
def test_good_run_id_is_accepted(good: str) -> None:
    assert _validated_run_id(good) == good


def test_run_dir_must_stay_under_runs_root(tmp_path: Path) -> None:
    runs_root = tmp_path / "runs"
    runs_root.mkdir()
    other_root = tmp_path / "elsewhere"
    other_root.mkdir()
    # Symlink an "innocent" run_id into a directory outside runs_root.
    target = other_root / "victim"
    target.mkdir()
    (runs_root / "innocent").symlink_to(target)

    with pytest.raises(InvalidRunIdError):
        _validated_run_dir(runs_root, "innocent")


def test_run_dir_resolves_normally(tmp_path: Path) -> None:
    runs_root = tmp_path / "runs"
    runs_root.mkdir()
    out = _validated_run_dir(runs_root, "abc_123")
    assert out == runs_root / "abc_123"
