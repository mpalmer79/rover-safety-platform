"""Verification acceptance status vocabulary.

The verification layer reports five distinct outcomes. They are
chosen to make honest reporting easy and auditing tractable:

* ``passed`` — every check in scope held.
* ``failed`` — at least one check explicitly failed.
* ``partial`` — some checks held, some are not yet implemented or
  not yet evaluable from the available artefacts. The verifier
  produces a partial result rather than a fake pass.
* ``skipped`` — the check / scenario was deliberately bypassed
  (e.g. operator request, environment lacking a dependency).
* ``not_executed`` — the check / scenario could not run in the
  current environment (e.g. requires Gazebo on a Jazzy host). The
  reporter must include a reason.

The ``aggregate_status`` helper combines a list of statuses into a
single overall status for a scenario or report. The aggregation rule
is conservative: any failure dominates, then partial, then
not_executed, then skipped, then passed.
"""

from __future__ import annotations

from enum import Enum
from typing import Iterable


class AcceptanceStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    PARTIAL = "partial"
    SKIPPED = "skipped"
    NOT_EXECUTED = "not_executed"


_SEVERITY: dict[AcceptanceStatus, int] = {
    AcceptanceStatus.PASSED: 0,
    AcceptanceStatus.SKIPPED: 1,
    AcceptanceStatus.NOT_EXECUTED: 2,
    AcceptanceStatus.PARTIAL: 3,
    AcceptanceStatus.FAILED: 4,
}


def aggregate_status(statuses: Iterable[AcceptanceStatus]) -> AcceptanceStatus:
    """Combine many checks into one status.

    The dominant status is the highest-severity status in the input.
    An empty input returns :attr:`AcceptanceStatus.NOT_EXECUTED` so
    "no checks ran" is never misread as "all checks passed".
    """

    statuses = tuple(statuses)
    if not statuses:
        return AcceptanceStatus.NOT_EXECUTED
    return max(statuses, key=lambda s: _SEVERITY[s])
