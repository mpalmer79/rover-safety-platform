"""Standalone event-stream validator.

Wraps :func:`app.telemetry.schemas.validate_event_dict` for use against
``events.jsonl`` files outside a full run-directory check. Used by the
``tools/validate_event_integrity.py`` CLI.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from app.telemetry.schemas import EventSchemaError, validate_event_dict


@dataclass
class EventValidationResult:
    source: str
    ok: bool = True
    line_count: int = 0
    valid_count: int = 0
    errors: list[str] = field(default_factory=list)
    duplicate_event_ids: list[str] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        self.errors.append(message)
        self.ok = False

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "ok": self.ok,
            "line_count": self.line_count,
            "valid_count": self.valid_count,
            "errors": list(self.errors),
            "duplicate_event_ids": list(self.duplicate_event_ids),
        }


def validate_events_iter(
    payloads: Iterable[dict], *, source: str = "<iter>"
) -> EventValidationResult:
    result = EventValidationResult(source=source)
    seen_ids: set[str] = set()
    for index, payload in enumerate(payloads, start=1):
        result.line_count += 1
        if not isinstance(payload, dict):
            result.add_error(f"{source} entry {index}: not a JSON object")
            continue
        try:
            validate_event_dict(payload)
        except EventSchemaError as exc:
            result.add_error(f"{source} entry {index}: {exc}")
            continue
        eid = payload["event_id"]
        if eid in seen_ids:
            result.duplicate_event_ids.append(eid)
            result.add_error(f"{source} entry {index}: duplicate event_id {eid!r}")
        seen_ids.add(eid)
        result.valid_count += 1
    return result


def validate_events_file(path: Path | str) -> EventValidationResult:
    path = Path(path)
    if not path.exists():
        result = EventValidationResult(source=str(path))
        result.add_error(f"file does not exist: {path}")
        return result

    payloads: list[dict] = []
    with path.open("r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                payloads.append(json.loads(line))
            except json.JSONDecodeError as exc:
                # Surface this as part of the result rather than raising.
                payloads.append({"__json_error__": f"line {line_no}: {exc}"})
    return validate_events_iter(payloads, source=str(path))
