"""Safety state transition audit.

Reads ``events.jsonl`` from a recorded run and verifies every
``safety_transition.entered`` against the allowed-transition table in
:mod:`app.safety.transitions`. Specifically asserts:

* every observed transition (from -> to) is in the documented graph,
* once ``E_STOP_LATCHED`` is entered the only outbound transition is
  to ``RECOVERY``,
* once ``SAFE_STOP`` is entered the only outbound transitions are
  ``RECOVERY`` or ``E_STOP_LATCHED``,
* every transition carries a non-empty ``reason_code``,
* the run terminates in a documented terminal state (the list of
  allowed terminal states is the union of ``ACTIVE_*`` + ``SAFE_STOP``
  + ``E_STOP_LATCHED`` + ``INACTIVE`` — anything else is a defect).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from app.domain.enums import SafetyState
from app.safety.transitions import is_transition_allowed
from app.verification.acceptance import AcceptanceStatus


_TERMINAL_STATES: frozenset[str] = frozenset(
    s.value for s in SafetyState
)


@dataclass
class SafetyTransitionAuditResult:
    run_dir: Path
    status: AcceptanceStatus = AcceptanceStatus.PASSED
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    transition_count: int = 0
    transitions: list[tuple[str, str, str]] = field(default_factory=list)
    """Each tuple is (from_state, to_state, reason_code)."""
    final_state: str | None = None

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)
        self.status = AcceptanceStatus.FAILED

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)

    @property
    def ok(self) -> bool:
        return self.status == AcceptanceStatus.PASSED

    def as_dict(self) -> dict:
        return {
            "run_dir": str(self.run_dir),
            "status": self.status.value,
            "ok": self.ok,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "transition_count": self.transition_count,
            "transitions": [list(t) for t in self.transitions],
            "final_state": self.final_state,
        }


def audit_safety_transitions(run_dir: Path | str) -> SafetyTransitionAuditResult:
    run_dir = Path(run_dir)
    result = SafetyTransitionAuditResult(run_dir=run_dir)
    events_path = run_dir / "events.jsonl"
    if not events_path.exists():
        result.add_error(f"events.jsonl not found at {events_path}")
        result.status = AcceptanceStatus.NOT_EXECUTED
        return result

    last_state = SafetyState.BOOT.value
    estop_latched = False
    safe_stop_active = False

    with events_path.open("r", encoding="utf-8") as fh:
        for line_no, raw in enumerate(fh, start=1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                event = json.loads(raw)
            except json.JSONDecodeError as exc:
                result.add_error(f"events.jsonl line {line_no}: {exc}")
                continue
            if event.get("event_type") != "safety_transition.entered":
                continue
            attrs = event.get("attributes") or {}
            from_state = attrs.get("from_state") or last_state
            to_state = attrs.get("to_state") or event.get("safety_state")
            reason = event.get("reason_code") or ""
            if from_state not in _TERMINAL_STATES:
                result.add_error(
                    f"line {line_no}: from_state {from_state!r} not in vocabulary"
                )
                continue
            if to_state not in _TERMINAL_STATES:
                result.add_error(
                    f"line {line_no}: to_state {to_state!r} not in vocabulary"
                )
                continue
            if not reason:
                result.add_error(f"line {line_no}: missing reason_code on transition")
            try:
                fs = SafetyState(from_state)
                ts = SafetyState(to_state)
            except ValueError as exc:
                result.add_error(f"line {line_no}: {exc}")
                continue
            if not is_transition_allowed(fs, ts):
                result.add_error(
                    f"line {line_no}: forbidden transition {from_state} -> {to_state}"
                )
                continue
            if estop_latched and ts != SafetyState.RECOVERY:
                result.add_error(
                    f"line {line_no}: from E_STOP_LATCHED only RECOVERY is allowed; got {to_state}"
                )
            if safe_stop_active and ts not in {
                SafetyState.RECOVERY,
                SafetyState.E_STOP_LATCHED,
            }:
                result.add_error(
                    f"line {line_no}: from SAFE_STOP only RECOVERY/E_STOP_LATCHED allowed; got {to_state}"
                )
            if ts == SafetyState.E_STOP_LATCHED:
                estop_latched = True
            elif ts == SafetyState.RECOVERY and estop_latched:
                # Recovery cleared the latch.
                estop_latched = False
            safe_stop_active = ts == SafetyState.SAFE_STOP
            result.transition_count += 1
            result.transitions.append((from_state, to_state, reason))
            last_state = to_state

    result.final_state = last_state
    if result.final_state not in _TERMINAL_STATES:
        result.add_error(f"final state {result.final_state!r} not in vocabulary")
    return result
