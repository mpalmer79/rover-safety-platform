"""Lifecycle transition rules for artefacts.

Lifecycle ladder (top = most authoritative):

```
canonical
  ↑
verified
  ↑
committed
  ↑
hydrated
  ↑
generated
```

``deprecated`` is a side-state reachable from any rung; once an
artefact is deprecated it should not be referenced by the frontend.

The rules below are deliberately loose — the Phase 18 layer is
descriptive, not enforcing. The CI honesty greps + the validator
catch violations; the lifecycle helpers exist so tests + the
reporter can answer "is this artefact authoritative right now?".
"""

from __future__ import annotations

from .models import (
    INTEGRITY_PASSED,
    LIFECYCLE_CANONICAL,
    LIFECYCLE_COMMITTED,
    LIFECYCLE_DEPRECATED,
    LIFECYCLE_GENERATED,
    LIFECYCLE_HYDRATED,
    LIFECYCLE_STATES,
    LIFECYCLE_VERIFIED,
)


_ORDER: dict[str, int] = {
    LIFECYCLE_GENERATED: 0,
    LIFECYCLE_HYDRATED: 1,
    LIFECYCLE_COMMITTED: 2,
    LIFECYCLE_VERIFIED: 3,
    LIFECYCLE_CANONICAL: 4,
    LIFECYCLE_DEPRECATED: -1,
}


def is_authoritative(lifecycle: str) -> bool:
    """Return True if the lifecycle rung is renderable in the UI."""

    return lifecycle in {LIFECYCLE_COMMITTED, LIFECYCLE_VERIFIED, LIFECYCLE_CANONICAL}


def is_deprecated(lifecycle: str) -> bool:
    return lifecycle == LIFECYCLE_DEPRECATED


def can_promote(current: str, target: str) -> bool:
    """Return True iff a promotion from ``current`` to ``target`` is allowed.

    Promotions only move *up* the ladder; deprecation may always be
    set; downward demotions are forbidden via this helper (a caller
    that needs to demote should set ``deprecated`` instead).
    """

    if current not in LIFECYCLE_STATES or target not in LIFECYCLE_STATES:
        return False
    if target == LIFECYCLE_DEPRECATED:
        return True
    return _ORDER[target] > _ORDER[current]


def lifecycle_for_integrity(integrity: str, lifecycle: str) -> str:
    """Return the most-authoritative lifecycle ``lifecycle`` may claim.

    A committed-but-not-verified artefact stays at ``committed`` even
    if the registry already lists it as ``verified``. The function is
    used by the reporter to clamp claims when integrity drops.
    """

    if integrity != INTEGRITY_PASSED and lifecycle in {
        LIFECYCLE_VERIFIED,
        LIFECYCLE_CANONICAL,
    }:
        return LIFECYCLE_COMMITTED
    return lifecycle


__all__ = [
    "can_promote",
    "is_authoritative",
    "is_deprecated",
    "lifecycle_for_integrity",
]
