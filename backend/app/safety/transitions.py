"""Allowed safety state transitions.

The transition table mirrors docs/SAFETY_MODEL.md section 5.3. The table
is defined here so it can be queried by tests and by the supervisor
without depending on the supervisor's full evaluation logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.domain.enums import SafetyState


# Mapping: from -> set of allowed-to states.
#
# Invariant: post-E-stop reactivation must pass through SAFE_STOP after
# recovery validation. RECOVERY does not lead directly to any ACTIVE_*
# state; the only legal exit from RECOVERY is SAFE_STOP, from which the
# supervisor may then promote to ACTIVE_NORMAL once the operator has
# completed the two-step armed-reset sequence. This forces the
# reactivation path to: E_STOP_LATCHED -> RECOVERY -> SAFE_STOP ->
# ACTIVE_NORMAL, so no single operator pulse and no single
# misclassified recovery-validation can authorize motion again.
ALLOWED_TRANSITIONS: dict[SafetyState, frozenset[SafetyState]] = {
    SafetyState.BOOT: frozenset({SafetyState.INACTIVE, SafetyState.SAFE_STOP, SafetyState.E_STOP_LATCHED}),
    SafetyState.INACTIVE: frozenset(
        {
            SafetyState.ACTIVE_NORMAL,
            SafetyState.SAFE_STOP,
            SafetyState.E_STOP_LATCHED,
        }
    ),
    SafetyState.ACTIVE_NORMAL: frozenset(
        {
            SafetyState.ACTIVE_RESTRICTED,
            SafetyState.ACTIVE_DEGRADED,
            SafetyState.SAFE_STOP,
            SafetyState.E_STOP_LATCHED,
        }
    ),
    SafetyState.ACTIVE_RESTRICTED: frozenset(
        {
            SafetyState.ACTIVE_DEGRADED,
            SafetyState.SAFE_STOP,
            SafetyState.E_STOP_LATCHED,
            SafetyState.ACTIVE_NORMAL,
        }
    ),
    SafetyState.ACTIVE_DEGRADED: frozenset(
        {
            SafetyState.SAFE_STOP,
            SafetyState.E_STOP_LATCHED,
        }
    ),
    SafetyState.SAFE_STOP: frozenset(
        {
            SafetyState.RECOVERY,
            SafetyState.E_STOP_LATCHED,
            # Recovery-validated reactivation: only legal after the
            # supervisor's two-step armed-reset sequence (see
            # SafetySupervisor._propose_state).
            SafetyState.ACTIVE_NORMAL,
        }
    ),
    SafetyState.E_STOP_LATCHED: frozenset({SafetyState.RECOVERY}),
    SafetyState.RECOVERY: frozenset({SafetyState.SAFE_STOP}),
}


INVALID_TRANSITION_REASON = "invalid_transition"


def is_transition_allowed(from_state: SafetyState, to_state: SafetyState) -> bool:
    """Return ``True`` if ``from_state -> to_state`` is permitted.

    A transition to the *same* state is always allowed (it's a no-op).
    """

    if from_state == to_state:
        return True
    return to_state in ALLOWED_TRANSITIONS.get(from_state, frozenset())


@dataclass(frozen=True, slots=True)
class TransitionRequest:
    from_state: SafetyState
    to_state: SafetyState
    reason_code: str
    message: str
    correlation_id: Optional[str] = None


@dataclass(frozen=True, slots=True)
class TransitionResult:
    """Outcome of validating a transition.

    ``accepted`` is ``False`` when the transition would violate the
    state graph; the supervisor must then refuse and emit a
    ``safety_transition.refused`` event.
    """

    request: TransitionRequest
    accepted: bool
    rejection_reason: Optional[str] = None

    @classmethod
    def accept(cls, request: TransitionRequest) -> "TransitionResult":
        return cls(request=request, accepted=True)

    @classmethod
    def reject(cls, request: TransitionRequest, *, reason: str) -> "TransitionResult":
        return cls(request=request, accepted=False, rejection_reason=reason)


def validate_transition(request: TransitionRequest) -> TransitionResult:
    if is_transition_allowed(request.from_state, request.to_state):
        return TransitionResult.accept(request)
    return TransitionResult.reject(request, reason=INVALID_TRANSITION_REASON)
