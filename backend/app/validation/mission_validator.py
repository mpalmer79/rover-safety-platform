"""Mission-aware run-directory validation.

Builds on :func:`validate_run_directory` and adds mission-specific
checks:

* ``mission_state_transitions.jsonl`` exists and parses,
* every transition uses the controlled vocabulary defined in
  :mod:`app.mission.enums`,
* per-producer ordering is preserved,
* ``waypoint_events.jsonl`` and ``recovery_events.jsonl`` parse,
* ``world_model_snapshots.jsonl`` parses and every snapshot has the
  required keys.

The validator runs in CI (no ROS dependencies) and is wrapped by the
``tools/validate_mission_run.py`` CLI.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from app.mission.enums import (
    MissionState,
    RecoveryBehavior,
    WaypointStatus as WaypointStatusEnum,
)
from app.validation.replay_validator import (
    ReplayValidationResult,
    validate_run_directory,
)


_MISSION_STATE_VALUES = {s.value for s in MissionState}
_RECOVERY_BEHAVIOR_VALUES = {b.value for b in RecoveryBehavior}
_WAYPOINT_STATUS_VALUES = {s.value for s in WaypointStatusEnum}

_REQUIRED_SNAPSHOT_KEYS = (
    "sim_time_ns",
    "pose_x",
    "pose_y",
    "heading_rad",
    "occupancy_min_range_m",
    "occupancy_mean_range_m",
    "forward_sector_clear",
    "forward_clearance_m",
    "inside_keepout",
    "near_keepout",
    "inside_restricted",
    "boundary_violations",
)


@dataclass
class MissionRunValidationResult:
    run_dir: Path
    ok: bool
    base_replay: ReplayValidationResult
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    mission_state_count: int = 0
    waypoint_event_count: int = 0
    recovery_event_count: int = 0
    world_model_snapshot_count: int = 0
    final_mission_state: str | None = None
    waypoints_completed: tuple[str, ...] = ()
    waypoints_timed_out: tuple[str, ...] = ()
    recovery_behaviors_seen: tuple[str, ...] = ()

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)
        self.ok = False

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)

    def as_dict(self) -> dict:
        return {
            "run_dir": str(self.run_dir),
            "ok": self.ok,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "base_replay": self.base_replay.as_dict(),
            "mission_state_count": self.mission_state_count,
            "waypoint_event_count": self.waypoint_event_count,
            "recovery_event_count": self.recovery_event_count,
            "world_model_snapshot_count": self.world_model_snapshot_count,
            "final_mission_state": self.final_mission_state,
            "waypoints_completed": list(self.waypoints_completed),
            "waypoints_timed_out": list(self.waypoints_timed_out),
            "recovery_behaviors_seen": list(self.recovery_behaviors_seen),
        }


@dataclass(frozen=True, slots=True)
class WaypointBounds:
    """Operational extents for waypoint-coordinate validation (#21).

    Sourced from :class:`app.domain.scenarios.ScenarioDefinition`. When
    a scenario does not declare extents, the validator falls back to a
    sanity range of +/-10_000 meters and emits a warning.
    """

    min_pose_x: float = -10_000.0
    max_pose_x: float = 10_000.0
    min_pose_y: float = -10_000.0
    max_pose_y: float = 10_000.0
    explicit: bool = False


def validate_mission_run(
    run_dir: Path | str,
    *,
    bounds: Optional[WaypointBounds] = None,
) -> MissionRunValidationResult:
    run_dir = Path(run_dir)
    base = validate_run_directory(run_dir)
    result = MissionRunValidationResult(
        run_dir=run_dir, ok=base.ok, base_replay=base
    )
    for err in base.errors:
        result.add_error(err)
    for warn in base.warnings:
        result.add_warning(warn)

    _validate_mission_states(run_dir, result)
    _validate_waypoint_events(run_dir, result)
    _validate_recovery_events(run_dir, result)
    _validate_world_model_snapshots(
        run_dir, result, bounds=bounds or WaypointBounds()
    )
    return result


def _validate_mission_states(run_dir: Path, result: MissionRunValidationResult) -> None:
    path = run_dir / "mission_state_transitions.jsonl"
    if not path.exists():
        result.add_error("mission_state_transitions.jsonl missing")
        return
    last_sim_ns = -1
    final_state: str | None = None
    with path.open("r", encoding="utf-8") as fh:
        for line_no, raw in enumerate(fh, start=1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError as exc:
                result.add_error(
                    f"mission_state_transitions.jsonl line {line_no} not JSON: {exc}"
                )
                continue
            for required in ("sim_time_ns", "event_id", "from_state", "to_state", "reason_code"):
                if required not in payload:
                    result.add_error(
                        f"mission_state_transitions.jsonl line {line_no}: missing {required!r}"
                    )
            from_state = payload.get("from_state")
            to_state = payload.get("to_state")
            if from_state and from_state not in _MISSION_STATE_VALUES:
                result.add_error(
                    f"unknown from_state {from_state!r} on line {line_no}"
                )
            if to_state and to_state not in _MISSION_STATE_VALUES:
                result.add_error(
                    f"unknown to_state {to_state!r} on line {line_no}"
                )
            sim_ns = int(payload.get("sim_time_ns", 0))
            if sim_ns < last_sim_ns:
                result.add_error(
                    f"mission_state_transitions.jsonl line {line_no}: out-of-order sim_time_ns"
                )
            last_sim_ns = sim_ns
            if isinstance(to_state, str):
                final_state = to_state
            result.mission_state_count += 1
    result.final_mission_state = final_state


def _validate_waypoint_events(run_dir: Path, result: MissionRunValidationResult) -> None:
    path = run_dir / "waypoint_events.jsonl"
    if not path.exists():
        result.add_error("waypoint_events.jsonl missing")
        return
    completed: list[str] = []
    timed_out: list[str] = []
    with path.open("r", encoding="utf-8") as fh:
        for line_no, raw in enumerate(fh, start=1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError as exc:
                result.add_error(f"waypoint_events.jsonl line {line_no} not JSON: {exc}")
                continue
            for required in ("sim_time_ns", "event_type", "reason_code"):
                if required not in payload:
                    result.add_error(
                        f"waypoint_events.jsonl line {line_no}: missing {required!r}"
                    )
            event_type = payload.get("event_type", "")
            phase = event_type.split(".", 1)[1] if "." in event_type else ""
            if phase and phase not in _WAYPOINT_STATUS_VALUES:
                result.add_warning(
                    f"waypoint_events.jsonl line {line_no}: unknown phase {phase!r}"
                )
            wid = payload.get("waypoint_id")
            if event_type == "mission_waypoint.completed" and isinstance(wid, str):
                completed.append(wid)
            elif event_type == "mission_waypoint.timed_out" and isinstance(wid, str):
                timed_out.append(wid)
            result.waypoint_event_count += 1
    result.waypoints_completed = tuple(completed)
    result.waypoints_timed_out = tuple(timed_out)


def _validate_recovery_events(run_dir: Path, result: MissionRunValidationResult) -> None:
    path = run_dir / "recovery_events.jsonl"
    if not path.exists():
        result.add_error("recovery_events.jsonl missing")
        return
    behaviors: set[str] = set()
    with path.open("r", encoding="utf-8") as fh:
        for line_no, raw in enumerate(fh, start=1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError as exc:
                result.add_error(f"recovery_events.jsonl line {line_no} not JSON: {exc}")
                continue
            behavior = payload.get("recovery_behavior")
            if isinstance(behavior, str) and behavior:
                if behavior not in _RECOVERY_BEHAVIOR_VALUES:
                    result.add_error(
                        f"recovery_events.jsonl line {line_no}: unknown recovery_behavior {behavior!r}"
                    )
                behaviors.add(behavior)
            result.recovery_event_count += 1
    result.recovery_behaviors_seen = tuple(sorted(behaviors))


def _validate_world_model_snapshots(
    run_dir: Path,
    result: MissionRunValidationResult,
    *,
    bounds: WaypointBounds,
) -> None:
    path = run_dir / "world_model_snapshots.jsonl"
    if not path.exists():
        result.add_error("world_model_snapshots.jsonl missing")
        return
    last_sim_ns = -1
    if not bounds.explicit:
        result.add_warning(
            "scenario did not declare operational extents; using +/-10_000 m "
            "sanity range for waypoint bounds (#21)"
        )
    with path.open("r", encoding="utf-8") as fh:
        for line_no, raw in enumerate(fh, start=1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError as exc:
                result.add_error(
                    f"world_model_snapshots.jsonl line {line_no} not JSON: {exc}"
                )
                continue
            for key in _REQUIRED_SNAPSHOT_KEYS:
                if key not in payload:
                    result.add_error(
                        f"world_model_snapshots.jsonl line {line_no}: missing {key!r}"
                    )
            sim_ns = int(payload.get("sim_time_ns", 0))
            if sim_ns < last_sim_ns:
                result.add_error(
                    f"world_model_snapshots.jsonl line {line_no}: out-of-order sim_time_ns"
                )
            last_sim_ns = sim_ns
            # #21: numeric-range check on pose_x / pose_y.
            try:
                px = float(payload.get("pose_x", 0.0))
                py = float(payload.get("pose_y", 0.0))
            except (TypeError, ValueError):
                result.add_error(
                    f"world_model_snapshots.jsonl line {line_no}: pose_x/pose_y not numeric"
                )
                px = py = 0.0
            if not (math.isfinite(px) and math.isfinite(py)):
                result.add_error(
                    f"world_model_snapshots.jsonl line {line_no}: non-finite pose"
                )
            elif not (
                bounds.min_pose_x <= px <= bounds.max_pose_x
                and bounds.min_pose_y <= py <= bounds.max_pose_y
            ):
                result.add_error(
                    f"world_model_snapshots.jsonl line {line_no}: pose "
                    f"({px}, {py}) outside operational extents "
                    f"x=[{bounds.min_pose_x}, {bounds.max_pose_x}] "
                    f"y=[{bounds.min_pose_y}, {bounds.max_pose_y}]"
                )
            result.world_model_snapshot_count += 1
