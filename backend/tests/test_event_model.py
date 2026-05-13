"""Tests for the event envelope and schema validator."""

from __future__ import annotations

import json

import pytest

from app.domain.enums import EventCategory, EventSeverity, LifecycleState, SafetyState
from app.domain.events import Event, EventBuilder, REQUIRED_EVENT_FIELDS
from app.domain.identifiers import EventId, RunId, ScenarioId, SequentialIdGenerator
from app.domain.time import ManualClock, Timestamp
from app.telemetry.schemas import EventSchemaError, validate_event_dict


def _build_minimal_event(*, ids: SequentialIdGenerator, clock: ManualClock) -> Event:
    return Event(
        timestamp=clock.stamp(),
        run_id=RunId("run-test"),
        scenario_id=ScenarioId("sc-test"),
        event_id=ids.event_id(),
        event_type="system_lifecycle.boot",
        severity=EventSeverity.INFO,
        subsystem="test_subsystem",
        node="/test/node",
        lifecycle_state=LifecycleState.ACTIVE,
        safety_state=SafetyState.BOOT,
        reason_code="boot",
        message="boot",
    )


def test_required_fields_complete() -> None:
    expected = {
        "timestamp",
        "run_id",
        "scenario_id",
        "event_id",
        "event_type",
        "severity",
        "subsystem",
        "node",
        "lifecycle_state",
        "safety_state",
        "source_topic",
        "confidence_score",
        "requested_motion",
        "final_motion",
        "reason_code",
        "message",
    }
    assert set(REQUIRED_EVENT_FIELDS) == expected


def test_event_serialization_round_trip(manual_clock: ManualClock, id_generator: SequentialIdGenerator) -> None:
    event = _build_minimal_event(ids=id_generator, clock=manual_clock)
    payload = json.loads(event.to_json())
    for field in REQUIRED_EVENT_FIELDS:
        assert field in payload, f"missing {field}"
    assert payload["severity"] == "INFO"
    assert payload["safety_state"] == "BOOT"
    # prev_event_hash is recorder-injected on disk (#13); the in-memory
    # envelope does not carry it. validate_event_dict applies to the
    # on-disk shape, so we inject the genesis hash before validating.
    payload["prev_event_hash"] = "0" * 64
    validate_event_dict(payload)


def test_event_builder_increments_event_ids(
    manual_clock: ManualClock, id_generator: SequentialIdGenerator, run_id, scenario_id
) -> None:
    builder = EventBuilder(
        run_id=run_id,
        scenario_id=scenario_id,
        clock=manual_clock,
        id_generator=id_generator,
        subsystem="test",
        node="/test/node",
    )
    e1 = builder.build(
        event_type="system_lifecycle.boot",
        severity=EventSeverity.INFO,
        reason_code="boot",
        message="one",
    )
    e2 = builder.build(
        event_type="system_lifecycle.boot",
        severity=EventSeverity.INFO,
        reason_code="boot",
        message="two",
    )
    assert e1.event_id != e2.event_id
    assert str(e1.event_id) == "evt-0000000001"
    assert str(e2.event_id) == "evt-0000000002"


def test_invalid_severity_rejected_by_validator() -> None:
    payload = {
        "timestamp": "2026-01-01T00:00:00Z",
        "run_id": "r",
        "scenario_id": "s",
        "event_id": "e",
        "event_type": "system_lifecycle.boot",
        "severity": "PANIC",
        "subsystem": "x",
        "node": "/x",
        "lifecycle_state": "active",
        "safety_state": "BOOT",
        "source_topic": None,
        "confidence_score": None,
        "requested_motion": None,
        "final_motion": None,
        "reason_code": "boot",
        "message": "m",
    }
    with pytest.raises(EventSchemaError):
        validate_event_dict(payload)


def test_unknown_category_rejected() -> None:
    payload = {
        "timestamp": "2026-01-01T00:00:00Z",
        "run_id": "r",
        "scenario_id": "s",
        "event_id": "e",
        "event_type": "made_up.thing",
        "severity": "INFO",
        "subsystem": "x",
        "node": "/x",
        "lifecycle_state": "active",
        "safety_state": "BOOT",
        "source_topic": None,
        "confidence_score": None,
        "requested_motion": None,
        "final_motion": None,
        "reason_code": "boot",
        "message": "m",
    }
    with pytest.raises(EventSchemaError):
        validate_event_dict(payload)


def test_event_type_must_be_dotted() -> None:
    with pytest.raises(ValueError):
        Event(
            timestamp=Timestamp(wall="2026-01-01T00:00:00Z", sim_time_ns=0),
            run_id=RunId("r"),
            scenario_id=ScenarioId("s"),
            event_id=EventId("e"),
            event_type="boot",
            severity=EventSeverity.INFO,
            subsystem="x",
            node="/x",
            lifecycle_state=LifecycleState.ACTIVE,
            safety_state=SafetyState.BOOT,
            reason_code="boot",
            message="m",
        )


def test_confidence_bounds_enforced() -> None:
    with pytest.raises(ValueError):
        Event(
            timestamp=Timestamp(wall="2026-01-01T00:00:00Z", sim_time_ns=0),
            run_id=RunId("r"),
            scenario_id=ScenarioId("s"),
            event_id=EventId("e"),
            event_type="sensor_health.stale",
            severity=EventSeverity.INFO,
            subsystem="x",
            node="/x",
            lifecycle_state=LifecycleState.ACTIVE,
            safety_state=SafetyState.BOOT,
            reason_code="stale_lidar",
            message="m",
            confidence_score=1.5,
        )


def test_all_categories_present() -> None:
    expected = {
        "system_lifecycle",
        "sensor_health",
        "state_estimation",
        "safety_transition",
        "motion_arbitration",
        "fault_injection",
        "watchdog",
        "replay",
        "operator_action",
    }
    assert {c.value for c in EventCategory} >= expected
