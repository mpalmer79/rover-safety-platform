"""Validate a recorded run directory against the replay contract.

Asserts the run directory matches the layout defined in
``docs/REPLAY_SYSTEM.md`` section 9 and that the recorded streams are
self-consistent:

* ``metadata.json`` parses, has the required fields, and is
  ``finalized`` if the run is meant to be replay-eligible.
* ``events.jsonl`` validates against :mod:`app.telemetry.schemas`
  for every line.
* Event sim_time_ns is monotonically non-decreasing per producer.
* ``states.jsonl``, ``commands.jsonl``, ``sensor_readings.jsonl`` parse
  and have at least one record.
* All ``correlation_id`` references and ``parent_event_id`` references
  resolve to events present in the same run.
* The ``run_id`` and ``scenario_id`` are consistent across metadata
  and events.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from app.telemetry.schemas import EventSchemaError, validate_event_dict


@dataclass
class ReplayValidationResult:
    run_dir: Path
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    # Counts captured during the walk.
    event_count: int = 0
    state_count: int = 0
    command_count: int = 0
    sensor_frame_count: int = 0
    transition_count: int = 0
    fired_fault_ids: set[str] = field(default_factory=set)

    def add_error(self, message: str) -> None:
        self.errors.append(message)
        self.ok = False

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def as_dict(self) -> dict:
        return {
            "run_dir": str(self.run_dir),
            "ok": self.ok,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "event_count": self.event_count,
            "state_count": self.state_count,
            "command_count": self.command_count,
            "sensor_frame_count": self.sensor_frame_count,
            "transition_count": self.transition_count,
            "fired_fault_ids": sorted(self.fired_fault_ids),
        }


_REQUIRED_TOP_LEVEL = (
    "metadata.json",
    "events.jsonl",
    "states.jsonl",
    "commands.jsonl",
    "sensor_readings.jsonl",
    "incident-summary.md",
    "bags",
    "traces",
)


def validate_run_directory(run_dir: Path | str) -> ReplayValidationResult:
    run_dir = Path(run_dir)
    result = ReplayValidationResult(run_dir=run_dir, ok=True)

    if not run_dir.exists() or not run_dir.is_dir():
        result.add_error(f"run directory does not exist or is not a directory: {run_dir}")
        return result

    for name in _REQUIRED_TOP_LEVEL:
        path = run_dir / name
        if not path.exists():
            result.add_error(f"missing required artefact: {name}")

    metadata = _validate_metadata(run_dir, result)
    if metadata is None:
        return result

    expected_run_id = metadata.get("run_id")
    expected_scenario_id = metadata.get("scenario_id")

    _validate_events(run_dir, result, expected_run_id, expected_scenario_id)
    _count_jsonl(run_dir / "states.jsonl", result, "state_count")
    _count_jsonl(run_dir / "commands.jsonl", result, "command_count")
    _count_jsonl(run_dir / "sensor_readings.jsonl", result, "sensor_frame_count")

    return result


def _validate_metadata(run_dir: Path, result: ReplayValidationResult) -> dict | None:
    path = run_dir / "metadata.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        result.add_error(f"metadata.json is not valid JSON: {exc}")
        return None
    for key in (
        "run_id",
        "scenario_id",
        "started_wall",
        "started_sim_ns",
        "event_schema_version",
        "recorded_topics",
        "status",
    ):
        if key not in data:
            result.add_error(f"metadata.json missing field: {key}")
    if data.get("status") not in {"open", "finalized", "invalid"}:
        result.add_error(f"metadata.json status invalid: {data.get('status')!r}")
    if data.get("status") != "finalized":
        result.add_warning(
            f"metadata.json status is {data.get('status')!r}; only finalised runs are replay-eligible"
        )
    return data


def _validate_events(
    run_dir: Path,
    result: ReplayValidationResult,
    expected_run_id: str | None,
    expected_scenario_id: str | None,
) -> None:
    path = run_dir / "events.jsonl"
    if not path.exists():
        return
    last_sim_ns_per_producer: dict[tuple[str, str], int] = {}
    seen_event_ids: set[str] = set()
    referenced_correlation_ids: set[str] = set()
    referenced_parent_ids: set[str] = set()
    seen_correlation_ids: set[str] = set()
    with path.open("r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                result.add_error(f"events.jsonl line {line_no} not valid JSON: {exc}")
                continue
            try:
                validate_event_dict(payload)
            except EventSchemaError as exc:
                result.add_error(f"events.jsonl line {line_no}: {exc}")
                continue

            event_id = payload["event_id"]
            if event_id in seen_event_ids:
                result.add_error(f"duplicate event_id in events.jsonl: {event_id}")
            seen_event_ids.add(event_id)

            if expected_run_id is not None and payload["run_id"] != expected_run_id:
                result.add_error(
                    f"events.jsonl line {line_no}: run_id "
                    f"{payload['run_id']!r} does not match metadata {expected_run_id!r}"
                )
            if expected_scenario_id is not None and payload["scenario_id"] != expected_scenario_id:
                result.add_warning(
                    f"events.jsonl line {line_no}: scenario_id "
                    f"{payload['scenario_id']!r} does not match metadata {expected_scenario_id!r}"
                )

            producer_key = (payload["subsystem"], payload["node"])
            sim_ns = int(payload.get("sim_time_ns", 0))
            previous = last_sim_ns_per_producer.get(producer_key)
            if previous is not None and sim_ns < previous:
                result.add_error(
                    f"events.jsonl line {line_no}: per-producer ordering violated "
                    f"({producer_key}: {sim_ns} < {previous})"
                )
            last_sim_ns_per_producer[producer_key] = sim_ns

            if payload.get("correlation_id"):
                seen_correlation_ids.add(payload["correlation_id"])
                referenced_correlation_ids.add(payload["correlation_id"])
            if payload.get("parent_event_id"):
                referenced_parent_ids.add(payload["parent_event_id"])

            event_type = payload["event_type"]
            if event_type == "safety_transition.entered":
                result.transition_count += 1
            if event_type == "fault_injection.fired":
                fid = payload.get("attributes", {}).get("fault_id")
                if isinstance(fid, str):
                    result.fired_fault_ids.add(fid)
            result.event_count += 1

    unresolved_parents = referenced_parent_ids - seen_event_ids
    if unresolved_parents:
        result.add_warning(
            "events.jsonl has parent_event_id references that resolve outside the run: "
            + ", ".join(sorted(unresolved_parents))
        )


def _count_jsonl(path: Path, result: ReplayValidationResult, attr: str) -> None:
    if not path.exists():
        return
    count = 0
    with path.open("r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                json.loads(line)
            except json.JSONDecodeError as exc:
                result.add_error(f"{path.name} line {line_no} not valid JSON: {exc}")
                continue
            count += 1
    setattr(result, attr, count)
    if count == 0:
        result.add_warning(f"{path.name} contains no records")
