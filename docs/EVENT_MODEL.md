# Event Model

## 1. Purpose

This document defines the canonical event model for the Autonomous Safety Validation Rover Platform.

Events are the platform's structured record of operationally significant facts: state transitions, sensor health changes, motion arbitration outcomes, fault injections, watchdog expirations, and operator actions. The event stream is the primary input to incident reconstruction, replay timeline analysis, and platform observability.

The event model is an architectural contract. Subsystems that emit events must conform to the schema defined here. Subsystems that consume events (replay, dashboards, analytics) must be able to rely on the contract without negotiating with producers at runtime.

This document does not define the wire transport for events. The wire transport is a deployment concern handled by `rover_observability` and is permitted to evolve, but the schema and the semantics defined here are stable.

---

## 2. Event Design Principles

### 2.1 Events describe facts

An event records something that happened. Events are not control messages. The supervisor does not change state because of an event; it emits an event because it changed state. The arbitration layer does not clamp because of an event; it emits an event because it clamped.

### 2.2 Events are append-only

Events are never updated, never deleted, and never reordered after publication. A correction is itself a new event with an explicit reason.

### 2.3 Events are self-contained

A consumer must be able to interpret an event using only the event itself, plus the schema and the controlled vocabularies defined here. Consumers must not need to query the live system to interpret a recorded event.

### 2.4 Events are replay-grade

Every event must contain enough information to be interpreted long after the run that produced it. This includes timestamps, run identity, scenario identity, subsystem identity, and the safety state at the time of emission.

### 2.5 Events do not replace topics

High-frequency continuous data (sensor scans, raw odometry, raw IMU) belongs on topics and in bag files. Events describe transitions, decisions, and discrete facts. The two are complementary, not interchangeable.

### 2.6 Events do not control safety

Fault injection, sensor adapters, and mission logic emit events. None of them sets `/safety/state` directly. Only the safety supervisor sets `/safety/state`, and it does so based on inputs and watchdogs, not based on events from peers.

---

## 3. Event Envelope Schema

Every event must conform to the following envelope.

### 3.1 Required fields

| Field | Type | Description |
|---|---|---|
| `timestamp` | RFC 3339 string with nanosecond precision, plus a separate `sim_time_ns` if available | Wall-clock time at emission. When the simulator provides `/clock`, both wall and sim time must be present. |
| `run_id` | UUID v4 string | Unique identifier for the operational run. Allocated at run start, stable for the run's duration. |
| `scenario_id` | string | Identifier of the scenario or mission template under test. Stable across runs that exercise the same scenario. |
| `event_id` | UUID v4 string | Unique identifier of this individual event. |
| `event_type` | controlled string | The event type, drawn from the vocabulary in section 5. |
| `severity` | controlled string | One of `DEBUG`, `INFO`, `NOTICE`, `WARNING`, `ERROR`, `CRITICAL`. |
| `subsystem` | controlled string | The owning subsystem, drawn from the controlled list in section 4. |
| `node` | string | The ROS 2 node name that emitted the event. |
| `lifecycle_state` | controlled string | The lifecycle state of the emitting node, e.g. `unconfigured`, `inactive`, `active`, `finalized`. |
| `safety_state` | controlled string | The safety state at the time of emission. One of the values defined in `docs/SAFETY_MODEL.md`. |
| `source_topic` | string \| null | The originating ROS 2 topic, where applicable. Null if not topic-derived. |
| `confidence_score` | float in [0.0, 1.0] \| null | The confidence value associated with the event, where applicable. |
| `requested_motion` | object \| null | The motion request observed at emission, where applicable. Schema in section 3.3. |
| `final_motion` | object \| null | The authorized motion at emission, where applicable. Schema in section 3.3. |
| `reason_code` | controlled string | Stable machine-readable reason. Drawn from the vocabulary in section 6. |
| `message` | string | Human-readable explanation. Not parsed by replay tooling. |

### 3.2 Optional fields

| Field | Type | Description |
|---|---|---|
| `sim_time_ns` | integer | Simulated time in nanoseconds, when `/clock` is available. |
| `correlation_id` | UUID v4 string | Used to group related events across subsystems. See section 7. |
| `parent_event_id` | UUID v4 string | The event that caused this event, if any. |
| `tags` | array of strings | Optional labels for filtering. Free-form but lowercase, dot-separated. |
| `attributes` | object | Subsystem-specific structured payload. Producers must document attributes per `event_type`. |

### 3.3 Motion sub-schema

```json
{
  "linear":  { "x": 0.0, "y": 0.0, "z": 0.0 },
  "angular": { "x": 0.0, "y": 0.0, "z": 0.0 }
}
```

Units are SI: meters per second for linear, radians per second for angular.

---

## 4. Subsystems

Events must declare a `subsystem` from this controlled list:

```text
sensor_adapter
state_estimation
world_model
safety_supervisor
motion_arbitration
mission
hardware_gateway
observability
fault_injection
replay
operator
system_lifecycle
```

A subsystem may host multiple ROS 2 nodes. The `node` field disambiguates which node within the subsystem emitted the event.

---

## 5. Event Categories and Types

`event_type` values are namespaced strings using dot notation. The category prefix must come from this controlled list:

```text
system_lifecycle
sensor_health
state_estimation
safety_transition
motion_arbitration
fault_injection
watchdog
replay
operator_action
```

Recommended `event_type` values:

| Category | Example types |
|---|---|
| `system_lifecycle` | `system_lifecycle.boot`, `system_lifecycle.node_configured`, `system_lifecycle.node_activated`, `system_lifecycle.node_failed` |
| `sensor_health` | `sensor_health.stale`, `sensor_health.recovered`, `sensor_health.disagreement`, `sensor_health.bias_detected` |
| `state_estimation` | `state_estimation.diverged`, `state_estimation.recovered`, `state_estimation.confidence_drop` |
| `safety_transition` | `safety_transition.entered`, `safety_transition.exited`, `safety_transition.refused` |
| `motion_arbitration` | `motion_arbitration.clamped`, `motion_arbitration.dropped`, `motion_arbitration.zeroed` |
| `fault_injection` | `fault_injection.armed`, `fault_injection.fired`, `fault_injection.cleared` |
| `watchdog` | `watchdog.armed`, `watchdog.petted`, `watchdog.expired` |
| `replay` | `replay.started`, `replay.paused`, `replay.completed`, `replay.skipped_topic` |
| `operator_action` | `operator_action.activate`, `operator_action.estop`, `operator_action.reset`, `operator_action.scenario_loaded` |

New types may be added by the owning subsystem. Adding a new category prefix requires updating this document.

---

## 6. Reason Code Strategy

`reason_code` is a stable, machine-readable string. It is the primary index for incident analysis and the most important field for grep-style triage.

Reason codes use lowercase, snake_case, namespaced where helpful. Examples:

```text
stale_lidar
stale_imu
stale_encoders
sensor_disagreement
imu_bias
encoder_drift
bridge_disconnect
command_timeout
watchdog_expiration
gateway_silent
operator_estop
operator_reset
operator_recovery
recovery_validated
recovery_failed
odd_terrain
odd_slope
odd_velocity_clamp
odd_angular_clamp
velocity_clamp
angular_clamp
acceleration_clamp
fault_armed
fault_fired
fault_cleared
boot_timeout
mission_request_rejected
```

Reason codes:

- must be stable across releases. Rename only with a deprecation period.
- are the primary axis for replay queries.
- must be documented in the producing subsystem and listed centrally in `rover_observability`.

A producer must not invent ad-hoc reason codes at runtime. Free-form context belongs in `message` or `attributes`, not in `reason_code`.

---

## 7. Correlation, Run, and Scenario IDs

### 7.1 `run_id`

`run_id` is allocated once per operational run. The run starts when the supervisor leaves `BOOT`. The run ends when the supervisor finalizes or the operator stops the run.

`run_id` is required on every event. It is the primary join key for replay.

### 7.2 `scenario_id`

`scenario_id` identifies the scenario template, not the run. Two runs of the same scenario share `scenario_id` but have different `run_id`s.

`scenario_id` should be human-meaningful, e.g. `lidar_stale_drive_forward_v1`.

### 7.3 `correlation_id`

`correlation_id` groups related events across subsystems within a run.

Examples:

- A LiDAR staleness incident might have a single `correlation_id` shared by:
  - the `sensor_health.stale` event from the sensor adapter
  - the `safety_transition.entered ACTIVE_DEGRADED` event from the supervisor
  - the `motion_arbitration.clamped` events that follow
  - the `safety_transition.entered SAFE_STOP` event if escalation occurs
  - the `sensor_health.recovered` event when the LiDAR returns
  - the `safety_transition.entered RECOVERY` and subsequent transitions

The supervisor is responsible for allocating correlation IDs for safety-driven incidents. Sensor adapters and fault injectors may propose a `correlation_id`, but the supervisor's allocation wins when the supervisor responds to the underlying condition.

### 7.4 `parent_event_id`

`parent_event_id` is the direct cause. Where a single causal chain exists, it should be set. Where the cause is a class of inputs (e.g. multiple stale topics), `parent_event_id` may be omitted and `correlation_id` used instead.

---

## 8. Event Ordering Rules

1. Events are ordered by `(run_id, sim_time_ns)` if `sim_time_ns` is available, otherwise by `(run_id, timestamp)`.
2. Within a single emitting node, events must be emitted in the order in which they occurred.
3. Across nodes, ordering is best-effort. Replay tooling must not assume cross-node real-time ordering at sub-millisecond resolution.
4. The supervisor must emit `safety_transition.entered` before any `motion_arbitration.*` events that occur in the new state.
5. The supervisor must emit `safety_transition.exited` (where used) before `safety_transition.entered` for the next state.

---

## 9. Timestamp Strategy

1. `timestamp` is wall-clock time at emission, RFC 3339 with nanosecond precision and explicit timezone (UTC).
2. `sim_time_ns` is the simulator clock at emission, as nanoseconds since the simulator epoch, when `/clock` is available.
3. Sensor-derived events should also include the source sensor timestamp inside `attributes.source_timestamp_ns`. This allows replay tooling to distinguish "the sensor was stale" from "the event was emitted late."
4. Timestamps are never edited after emission.

---

## 10. Replay Requirements

For an event to be considered replay-grade:

- it must conform to the envelope in section 3
- it must use a known `event_type` from section 5
- it must use a documented `reason_code` from section 6
- it must include `run_id`, `scenario_id`, and `safety_state`
- it must be persisted in `runs/<run_id>/events.jsonl` per `docs/REPLAY_SYSTEM.md`

A subsystem that emits non-conforming events fails replay validation, and the run is treated as non-replayable for that subsystem.

---

## 11. Example Events

### 11.1 Stale LiDAR

```json
{
  "timestamp": "2026-04-12T13:42:18.123456789Z",
  "sim_time_ns": 4218123456789,
  "run_id": "9c7a1f31-3d62-4f7d-a3b1-2c5f7e8a9b10",
  "scenario_id": "indoor_corridor_v3",
  "event_id": "21b6c0a7-2c1f-4ef5-8e0a-1f3a7e9b2d44",
  "event_type": "sensor_health.stale",
  "severity": "WARNING",
  "subsystem": "sensor_adapter",
  "node": "/rover/sensor_adapter_lidar",
  "lifecycle_state": "active",
  "safety_state": "ACTIVE_NORMAL",
  "source_topic": "/scan",
  "confidence_score": null,
  "requested_motion": null,
  "final_motion": null,
  "reason_code": "stale_lidar",
  "message": "LiDAR scan stale beyond 250 ms threshold; last scan age 412 ms",
  "correlation_id": "f3a7c1d4-9c2b-4d1e-a3b1-7e9b2d44ef21",
  "attributes": {
    "expected_period_ms": 100,
    "stale_threshold_ms": 250,
    "observed_age_ms": 412,
    "source_timestamp_ns": 4217711000000
  }
}
```

### 11.2 Degraded-Mode Transition

```json
{
  "timestamp": "2026-04-12T13:42:18.241000000Z",
  "sim_time_ns": 4218241000000,
  "run_id": "9c7a1f31-3d62-4f7d-a3b1-2c5f7e8a9b10",
  "scenario_id": "indoor_corridor_v3",
  "event_id": "8f4e2c0d-7d3a-49b1-b2c0-0a5e1d6c9b3f",
  "event_type": "safety_transition.entered",
  "severity": "WARNING",
  "subsystem": "safety_supervisor",
  "node": "/rover/safety_supervisor",
  "lifecycle_state": "active",
  "safety_state": "ACTIVE_DEGRADED",
  "source_topic": null,
  "confidence_score": 0.62,
  "requested_motion": { "linear": { "x": 0.5, "y": 0.0, "z": 0.0 }, "angular": { "x": 0.0, "y": 0.0, "z": 0.0 } },
  "final_motion":     { "linear": { "x": 0.15, "y": 0.0, "z": 0.0 }, "angular": { "x": 0.0, "y": 0.0, "z": 0.0 } },
  "reason_code": "stale_lidar",
  "message": "Entering ACTIVE_DEGRADED due to LiDAR staleness; clamping linear velocity to degraded limit",
  "correlation_id": "f3a7c1d4-9c2b-4d1e-a3b1-7e9b2d44ef21",
  "parent_event_id": "21b6c0a7-2c1f-4ef5-8e0a-1f3a7e9b2d44",
  "attributes": {
    "from_state": "ACTIVE_NORMAL",
    "to_state": "ACTIVE_DEGRADED",
    "active_limits": { "linear_max": 0.15, "angular_max": 0.3 }
  }
}
```

### 11.3 Safe-Stop

```json
{
  "timestamp": "2026-04-12T13:42:19.011000000Z",
  "sim_time_ns": 4219011000000,
  "run_id": "9c7a1f31-3d62-4f7d-a3b1-2c5f7e8a9b10",
  "scenario_id": "indoor_corridor_v3",
  "event_id": "c4e2d6b1-1a9f-4d2c-9b3e-77a01f2d8c44",
  "event_type": "safety_transition.entered",
  "severity": "ERROR",
  "subsystem": "safety_supervisor",
  "node": "/rover/safety_supervisor",
  "lifecycle_state": "active",
  "safety_state": "SAFE_STOP",
  "source_topic": null,
  "confidence_score": 0.31,
  "requested_motion": { "linear": { "x": 0.5, "y": 0.0, "z": 0.0 }, "angular": { "x": 0.0, "y": 0.0, "z": 0.0 } },
  "final_motion":     { "linear": { "x": 0.0, "y": 0.0, "z": 0.0 }, "angular": { "x": 0.0, "y": 0.0, "z": 0.0 } },
  "reason_code": "stale_lidar",
  "message": "Escalating to SAFE_STOP; LiDAR stale beyond safe-stop threshold",
  "correlation_id": "f3a7c1d4-9c2b-4d1e-a3b1-7e9b2d44ef21",
  "parent_event_id": "8f4e2c0d-7d3a-49b1-b2c0-0a5e1d6c9b3f",
  "attributes": {
    "from_state": "ACTIVE_DEGRADED",
    "to_state": "SAFE_STOP",
    "stale_duration_ms": 893,
    "safe_stop_threshold_ms": 750
  }
}
```

### 11.4 E-Stop Latched

```json
{
  "timestamp": "2026-04-12T13:42:25.500000000Z",
  "sim_time_ns": 4225500000000,
  "run_id": "9c7a1f31-3d62-4f7d-a3b1-2c5f7e8a9b10",
  "scenario_id": "indoor_corridor_v3",
  "event_id": "e02f7c10-c8b2-4a4e-9d1c-2abf09c1a7e5",
  "event_type": "safety_transition.entered",
  "severity": "CRITICAL",
  "subsystem": "safety_supervisor",
  "node": "/rover/safety_supervisor",
  "lifecycle_state": "active",
  "safety_state": "E_STOP_LATCHED",
  "source_topic": "/operator/estop",
  "confidence_score": null,
  "requested_motion": null,
  "final_motion": { "linear": { "x": 0.0, "y": 0.0, "z": 0.0 }, "angular": { "x": 0.0, "y": 0.0, "z": 0.0 } },
  "reason_code": "operator_estop",
  "message": "E_STOP_LATCHED asserted by operator; manual reset required",
  "correlation_id": "9b1d4e6f-2c8a-4f0d-bc31-7e1a4f9a2c10",
  "attributes": {
    "from_state": "SAFE_STOP",
    "to_state": "E_STOP_LATCHED",
    "operator_pathway": "physical_button"
  }
}
```

---

## 12. Schema Versioning

The envelope schema is versioned via the run metadata, not in every event. Run metadata in `runs/<run_id>/metadata.json` records the event schema version. Replay tooling must inspect the run metadata to choose the correct interpretation.

Adding optional fields, new `event_type` values within an existing category, and new `reason_code` values is a non-breaking change.

Removing or renaming required fields, removing or renaming categories, or changing field semantics is a breaking change and requires a schema version bump and an ADR.
