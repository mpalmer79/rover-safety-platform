"""Deterministic event factory.

Event ids and timestamps are derived from the rehearsal seed so two
runs of the same request produce identical events. ``event_time_ns``
counts from 0 in 100 ms steps; the test suite compares event
streams without depending on wall-clock time.
"""

from __future__ import annotations

import hashlib
import json
from typing import Mapping

from .models import MissionRehearsalEvent


_BASE_TICK_NS: int = 100_000_000  # 100 ms per logical tick


def deterministic_hash(payload: Mapping[str, object]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:16]


def build_event(
    *,
    mission_id: str,
    sequence: int,
    event_type: str,
    event_subtype: str,
    source_phase: str,
    severity: str,
    description: str,
    payload: Mapping[str, object] | None = None,
) -> MissionRehearsalEvent:
    payload_dict = dict(payload or {})
    full = {
        "mission_id": mission_id,
        "sequence": sequence,
        "event_type": event_type,
        "event_subtype": event_subtype,
        "source_phase": source_phase,
        "severity": severity,
        "description": description,
        "payload": payload_dict,
    }
    event_id = f"{mission_id}-evt-{sequence:04d}"
    return MissionRehearsalEvent(
        event_id=event_id,
        mission_id=mission_id,
        event_type=event_type,
        event_subtype=event_subtype,
        event_time_ns=sequence * _BASE_TICK_NS,
        source_phase=source_phase,
        severity=severity,
        description=description,
        deterministic_hash=deterministic_hash(full),
        payload=payload_dict,
    )
