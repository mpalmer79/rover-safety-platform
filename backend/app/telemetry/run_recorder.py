"""Filesystem run recorder.

The recorder writes the canonical replay-ready directory layout described
in docs/REPLAY_SYSTEM.md section 9. It is intentionally simple: files are
opened in append mode for the duration of the run and closed at
:meth:`close`.

The recorder does not depend on the simulation engine; the engine
constructs one and feeds it events, states, commands, and sensor
readings. This keeps the engine decoupled from filesystem details.
"""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any, IO, Optional

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
        self._open()
        self._closed = False
        self._scenario_id = scenario_id
        self._transitions: list[IncidentEntry] = []
        self._fired_faults: set[str] = set()
        self._watchdog_expirations: set[str] = set()
        self._event_count = 0
        self._final_safety_state: SafetyState = SafetyState.BOOT

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
        # Initial metadata is written eagerly; finalize updates it.
        self._write_metadata()

    def _write_metadata(self) -> None:
        path = self._run_dir / "metadata.json"
        path.write_text(json.dumps(self._metadata.to_dict(), indent=2, sort_keys=True), encoding="utf-8")

    def append_event(self, event: Event) -> None:
        if self._closed:
            raise RuntimeError("Recorder is closed")
        assert self._events_file is not None
        self._events_file.write(event.to_json())
        self._events_file.write("\n")
        self._events_file.flush()
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
        )
        self._write_metadata()

        summary = self._build_summary()
        (self._run_dir / "incident-summary.md").write_text(self._render_summary(summary), encoding="utf-8")
        return summary

    def close(self) -> None:
        if self._closed:
            return
        for f in (self._events_file, self._states_file, self._commands_file, self._sensors_file):
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

    @staticmethod
    def _render_summary(summary: RunSummary) -> str:
        lines: list[str] = []
        meta = summary.metadata
        lines.append(f"# Incident Summary — run {meta.run_id}")
        lines.append("")
        lines.append(f"- scenario: `{meta.scenario_id}`")
        lines.append(f"- duration: {summary.duration_ms} ms")
        lines.append(f"- events recorded: {summary.event_count}")
        lines.append(f"- final safety state: `{summary.final_safety_state.value}`")
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
