"""run_id validation helpers (#19).

Lives in its own module so it can be unit-tested without rclpy. The
event_recorder node imports the symbols here.

The policy is documented in ``backend/app/api/routes/runs.py`` — the
same charset / length rule is used everywhere so the recorder and the
HTTP gateway cannot disagree about what a valid run_id looks like.
"""

from __future__ import annotations

import re
from pathlib import Path


_RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,128}$")


class InvalidRunIdError(ValueError):
    """Raised when ``run_id`` does not match the charset / length policy."""


def validated_run_id(run_id: str) -> str:
    if not isinstance(run_id, str) or not _RUN_ID_PATTERN.fullmatch(run_id):
        raise InvalidRunIdError(
            f"run_id must match {_RUN_ID_PATTERN.pattern!r}; got {run_id!r}"
        )
    return run_id


def validated_run_dir(runs_root: Path, run_id: str) -> Path:
    """Join + resolve; assert the result stays under ``runs_root``."""

    runs_root_resolved = runs_root.resolve()
    run_dir = runs_root / run_id
    run_dir_resolved = run_dir.resolve()
    if not run_dir_resolved.is_relative_to(runs_root_resolved):
        raise InvalidRunIdError(
            f"resolved run_dir {run_dir_resolved} escapes runs_root {runs_root_resolved}"
        )
    return run_dir


__all__ = [
    "InvalidRunIdError",
    "validated_run_id",
    "validated_run_dir",
]
