"""Scenario definitions for the deterministic simulation engine."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar, Iterable, Optional

from app.domain.enums import FaultType
from app.domain.faults import FaultProfile
from app.domain.identifiers import ScenarioId


@dataclass(frozen=True, slots=True)
class ScenarioInitialState:
    """Initial pose/orientation and any operator preconditions."""

    pose_x: float = 0.0
    pose_y: float = 0.0
    heading_rad: float = 0.0
    operator_activate_at_ms: int = 200
    operator_estop_at_ms: Optional[int] = None
    operator_recovery_at_ms: Optional[int] = None
    operator_reset_at_ms: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "pose_x": self.pose_x,
            "pose_y": self.pose_y,
            "heading_rad": self.heading_rad,
            "operator_activate_at_ms": self.operator_activate_at_ms,
            "operator_estop_at_ms": self.operator_estop_at_ms,
            "operator_recovery_at_ms": self.operator_recovery_at_ms,
            "operator_reset_at_ms": self.operator_reset_at_ms,
        }


@dataclass(frozen=True, slots=True)
class RequestedMotionPlan:
    """A constant motion request that the mission layer would issue.

    The Phase 1A engine does not yet host BehaviorTree.CPP. Instead,
    scenarios declare the motion the mission layer "would" request, and
    the engine replays it through the supervisor exactly as a real
    mission would.
    """

    linear_velocity: float
    angular_velocity: float
    starts_at_ms: int = 0
    ends_at_ms: Optional[int] = None
    command_lifetime_ms: int = 500

    def to_dict(self) -> dict[str, Any]:
        return {
            "linear_velocity": self.linear_velocity,
            "angular_velocity": self.angular_velocity,
            "starts_at_ms": self.starts_at_ms,
            "ends_at_ms": self.ends_at_ms,
            "command_lifetime_ms": self.command_lifetime_ms,
        }


@dataclass(frozen=True, slots=True)
class ScenarioFault:
    """A scenario-level fault declaration; converts to :class:`FaultProfile`."""

    fault_id: str
    fault_type: str
    target: str
    activation_ms: int
    duration_ms: int = -1
    parameters: dict[str, Any] = field(default_factory=dict)

    def to_profile(self) -> FaultProfile:
        try:
            ftype = FaultType(self.fault_type)
        except ValueError as exc:
            raise ValueError(f"Unknown fault_type: {self.fault_type!r}") from exc
        return FaultProfile(
            fault_id=self.fault_id,
            fault_type=ftype,
            target=self.target,
            activation_ms=self.activation_ms,
            duration_ms=self.duration_ms,
            parameters=dict(self.parameters),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "fault_id": self.fault_id,
            "fault_type": self.fault_type,
            "target": self.target,
            "activation_ms": self.activation_ms,
            "duration_ms": self.duration_ms,
            "parameters": dict(self.parameters),
        }


@dataclass(frozen=True, slots=True)
class ScenarioDefinition:
    """A single scenario the engine can run."""

    scenario_id: ScenarioId
    duration_seconds: float
    time_step_ms: int = 100
    initial_state: ScenarioInitialState = field(default_factory=ScenarioInitialState)
    requested_motion: RequestedMotionPlan = field(
        default_factory=lambda: RequestedMotionPlan(linear_velocity=0.4, angular_velocity=0.0)
    )
    faults: tuple[ScenarioFault, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)
    # Optional Phase-2 mission plan. Stored as a raw dict to keep
    # ``app.domain.scenarios`` independent of ``app.mission`` /
    # ``app.world_model``. The simulation engine resolves it via
    # :meth:`MissionPlan.from_dict` when present.
    mission_plan: dict[str, Any] | None = None

    # Hard bounds enforced at construction time. The simulation engine
    # is deterministic but not cheap; an attacker who can post arbitrary
    # scenario payloads should not be able to spin a 1 GHz / 24-hour
    # configuration that pegs the worker. These bounds are conservative
    # — well above any sane test scenario and well below "denial".
    MAX_DURATION_SECONDS: ClassVar[float] = 3600.0
    MIN_TIME_STEP_MS: ClassVar[int] = 1
    MAX_TOTAL_STEPS: ClassVar[int] = 1_000_000
    MAX_FAULTS: ClassVar[int] = 64

    def __post_init__(self) -> None:
        if self.time_step_ms < self.MIN_TIME_STEP_MS:
            raise ValueError(
                f"time_step_ms must be >= {self.MIN_TIME_STEP_MS}"
            )
        if self.duration_seconds <= 0:
            raise ValueError("duration_seconds must be positive")
        if self.duration_seconds > self.MAX_DURATION_SECONDS:
            raise ValueError(
                f"duration_seconds must be <= {self.MAX_DURATION_SECONDS}"
            )
        if self.total_steps > self.MAX_TOTAL_STEPS:
            raise ValueError(
                f"total_steps must be <= {self.MAX_TOTAL_STEPS}"
            )
        if len(self.faults) > self.MAX_FAULTS:
            raise ValueError(f"faults must contain <= {self.MAX_FAULTS} entries")

    @property
    def has_mission_plan(self) -> bool:
        return self.mission_plan is not None

    @property
    def duration_ms(self) -> int:
        return int(self.duration_seconds * 1000)

    @property
    def total_steps(self) -> int:
        return self.duration_ms // self.time_step_ms

    def fault_profiles(self) -> tuple[FaultProfile, ...]:
        return tuple(f.to_profile() for f in self.faults)

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "scenario_id": str(self.scenario_id),
            "duration_seconds": self.duration_seconds,
            "time_step_ms": self.time_step_ms,
            "initial_state": self.initial_state.to_dict(),
            "requested_motion": self.requested_motion.to_dict(),
            "faults": [f.to_dict() for f in self.faults],
            "metadata": dict(self.metadata),
        }
        if self.mission_plan is not None:
            out["mission_plan"] = dict(self.mission_plan)
        return out

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScenarioDefinition":
        sid = data.get("scenario_id")
        if not sid:
            raise ValueError("scenario_id is required")
        initial_state = ScenarioInitialState(**data.get("initial_state", {}))
        rm_data = data.get("requested_motion") or {}
        requested_motion = RequestedMotionPlan(
            linear_velocity=float(rm_data.get("linear_velocity", 0.0)),
            angular_velocity=float(rm_data.get("angular_velocity", 0.0)),
            starts_at_ms=int(rm_data.get("starts_at_ms", 0)),
            ends_at_ms=rm_data.get("ends_at_ms"),
            command_lifetime_ms=int(rm_data.get("command_lifetime_ms", 500)),
        )
        faults = tuple(
            ScenarioFault(
                fault_id=f["fault_id"],
                fault_type=f["fault_type"],
                target=f["target"],
                activation_ms=int(f["activation_ms"]),
                duration_ms=int(f.get("duration_ms", -1)),
                parameters=dict(f.get("parameters", {})),
            )
            for f in data.get("faults", [])
        )
        mission_plan = data.get("mission_plan")
        if mission_plan is not None and not isinstance(mission_plan, dict):
            raise ValueError("mission_plan must be a JSON object")
        return cls(
            scenario_id=ScenarioId(str(sid)),
            duration_seconds=float(data["duration_seconds"]),
            time_step_ms=int(data.get("time_step_ms", 100)),
            initial_state=initial_state,
            requested_motion=requested_motion,
            faults=faults,
            metadata=dict(data.get("metadata", {})),
            mission_plan=dict(mission_plan) if mission_plan else None,
        )

    @classmethod
    def from_json_file(cls, path: str | Path) -> "ScenarioDefinition":
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return cls.from_dict(data)


def load_scenarios(directory: str | Path) -> Iterable[ScenarioDefinition]:
    p = Path(directory)
    for entry in sorted(p.glob("*.json")):
        yield ScenarioDefinition.from_json_file(entry)
