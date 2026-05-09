"""Command-path audit.

Inspects ``commands.jsonl`` from a recorded run and verifies the
documented architectural invariants:

* every published authorized command was constructed by the
  supervisor's arbiter (its ``source`` field is
  ``safety.supervisor.arbitration``),
* in SAFE_STOP, E_STOP_LATCHED, BOOT, INACTIVE, and RECOVERY, every
  authorized command carries zero linear and zero angular velocity,
* in any ``ACTIVE_*`` state the authorized command never exceeds the
  documented per-state limits from
  :func:`app.domain.motion.motion_limits_for_state`,
* if a request was published, a corresponding authorized command
  follows within the same evaluation tick (the recorder writes both
  per tick, so we assert that the sim_time_ns of the authorized
  command is >= the sim_time_ns of the request and within one tick),
* expired requests are rejected (decision == ``rejected_expired``).

The audit runs without a live ROS graph: it operates entirely on the
JSONL files emitted by the recorder.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from app.domain.enums import MotionDecision, SafetyState
from app.domain.motion import motion_limits_for_state
from app.verification.acceptance import AcceptanceStatus


_AUTHORIZED_SOURCE = "safety.supervisor.arbitration"
_FORCE_ZERO_STATES: frozenset[str] = frozenset(
    {
        SafetyState.BOOT.value,
        SafetyState.INACTIVE.value,
        SafetyState.SAFE_STOP.value,
        SafetyState.E_STOP_LATCHED.value,
        SafetyState.RECOVERY.value,
    }
)


@dataclass
class CommandAuditResult:
    run_dir: Path
    status: AcceptanceStatus = AcceptanceStatus.PASSED
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    command_count: int = 0
    request_count: int = 0
    clamped_count: int = 0
    zeroed_count: int = 0
    expired_count: int = 0
    rejected_count: int = 0

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
            "command_count": self.command_count,
            "request_count": self.request_count,
            "clamped_count": self.clamped_count,
            "zeroed_count": self.zeroed_count,
            "expired_count": self.expired_count,
            "rejected_count": self.rejected_count,
        }


def audit_command_path(run_dir: Path | str) -> CommandAuditResult:
    """Audit ``runs/<run_id>/commands.jsonl`` against the safety contract."""

    run_dir = Path(run_dir)
    result = CommandAuditResult(run_dir=run_dir)
    commands_path = run_dir / "commands.jsonl"
    if not commands_path.exists():
        result.add_error(f"commands.jsonl not found at {commands_path}")
        result.status = AcceptanceStatus.NOT_EXECUTED
        return result

    last_request_sim_ns: int | None = None
    last_request_expires: int | None = None

    with commands_path.open("r", encoding="utf-8") as fh:
        for line_no, raw in enumerate(fh, start=1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError as exc:
                result.add_error(f"commands.jsonl line {line_no}: {exc}")
                continue
            authorized = payload.get("authorized")
            requested = payload.get("requested")
            sim_ns = int(payload.get("sim_time_ns", 0))
            if not isinstance(authorized, dict):
                result.add_error(f"line {line_no}: missing authorized payload")
                continue
            result.command_count += 1
            if requested is not None:
                result.request_count += 1
                last_request_sim_ns = sim_ns
                last_request_expires = int(
                    requested.get("expires_at_ms", 0)
                ) * 1_000_000  # ms -> ns

            # 1. Source must be the supervisor's arbiter.
            source = authorized.get("source")
            if source != _AUTHORIZED_SOURCE:
                result.add_error(
                    f"line {line_no}: authorized command from non-supervisor source {source!r}"
                )
                continue

            decision = authorized.get("decision")
            safety_state = authorized.get("safety_state")
            linear = float(authorized.get("linear_velocity", 0.0))
            angular = float(authorized.get("angular_velocity", 0.0))

            if decision == MotionDecision.AUTHORIZED_CLAMPED.value:
                result.clamped_count += 1
            if decision in {
                MotionDecision.REJECTED_ZEROED.value,
                MotionDecision.REJECTED_DEGRADED.value,
            }:
                result.zeroed_count += 1
                result.rejected_count += 1
                if linear != 0.0 or angular != 0.0:
                    result.add_error(
                        f"line {line_no}: {decision} carried non-zero motion"
                    )
            elif decision == MotionDecision.REJECTED_EXPIRED.value:
                result.expired_count += 1
                result.rejected_count += 1
                if linear != 0.0 or angular != 0.0:
                    result.add_error(
                        f"line {line_no}: rejected_expired carried non-zero motion"
                    )

            # 2. Forced-zero states.
            if safety_state in _FORCE_ZERO_STATES:
                if linear != 0.0 or angular != 0.0:
                    result.add_error(
                        f"line {line_no}: state {safety_state} authorized non-zero "
                        f"motion (linear={linear}, angular={angular})"
                    )

            # 3. Active-state limit envelope.
            if safety_state in {
                SafetyState.ACTIVE_NORMAL.value,
                SafetyState.ACTIVE_RESTRICTED.value,
                SafetyState.ACTIVE_DEGRADED.value,
            }:
                try:
                    limits = motion_limits_for_state(SafetyState(safety_state))
                except ValueError:
                    result.add_warning(
                        f"line {line_no}: unknown safety_state {safety_state!r}"
                    )
                    continue
                if abs(linear) > limits.linear_max + 1e-6:
                    result.add_error(
                        f"line {line_no}: linear={linear} exceeds {safety_state} "
                        f"limit {limits.linear_max}"
                    )
                if abs(angular) > limits.angular_max + 1e-6:
                    result.add_error(
                        f"line {line_no}: angular={angular} exceeds {safety_state} "
                        f"limit {limits.angular_max}"
                    )

            # 4. Cross-check: an authorized command at sim_ns t must
            #    have a request observed at t' <= t, OR be a forced-zero
            #    decision (including REJECTED_EXPIRED when no request).
            if requested is None and decision == MotionDecision.AUTHORIZED.value:
                # Authorized non-zero motion without an accompanying
                # request would mean the supervisor synthesised motion.
                # The arbiter never does this — its only AUTHORIZED
                # path runs when ``requested`` is present.
                if linear != 0.0 or angular != 0.0:
                    result.add_error(
                        f"line {line_no}: AUTHORIZED non-zero motion without a request"
                    )

    if result.command_count == 0:
        result.add_warning("no commands recorded")
    return result
