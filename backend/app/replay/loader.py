"""Replay loader.

Reads a recorded run directory and exposes its events, states, and
commands without depending on the recorder. Used by tests, the API, and
future replay validators.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator, Optional

from app.domain.enums import ReplayStatus, SafetyState
from app.domain.identifiers import RunId, ScenarioId
from app.domain.replay import RunMetadata
from app.replay.manifest import RunManifest


def load_metadata(run_dir: Path) -> RunMetadata:
    path = run_dir / "metadata.json"
    if not path.exists():
        raise FileNotFoundError(f"metadata.json not found in {run_dir}")
    data = json.loads(path.read_text(encoding="utf-8"))
    return RunMetadata(
        run_id=RunId(data["run_id"]),
        scenario_id=ScenarioId(data["scenario_id"]),
        started_wall=data["started_wall"],
        started_sim_ns=int(data["started_sim_ns"]),
        ended_wall=data.get("ended_wall"),
        ended_sim_ns=data.get("ended_sim_ns"),
        event_schema_version=data.get("event_schema_version", "1.0.0"),
        supervisor_version=data.get("supervisor_version", "0.0.0"),
        fault_subsystem_version=data.get("fault_subsystem_version", "0.0.0"),
        simulator_version=data.get("simulator_version", "deterministic-engine-0.1.0"),
        rover_description_hash=data.get("rover_description_hash"),
        world_hash=data.get("world_hash"),
        determinism_level=data.get("determinism_level", "pinned"),
        recorded_topics=tuple(data.get("recorded_topics", [])),
        armed_faults=tuple(data.get("armed_faults", [])),
        status=ReplayStatus(data.get("status", ReplayStatus.OPEN.value)),
        extra=dict(data.get("extra", {})),
        events_chain_tip=data.get("events_chain_tip"),
        events_count=data.get("events_count"),
    )


class RunLoader:
    """Lightweight reader for a recorded run."""

    def __init__(self, run_dir: str | Path) -> None:
        self._run_dir = Path(run_dir)
        if not self._run_dir.exists():
            raise FileNotFoundError(self._run_dir)

    @property
    def run_dir(self) -> Path:
        return self._run_dir

    def manifest(self) -> RunManifest:
        return RunManifest(run_dir=self._run_dir, metadata=load_metadata(self._run_dir))

    def events(self) -> Iterator[dict[str, Any]]:
        return _read_jsonl(self._run_dir / "events.jsonl")

    def states(self) -> Iterator[dict[str, Any]]:
        return _read_jsonl(self._run_dir / "states.jsonl")

    def commands(self) -> Iterator[dict[str, Any]]:
        return _read_jsonl(self._run_dir / "commands.jsonl")

    def sensor_frames(self) -> Iterator[dict[str, Any]]:
        return _read_jsonl(self._run_dir / "sensor_readings.jsonl")

    def find_first_safety_state(self, state: SafetyState) -> Optional[dict[str, Any]]:
        for evt in self.events():
            if evt.get("event_type") == "safety_transition.entered" and evt.get("safety_state") == state.value:
                return evt
        return None


def _read_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    if not path.exists():
        return iter(())

    def _gen():
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    yield json.loads(line)

    return _gen()
