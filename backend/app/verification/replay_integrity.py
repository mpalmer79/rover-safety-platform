"""Phase 3 replay-integrity wrapper.

Composes the Phase 1C and Phase 2 validators
(:func:`app.validation.validate_run_directory`,
:func:`app.validation.validate_mission_run`,
:func:`app.validation.validate_events_file`) into a single
:class:`ReplayIntegrityResult` that fits the verification reporting
vocabulary (``passed`` / ``failed`` / ``partial`` / ``not_executed``).

The wrapper does not duplicate validator logic; it normalises the
status field and aggregates errors so that the scenario verifier and
report generator can treat replay integrity as a single check.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.validation.event_validator import validate_events_file
from app.validation.mission_validator import validate_mission_run
from app.validation.replay_validator import validate_run_directory
from app.verification.acceptance import AcceptanceStatus


@dataclass
class ReplayIntegrityResult:
    run_dir: Path
    status: AcceptanceStatus = AcceptanceStatus.PASSED
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    base_replay_ok: bool = True
    mission_ok: bool = True
    events_ok: bool = True
    event_count: int = 0
    transition_count: int = 0
    mission_state_count: int = 0
    waypoints_completed: tuple[str, ...] = ()
    final_mission_state: str | None = None

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
            "base_replay_ok": self.base_replay_ok,
            "mission_ok": self.mission_ok,
            "events_ok": self.events_ok,
            "event_count": self.event_count,
            "transition_count": self.transition_count,
            "mission_state_count": self.mission_state_count,
            "waypoints_completed": list(self.waypoints_completed),
            "final_mission_state": self.final_mission_state,
        }


def verify_replay_integrity(run_dir: Path | str) -> ReplayIntegrityResult:
    run_dir = Path(run_dir)
    result = ReplayIntegrityResult(run_dir=run_dir)

    if not run_dir.exists() or not run_dir.is_dir():
        result.add_error(f"run directory does not exist: {run_dir}")
        result.status = AcceptanceStatus.NOT_EXECUTED
        return result

    base = validate_run_directory(run_dir)
    result.base_replay_ok = base.ok
    result.event_count = base.event_count
    result.transition_count = base.transition_count
    if not base.ok:
        for err in base.errors:
            result.add_error(f"replay_validator: {err}")
    for warn in base.warnings:
        result.add_warning(f"replay_validator: {warn}")

    mission = validate_mission_run(run_dir)
    result.mission_ok = mission.ok
    result.mission_state_count = mission.mission_state_count
    result.waypoints_completed = mission.waypoints_completed
    result.final_mission_state = mission.final_mission_state
    if not mission.ok:
        for err in mission.errors:
            if err not in result.errors:
                result.add_error(f"mission_validator: {err}")

    events_path = run_dir / "events.jsonl"
    events_result = validate_events_file(events_path)
    result.events_ok = events_result.ok
    if not events_result.ok:
        for err in events_result.errors[:10]:
            result.add_error(f"event_validator: {err}")
        if len(events_result.errors) > 10:
            result.add_error(
                f"event_validator: ... and {len(events_result.errors) - 10} more"
            )
    return result
