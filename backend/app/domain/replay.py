"""Replay-related value objects: run metadata, summaries, and incidents."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from app.domain.enums import ReplayStatus, SafetyState
from app.domain.identifiers import RunId, ScenarioId


@dataclass(frozen=True, slots=True)
class RunMetadata:
    """Per-run metadata mirroring docs/REPLAY_SYSTEM.md section 9.1."""

    run_id: RunId
    scenario_id: ScenarioId
    started_wall: str
    started_sim_ns: int
    ended_wall: Optional[str] = None
    ended_sim_ns: Optional[int] = None
    event_schema_version: str = "1.0.0"
    supervisor_version: str = "0.1.0"
    fault_subsystem_version: str = "0.1.0"
    simulator_version: str = "deterministic-engine-0.1.0"
    rover_description_hash: Optional[str] = None
    world_hash: Optional[str] = None
    determinism_level: str = "pinned"
    recorded_topics: tuple[str, ...] = field(default_factory=tuple)
    armed_faults: tuple[str, ...] = field(default_factory=tuple)
    status: ReplayStatus = ReplayStatus.OPEN
    extra: dict[str, Any] = field(default_factory=dict)
    # Tamper-evident event chain (#13). ``events_chain_tip`` is the
    # SHA-256 (hex, lower-case) of the LAST event's canonical bytes
    # at finalize time - i.e. the un-chained event serialised with
    # json.dumps(sort_keys=True, separators=(",",":"),
    # ensure_ascii=False), with the event's own ``prev_event_hash``
    # field removed. ``events_count`` is the integer count of lines
    # in events.jsonl at finalize. Both are None before finalize.
    events_chain_tip: Optional[str] = None
    events_count: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": str(self.run_id),
            "scenario_id": str(self.scenario_id),
            "started_wall": self.started_wall,
            "started_sim_ns": self.started_sim_ns,
            "ended_wall": self.ended_wall,
            "ended_sim_ns": self.ended_sim_ns,
            "event_schema_version": self.event_schema_version,
            "supervisor_version": self.supervisor_version,
            "fault_subsystem_version": self.fault_subsystem_version,
            "simulator_version": self.simulator_version,
            "rover_description_hash": self.rover_description_hash,
            "world_hash": self.world_hash,
            "determinism_level": self.determinism_level,
            "recorded_topics": list(self.recorded_topics),
            "armed_faults": list(self.armed_faults),
            "status": self.status.value,
            "extra": dict(self.extra),
            "events_chain_tip": self.events_chain_tip,
            "events_count": self.events_count,
        }


@dataclass(frozen=True, slots=True)
class IncidentEntry:
    """One row of an incident summary."""

    sim_time_ns: int
    safety_state: SafetyState
    reason_code: str
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "sim_time_ns": self.sim_time_ns,
            "safety_state": self.safety_state.value,
            "reason_code": self.reason_code,
            "summary": self.summary,
        }


@dataclass(frozen=True, slots=True)
class RunSummary:
    """Top-level run summary used by the API and the incident summary renderer."""

    metadata: RunMetadata
    final_safety_state: SafetyState
    transitions: tuple[IncidentEntry, ...]
    fired_faults: tuple[str, ...]
    watchdog_expirations: tuple[str, ...]
    duration_ms: int
    event_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "metadata": self.metadata.to_dict(),
            "final_safety_state": self.final_safety_state.value,
            "transitions": [t.to_dict() for t in self.transitions],
            "fired_faults": list(self.fired_faults),
            "watchdog_expirations": list(self.watchdog_expirations),
            "duration_ms": self.duration_ms,
            "event_count": self.event_count,
        }
