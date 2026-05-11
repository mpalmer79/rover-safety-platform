"""Live runtime maturity baseline.

The baseline records whether a bag-backed live run has ever been
captured against this repository. It exists so a reviewer can tell
"this project has produced real runtime evidence" from "this project
has the scaffolding but no real run yet" without trawling through
artefacts.

The honest default is ``not_established`` until a bag-backed
:class:`LiveRuntimeEvidence` record exists.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class MaturityStatus(str, Enum):
    NOT_ESTABLISHED = "not_established"
    ESTABLISHED = "established"


@dataclass(frozen=True)
class MaturityBaseline:
    status: MaturityStatus
    reason: str
    bag_backed_runs: int
    last_run_id: Optional[str] = None
    last_run_at: Optional[str] = None
    last_runner_id: Optional[str] = None
    last_bag_dir: Optional[str] = None
    last_scenario_plan_id: Optional[str] = None
    notes: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "status": self.status.value,
            "reason": self.reason,
            "bag_backed_runs": self.bag_backed_runs,
            "last_run_id": self.last_run_id,
            "last_run_at": self.last_run_at,
            "last_runner_id": self.last_runner_id,
            "last_bag_dir": self.last_bag_dir,
            "last_scenario_plan_id": self.last_scenario_plan_id,
            "notes": list(self.notes),
        }


def new_not_established_baseline(
    *,
    reason: str = "no bag-backed live run has been captured",
) -> MaturityBaseline:
    return MaturityBaseline(
        status=MaturityStatus.NOT_ESTABLISHED,
        reason=reason,
        bag_backed_runs=0,
        notes=(
            "the platform must remain at not_established until a real "
            "bag-backed run is observed; do not pin a fake baseline.",
        ),
    )


def parse_maturity_baseline(data: dict) -> MaturityBaseline:
    if not isinstance(data, dict):
        raise ValueError("maturity baseline must be a JSON object")
    try:
        status = MaturityStatus(data.get("status", "not_established"))
    except ValueError as exc:
        raise ValueError(f"invalid maturity status: {exc}") from exc
    notes = data.get("notes") or ()
    if isinstance(notes, str):
        notes_tuple: tuple[str, ...] = (notes,)
    else:
        notes_tuple = tuple(str(n) for n in notes)
    return MaturityBaseline(
        status=status,
        reason=str(data.get("reason", "")),
        bag_backed_runs=int(data.get("bag_backed_runs", 0) or 0),
        last_run_id=data.get("last_run_id"),
        last_run_at=data.get("last_run_at"),
        last_runner_id=data.get("last_runner_id"),
        last_bag_dir=data.get("last_bag_dir"),
        last_scenario_plan_id=data.get("last_scenario_plan_id"),
        notes=notes_tuple,
    )


def load_maturity_baseline(path: Path) -> MaturityBaseline:
    return parse_maturity_baseline(json.loads(Path(path).read_text(encoding="utf-8")))


def assert_baseline_honest(
    baseline: MaturityBaseline,
    *,
    has_bag_backed_evidence: bool,
) -> list[str]:
    """Return errors if the baseline overclaims maturity."""

    errors: list[str] = []
    if baseline.status is MaturityStatus.ESTABLISHED:
        if not has_bag_backed_evidence:
            errors.append(
                "maturity baseline claims 'established' but no bag-backed "
                "evidence was supplied"
            )
        if baseline.bag_backed_runs <= 0:
            errors.append(
                "maturity baseline claims 'established' but bag_backed_runs == 0"
            )
        if not baseline.last_run_id:
            errors.append(
                "maturity baseline claims 'established' but last_run_id is empty"
            )
    if baseline.status is MaturityStatus.NOT_ESTABLISHED:
        if baseline.bag_backed_runs > 0:
            errors.append(
                "maturity baseline status='not_established' is inconsistent "
                "with bag_backed_runs > 0"
            )
    if baseline.last_run_at:
        try:
            datetime.fromisoformat(str(baseline.last_run_at).replace("Z", "+00:00"))
        except ValueError:
            errors.append(
                f"last_run_at must be ISO-8601, got {baseline.last_run_at!r}"
            )
    return errors


def promote_baseline(
    previous: MaturityBaseline,
    *,
    run_id: str,
    bag_dir: Optional[str],
    runner_id: Optional[str],
    scenario_plan_id: Optional[str],
    captured_at: Optional[str] = None,
) -> MaturityBaseline:
    """Construct a new baseline reflecting an additional bag-backed run.

    The caller is responsible for confirming the run is genuinely
    bag-backed (e.g. via :func:`process_evidence`); this helper does
    not re-validate.
    """

    timestamp = captured_at or datetime.now(timezone.utc).replace(
        microsecond=0
    ).isoformat()
    return MaturityBaseline(
        status=MaturityStatus.ESTABLISHED,
        reason="bag-backed live run observed",
        bag_backed_runs=previous.bag_backed_runs + 1,
        last_run_id=run_id,
        last_run_at=timestamp,
        last_runner_id=runner_id,
        last_bag_dir=bag_dir,
        last_scenario_plan_id=scenario_plan_id,
        notes=previous.notes,
    )
