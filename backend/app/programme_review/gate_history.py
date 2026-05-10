"""CI gate history aggregator.

Walks reliability-impact bundles in chronological order, counts
pass / warning / failure / not_executed gates, computes a
volatility label, and identifies the most recent transition. The
module never fabricates durations when timestamps are absent.
"""

from __future__ import annotations

from typing import Iterable, Optional

from app.programme_review.models import (
    GateHistoryReport,
    GateVolatility,
    HistoryRecord,
    LoadedHistory,
)


def build_gate_history(history: LoadedHistory) -> GateHistoryReport:
    if not history.reliability_impact:
        return GateHistoryReport(
            pass_count=0,
            warning_count=0,
            failure_count=0,
            not_executed_count=0,
            last_status="unknown",
            last_transition=None,
            volatility=GateVolatility.UNKNOWN,
            sequence=(),
            notes=("no reliability-impact bundles in history",),
        )

    sequence: list[str] = []
    for record in history.reliability_impact:
        status = (
            record.payload.get("gate_decision", {}).get("status") or "unknown"
        )
        sequence.append(str(status))

    pass_count = sequence.count("passed")
    warning_count = sequence.count("warning")
    failure_count = sequence.count("failed")
    not_executed_count = sum(
        1 for s in sequence if s in {"not_executed", "unknown"}
    )
    last_status = sequence[-1]
    last_transition = _last_transition(sequence)
    volatility = _classify_volatility(sequence)
    notes: tuple[str, ...] = ()
    if len(sequence) < 2:
        notes = ("only one gate decision available; volatility is informational",)
    return GateHistoryReport(
        pass_count=pass_count,
        warning_count=warning_count,
        failure_count=failure_count,
        not_executed_count=not_executed_count,
        last_status=last_status,
        last_transition=last_transition,
        volatility=volatility,
        sequence=tuple(sequence),
        notes=notes,
    )


def _last_transition(sequence: list[str]) -> Optional[str]:
    for idx in range(len(sequence) - 1, 0, -1):
        if sequence[idx] != sequence[idx - 1]:
            return f"{sequence[idx - 1]} -> {sequence[idx]}"
    return None


def _classify_volatility(sequence: list[str]) -> GateVolatility:
    if len(sequence) < 2:
        return GateVolatility.UNKNOWN
    transitions = sum(
        1 for i in range(1, len(sequence)) if sequence[i] != sequence[i - 1]
    )
    rank = {"failed": -1, "warning": 0, "passed": 1, "unknown": 0, "not_executed": 0}
    first = rank.get(sequence[0], 0)
    last = rank.get(sequence[-1], 0)
    if transitions == 0:
        return GateVolatility.STEADY
    if last > first:
        return GateVolatility.IMPROVING
    if last < first:
        return GateVolatility.REGRESSING
    return GateVolatility.OSCILLATING
