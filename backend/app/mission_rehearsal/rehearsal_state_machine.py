"""Explicit rehearsal state machine.

The rehearsal pipeline progresses through a small, bounded set of
states. Illegal transitions raise :class:`StateMachineError`; the
runtime treats every legal transition as an audit event.

```
   created
     │
     ▼ validation passes
   validated ─────────── rejected (validator)
     │
     ▼ supervisor approves
   approved ──────────── rejected (supervisor)
     │
     ▼ runtime starts
   rehearsing ── paused ─┬── aborted (safety escalation)
     │                   │
     ▼                   ▼
   completed         rejected
```
"""

from __future__ import annotations

from .models import RehearsalStatus


class StateMachineError(RuntimeError):
    pass


# Allowed transitions, keyed by source state.
REHEARSAL_TRANSITIONS: dict[str, frozenset[str]] = {
    RehearsalStatus.CREATED.value: frozenset(
        {RehearsalStatus.VALIDATED.value, RehearsalStatus.REJECTED.value}
    ),
    RehearsalStatus.VALIDATED.value: frozenset(
        {RehearsalStatus.APPROVED.value, RehearsalStatus.REJECTED.value}
    ),
    RehearsalStatus.APPROVED.value: frozenset(
        {RehearsalStatus.REHEARSING.value, RehearsalStatus.REJECTED.value}
    ),
    RehearsalStatus.REHEARSING.value: frozenset(
        {
            RehearsalStatus.PAUSED.value,
            RehearsalStatus.COMPLETED.value,
            RehearsalStatus.ABORTED.value,
            RehearsalStatus.REJECTED.value,
        }
    ),
    RehearsalStatus.PAUSED.value: frozenset(
        {
            RehearsalStatus.REHEARSING.value,
            RehearsalStatus.ABORTED.value,
            RehearsalStatus.COMPLETED.value,
            RehearsalStatus.REJECTED.value,
        }
    ),
    # Terminal states: no further transitions.
    RehearsalStatus.REJECTED.value: frozenset(),
    RehearsalStatus.ABORTED.value: frozenset(),
    RehearsalStatus.COMPLETED.value: frozenset(),
}


def valid_transitions(state: str) -> frozenset[str]:
    if state not in REHEARSAL_TRANSITIONS:
        raise StateMachineError(f"unknown rehearsal state: {state!r}")
    return REHEARSAL_TRANSITIONS[state]


def next_status(current: str, requested: str) -> str:
    """Return ``requested`` if the transition is legal, else raise."""

    allowed = valid_transitions(current)
    if requested not in allowed:
        raise StateMachineError(
            f"illegal rehearsal transition {current!r} → {requested!r}; "
            f"allowed: {sorted(allowed)}"
        )
    return requested
