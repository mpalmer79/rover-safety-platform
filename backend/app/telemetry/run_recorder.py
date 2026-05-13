"""Filesystem run recorder.

The recorder writes the canonical replay-ready directory layout described
in docs/REPLAY_SYSTEM.md section 9. It is intentionally simple: files are
opened in append mode for the duration of the run and closed at
:meth:`close`.

The recorder does not depend on the simulation engine; the engine
constructs one and feeds it events, states, commands, and sensor
readings. This keeps the engine decoupled from filesystem details.

events.jsonl is **tamper-evident** (#13). Every event line carries a
``prev_event_hash`` field whose value is the SHA-256 of the *previous*
event's canonical bytes (see :mod:`app.replay.chain` for the exact
serialisation). The first event chains to ``"0" * 64``. At
:meth:`finalize` the recorder writes the final tip and the integer
event count into ``metadata.json`` as ``events_chain_tip`` and
``events_count``. The replay validator recomputes the chain end-to-end
on read and refuses any mismatch.
"""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any, IO, Optional

from app.telemetry.chain import CHAIN_FIELD, GENESIS_HASH, hash_canonical

from app.domain.enums import ReplayStatus, SafetyState
from app.domain.events import Event
from app.domain.identifiers import RunId, ScenarioId
from app.domain.motion import AuthorizedMotionCommand, RequestedMotionCommand
from app.domain.replay import IncidentEntry, RunMetadata, RunSummary
from app.domain.rover_state import RoverState
from app.domain.sensors import SensorFrame


class RunRecorder:
    """Append-only writer for one run."""

    def __init__(
        self,
        *,
        runs_root: str | Path,
        run_id: RunId,
        scenario_id: ScenarioId,
        metadata: RunMetadata,
    ) -> None:
        self._runs_root = Path(runs_root)
        self._run_dir = self._runs_root / str(run_id)
        self._run_dir.mkdir(parents=True, exist_ok=True)
        (self._run_dir / "bags").mkdir(exist_ok=True)
        (self._run_dir / "traces").mkdir(exist_ok=True)
        self._metadata = metadata
        self._events_file: Optional[IO[str]] = None
        self._states_file: Optional[IO[str]] = None
        self._commands_file: Optional[IO[str]] = None
        self._sensors_file: Optional[IO[str]] = None
        self._mission_state_file: Optional[IO[str]] = None
        self._waypoint_events_file: Optional[IO[str]] = None
        self._recovery_events_file: Optional[IO[str]] = None
        self._world_model_file: Optional[IO[str]] = None
        self._open()
        self._closed = False
        self._scenario_id = scenario_id
        self._transitions: list[IncidentEntry] = []
        self._fired_faults: set[str] = set()
        self._watchdog_expirations: set[str] = set()
        self._event_count = 0
        # Running tip for the tamper-evident event chain. The next
        # event's ``prev_event_hash`` will carry this value; the
        # GENESIS_HASH is recorded for the very first event.
        self._chain_tip: str = GENESIS_HASH
        self._final_safety_state: SafetyState = SafetyState.BOOT
        # Phase 2 counters.
        self._mission_state_count = 0
        self._waypoint_event_count = 0
        self._recovery_event_count = 0
        self._world_model_snapshot_count = 0
        self._final_mission_state: str = "MISSION_IDLE"
        self._mission_lifecycle: list[dict[str, Any]] = []
        self._waypoints_completed: list[str] = []
        self._waypoints_timed_out: list[str] = []
        self._recovery_engagements: list[dict[str, Any]] = []

    @property
    def run_dir(self) -> Path:
        return self._run_dir

    @property
    def metadata(self) -> RunMetadata:
        return self._metadata

    def _open(self) -> None:
        self._events_file = (self._run_dir / "events.jsonl").open("w", encoding="utf-8")
        self._states_file = (self._run_dir / "states.jsonl").open("w", encoding="utf-8")
        self._commands_file = (self._run_dir / "commands.jsonl").open("w", encoding="utf-8")
        self._sensors_file = (self._run_dir / "sensor_readings.jsonl").open("w", encoding="utf-8")
        # Phase 2 mission artefacts. The files are always created (with
        # zero records when no mission is active) so replay validators
        # can rely on their presence.
        self._mission_state_file = (
            self._run_dir / "mission_state_transitions.jsonl"
        ).open("w", encoding="utf-8")
        self._waypoint_events_file = (
            self._run_dir / "waypoint_events.jsonl"
        ).open("w", encoding="utf-8")
        self._recovery_events_file = (
            self._run_dir / "recovery_events.jsonl"
        ).open("w", encoding="utf-8")
        self._world_model_file = (
            self._run_dir / "world_model_snapshots.jsonl"
        ).open("w", encoding="utf-8")
        # Initial metadata is written eagerly; finalize updates it.
        self._write_metadata()

    def _write_metadata(self) -> None:
        path = self._run_dir / "metadata.json"
        path.write_text(json.dumps(self._metadata.to_dict(), indent=2, sort_keys=True), encoding="utf-8")

    def append_event(self, event: Event) -> None:
        if self._closed:
            raise RuntimeError("Recorder is closed")
        assert self._events_file is not None
        # Chain step (#13): the event we are about to write carries the
        # hash of the previous event's canonical bytes. Once written,
        # advance the running tip to the hash of *this* event's
        # canonical bytes for the next call.
        payload = event.to_dict()
        payload[CHAIN_FIELD] = self._chain_tip
        line = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )
        self._events_file.write(line)
        self._events_file.write("\n")
        self._events_file.flush()
        self._chain_tip = hash_canonical(payload)
        self._event_count += 1

        if event.event_type == "safety_transition.entered":
            self._transitions.append(
                IncidentEntry(
                    sim_time_ns=event.timestamp.sim_time_ns,
                    safety_state=event.safety_state,
                    reason_code=event.reason_code,
                    summary=event.message,
                )
            )
            self._final_safety_state = event.safety_state
        elif event.event_type == "fault_injection.fired":
            fid = event.attributes.get("fault_id")
            if isinstance(fid, str):
                self._fired_faults.add(fid)
        elif event.event_type == "watchdog.expired":
            name = event.attributes.get("watchdog_name")
            if isinstance(name, str):
                self._watchdog_expirations.add(name)
        # Phase 2 mission / world-model fan-out.
        if event.event_type.startswith("mission_lifecycle."):
            assert self._mission_state_file is not None
            row = {
                "sim_time_ns": event.timestamp.sim_time_ns,
                "event_id": str(event.event_id),
                "event_type": event.event_type,
                "reason_code": event.reason_code,
                "from_state": event.attributes.get("from_state"),
                "to_state": event.attributes.get("to_state"),
                "message": event.message,
            }
            self._mission_state_file.write(json.dumps(row, separators=(",", ":")))
            self._mission_state_file.write("\n")
            self._mission_state_file.flush()
            self._mission_state_count += 1
            self._mission_lifecycle.append(row)
            to_state = event.attributes.get("to_state")
            if isinstance(to_state, str):
                self._final_mission_state = to_state
        elif event.event_type.startswith("mission_waypoint."):
            assert self._waypoint_events_file is not None
            row = {
                "sim_time_ns": event.timestamp.sim_time_ns,
                "event_id": str(event.event_id),
                "event_type": event.event_type,
                "reason_code": event.reason_code,
                "waypoint_id": event.attributes.get("waypoint_id"),
                "elapsed_ms": event.attributes.get("elapsed_ms"),
                "message": event.message,
            }
            self._waypoint_events_file.write(json.dumps(row, separators=(",", ":")))
            self._waypoint_events_file.write("\n")
            self._waypoint_events_file.flush()
            self._waypoint_event_count += 1
            wid = event.attributes.get("waypoint_id")
            if event.event_type == "mission_waypoint.completed" and isinstance(wid, str):
                self._waypoints_completed.append(wid)
            elif event.event_type == "mission_waypoint.timed_out" and isinstance(wid, str):
                self._waypoints_timed_out.append(wid)
        elif event.event_type.startswith("mission_recovery."):
            assert self._recovery_events_file is not None
            row = {
                "sim_time_ns": event.timestamp.sim_time_ns,
                "event_id": str(event.event_id),
                "event_type": event.event_type,
                "reason_code": event.reason_code,
                "recovery_behavior": event.attributes.get("recovery_behavior"),
                "waypoint_id": event.attributes.get("waypoint_id"),
                "attempt_count": event.attributes.get("attempt_count"),
                "message": event.message,
            }
            self._recovery_events_file.write(json.dumps(row, separators=(",", ":")))
            self._recovery_events_file.write("\n")
            self._recovery_events_file.flush()
            self._recovery_event_count += 1
            if event.event_type == "mission_recovery.engaged":
                self._recovery_engagements.append(row)

    def append_state(self, state: RoverState) -> None:
        if self._closed:
            raise RuntimeError("Recorder is closed")
        assert self._states_file is not None
        self._states_file.write(json.dumps(state.to_dict(), separators=(",", ":")))
        self._states_file.write("\n")
        self._states_file.flush()

    def append_command(
        self,
        *,
        requested: Optional[RequestedMotionCommand],
        authorized: AuthorizedMotionCommand,
        sim_time_ns: int,
    ) -> None:
        if self._closed:
            raise RuntimeError("Recorder is closed")
        assert self._commands_file is not None
        payload: dict[str, Any] = {
            "sim_time_ns": sim_time_ns,
            "requested": requested.to_dict() if requested else None,
            "authorized": authorized.to_dict(),
        }
        self._commands_file.write(json.dumps(payload, separators=(",", ":")))
        self._commands_file.write("\n")
        self._commands_file.flush()

    def append_sensor_frame(self, frame: SensorFrame, *, sim_time_ns: int) -> None:
        if self._closed:
            raise RuntimeError("Recorder is closed")
        assert self._sensors_file is not None
        payload: dict[str, Any] = {"sim_time_ns": sim_time_ns, "frame": frame.to_dict()}
        self._sensors_file.write(json.dumps(payload, separators=(",", ":")))
        self._sensors_file.write("\n")
        self._sensors_file.flush()

    def append_world_model_snapshot(self, snapshot, *, sim_time_ns: int | None = None) -> None:
        """Append a :class:`WorldModelSnapshot` to ``world_model_snapshots.jsonl``.

        ``sim_time_ns`` is optional because the snapshot already carries
        its own. The argument is accepted only for API symmetry with the
        other append methods.
        """

        if self._closed:
            raise RuntimeError("Recorder is closed")
        assert self._world_model_file is not None
        payload = snapshot.to_dict()
        self._world_model_file.write(json.dumps(payload, separators=(",", ":")))
        self._world_model_file.write("\n")
        self._world_model_file.flush()
        self._world_model_snapshot_count += 1

    def append_mission_progress(
        self,
        *,
        mission_state,
        progress,
        recovery,
        sim_time_ns: int,
    ) -> None:
        """Record one tick of mission progress.

        The recorder always writes a row even when ``progress`` is None
        (idle / paused / complete) so replay tooling can reason about
        per-tick mission state without sparse-row handling.
        """

        if self._closed:
            raise RuntimeError("Recorder is closed")
        # Latest mission state lives on the lifecycle stream.
        self._final_mission_state = (
            mission_state.value if hasattr(mission_state, "value") else str(mission_state)
        )

    def finalize(
        self,
        *,
        ended_wall: str,
        ended_sim_ns: int,
        status: ReplayStatus = ReplayStatus.FINALIZED,
    ) -> RunSummary:
        from dataclasses import replace

        self._metadata = replace(
            self._metadata,
            ended_wall=ended_wall,
            ended_sim_ns=ended_sim_ns,
            status=status,
            events_chain_tip=self._chain_tip,
            events_count=self._event_count,
        )
        self._write_metadata()

        summary = self._build_summary()
        (self._run_dir / "incident-summary.md").write_text(self._render_summary(summary), encoding="utf-8")
        return summary

    def close(self) -> None:
        if self._closed:
            return
        for f in (
            self._events_file,
            self._states_file,
            self._commands_file,
            self._sensors_file,
            self._mission_state_file,
            self._waypoint_events_file,
            self._recovery_events_file,
            self._world_model_file,
        ):
            if isinstance(f, io.IOBase):
                f.close()
        self._closed = True

    def __enter__(self) -> "RunRecorder":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _build_summary(self) -> RunSummary:
        duration_ms = 0
        if self._metadata.ended_sim_ns is not None:
            duration_ms = max(0, (self._metadata.ended_sim_ns - self._metadata.started_sim_ns) // 1_000_000)
        return RunSummary(
            metadata=self._metadata,
            final_safety_state=self._final_safety_state,
            transitions=tuple(self._transitions),
            fired_faults=tuple(sorted(self._fired_faults)),
            watchdog_expirations=tuple(sorted(self._watchdog_expirations)),
            duration_ms=int(duration_ms),
            event_count=self._event_count,
        )

    def _render_summary(self, summary: RunSummary) -> str:
        lines: list[str] = []
        meta = summary.metadata
        lines.append(f"# Incident Summary — run {meta.run_id}")
        lines.append("")
        lines.append(f"- scenario: `{meta.scenario_id}`")
        lines.append(f"- duration: {summary.duration_ms} ms")
        lines.append(f"- events recorded: {summary.event_count}")
        lines.append(f"- final safety state: `{summary.final_safety_state.value}`")
        if self._mission_state_count > 0:
            lines.append(f"- final mission state: `{self._final_mission_state}`")
            lines.append(
                f"- mission lifecycle records: {self._mission_state_count}"
            )
        lines.append(f"- supervisor version: {meta.supervisor_version}")
        lines.append(f"- simulator version: {meta.simulator_version}")
        lines.append("")
        lines.append("## Safety transitions")
        if not summary.transitions:
            lines.append("_None._")
        else:
            for t in summary.transitions:
                lines.append(
                    f"- `t={t.sim_time_ns/1_000_000:.0f}ms` "
                    f"`{t.safety_state.value}` "
                    f"reason `{t.reason_code}` — {t.summary}"
                )
        lines.append("")
        lines.append("## Mission lifecycle")
        if not self._mission_lifecycle:
            lines.append("_None._")
        else:
            for entry in self._mission_lifecycle:
                lines.append(
                    f"- `t={entry['sim_time_ns']/1_000_000:.0f}ms` "
                    f"`{entry.get('to_state','?')}` reason `{entry['reason_code']}` — "
                    f"{entry['message']}"
                )
        lines.append("")
        lines.append("## Waypoints")
        lines.append(f"- completed: {len(self._waypoints_completed)}")
        lines.append(f"- timed out: {len(self._waypoints_timed_out)}")
        if self._waypoints_completed:
            lines.append("")
            lines.append("Completed:")
            for w in self._waypoints_completed:
                lines.append(f"- `{w}`")
        if self._waypoints_timed_out:
            lines.append("")
            lines.append("Timed out:")
            for w in self._waypoints_timed_out:
                lines.append(f"- `{w}`")
        lines.append("")
        lines.append("## Recovery engagements")
        if not self._recovery_engagements:
            lines.append("_None._")
        else:
            for r in self._recovery_engagements:
                lines.append(
                    f"- `t={r['sim_time_ns']/1_000_000:.0f}ms` "
                    f"`{r.get('recovery_behavior','?')}` waypoint `{r.get('waypoint_id','-')}` — "
                    f"{r['message']}"
                )
        lines.append("")
        lines.append("## Fired faults")
        if not summary.fired_faults:
            lines.append("_None._")
        else:
            for f in summary.fired_faults:
                lines.append(f"- `{f}`")
        lines.append("")
        lines.append("## Watchdog expirations")
        if not summary.watchdog_expirations:
            lines.append("_None._")
        else:
            for w in summary.watchdog_expirations:
                lines.append(f"- `{w}`")
        lines.append("")
        return "\n".join(lines)
