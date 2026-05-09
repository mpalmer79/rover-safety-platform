# Replay and Incident Reconstruction System

## 1. Purpose

This document defines the replay and incident reconstruction architecture for the Autonomous Safety Validation Rover Platform.

Replay is a platform requirement, not a debugging convenience. The platform succeeds only when degraded behavior is bounded, explainable, and replayable. The replay subsystem is the artifact that makes "replayable" measurable.

The replay system spans recorded sensor and control data (rosbag2 / MCAP), a structured event index (the canonical event stream), trace data (`ros2_tracing` outputs where collected), and a visualization layer (Foxglove). The combination supports incident reconstruction, post-run analysis, regression replay, and reviewer-facing portfolio artifacts.

---

## 2. Replay Goals

The replay system is designed to support:

1. **Incident reconstruction** — given a `run_id`, a reviewer can reconstruct what happened, in what order, and why the safety supervisor took the actions it took.
2. **Regression replay** — a recorded scenario can be re-run against a new build and validated against expected events and state transitions.
3. **Operator review** — a reviewer can scrub through a run on a synchronized timeline showing sensor data, motion arbitration, and safety state.
4. **Causality analysis** — events can be filtered by `reason_code`, `correlation_id`, and `safety_state` to identify the cause of a transition.
5. **Determinism evaluation** — repeated runs of a pinned scenario can be compared at the event level to detect non-determinism.

---

## 3. Replay Non-Goals

The replay system does not:

- replay against live hardware as a control loop. Replay is read-only with respect to the rover.
- guarantee bit-exact physics reproduction across simulator versions or operating system versions.
- replace `ros2 bag play` for low-level topic playback in development. It uses bag playback as a primitive.
- run faster than real time on commodity hardware as a hard requirement. Where feasible, replay should support faster-than-real-time analysis, but this is best-effort.
- attempt to reconstruct safety state from the event stream during live operation. The supervisor is the source of truth for safety state during a run.

---

## 4. Components

### 4.1 rosbag2 / MCAP

`rosbag2` with the MCAP storage plugin is the recording substrate for ROS 2 topic data.

Roles:

- record the topics required for replay (see section 7)
- preserve message timestamps and message types via the type registry
- be portable across machines (single MCAP file per bag where practical)

Reasons for MCAP:

- self-describing schemas
- broad tooling support, including Foxglove
- good compression characteristics
- single-file artifacts simplify handoff and archival

### 4.2 Structured Event Index

The event stream defined in `docs/EVENT_MODEL.md` is the canonical record of operationally significant facts. It is recorded as `events.jsonl`, one JSON object per line, in the run's storage directory.

Roles:

- act as the primary index for incident analysis
- be human-readable and grep-friendly
- be append-only and replay-safe
- be parsable without the bag, so a reviewer can triage incidents from text alone

### 4.3 ros2_tracing

`ros2_tracing` produces low-level execution traces. It is enabled selectively, not on every run. When enabled, traces are stored alongside the bag.

Roles:

- support deep concurrency analysis
- support callback-ordering investigations
- support latency studies for control loops

`ros2_tracing` is an optional component; runs without traces are still valid for replay.

### 4.4 Foxglove

Foxglove is the primary visualization layer for replayed and live data.

Roles:

- present synchronized timelines of bag topics and event streams
- host saved layouts that show safety state, motion arbitration, sensor health, and active faults side by side
- support reviewer scrubbing and annotation

Foxglove's role is presentation. It is not the source of truth for any data and may be replaced or supplemented without changing the replay contract.

### 4.5 Replay tooling (`rover_observability`)

A small set of tooling under `rover_observability` is responsible for:

- managing run directories
- generating `metadata.json` per run
- emitting event-stream summaries
- validating event stream conformance against `docs/EVENT_MODEL.md`
- producing incident summaries when invoked

---

## 5. Replay Timeline Model

The replay timeline has three primary axes:

| Axis | Source | Use |
|---|---|---|
| Wall-clock time | event `timestamp` | Operator-facing clock. Cross-machine alignment. |
| Simulated time | event `sim_time_ns`, bag header timestamps | Primary axis for replay where the simulator publishes `/clock`. |
| Event sequence | `event_id` ordering by `(run_id, sim_time_ns)` | Deterministic ordering for incident analysis. |

Replays should default to simulated time when present. Where the simulator did not publish `/clock` (e.g., bench hardware bring-up), wall-clock time is used and labeled as such in the run's `metadata.json`.

Synchronization between bag data and the event stream is performed by the supervisor's emission of `safety_transition.*` events, which carry both `timestamp` and `sim_time_ns`. Foxglove layouts use the event stream as the alignment marker.

---

## 6. Deterministic Replay Limits

Deterministic replay is a goal, not an absolute guarantee.

The replay system is designed to be deterministic to within the following limits:

| Aspect | Determinism |
|---|---|
| Event ordering by `sim_time_ns` | Stable across replays of the same recorded run |
| Event causality (`correlation_id`, `parent_event_id`) | Stable across replays of the same recorded run |
| Bag playback timing | Stable to within the bag's recorded timestamps |
| Simulator physics | Best-effort; reproducible across runs of the same pinned simulator and world, but not guaranteed across simulator versions |
| Threading and callback order | Best-effort; subject to ROS 2 executor and DDS scheduling. `ros2_tracing` may be required to investigate variance. |
| Wall-clock alignment | Not guaranteed across machines. Use `sim_time_ns` for cross-machine analysis. |

When determinism limits are exceeded, the replay tooling must flag the run with a `replay.skipped_topic` or `replay.degraded` event in the run's analysis output.

---

## 7. Required Recorded Topics

A run is replay-eligible if and only if it records the following topics:

```text
/sensor/lidar or /scan
/odom
/imu
/tf
/tf_static
/cmd_vel_requested
/cmd_vel_authorized
/safety/state
/safety/events
/faults/injected
/mission/status
```

Notes:

- `/safety/events` is the on-wire publication of structured events. The same events must also be persisted to `events.jsonl` for grep-friendly inspection.
- `/scan` is the standard ROS 2 LiDAR topic name. Sensor adapters may use `/sensor/lidar`; either is acceptable, but the same name must be used consistently within a run.
- `/clock` must be recorded when the simulator publishes it.
- Additional topics are permitted and encouraged where they aid analysis. Recording must be configured per scenario.

A run that omits any required topic is treated as non-replay-eligible. Such runs are still useful for live debugging but cannot be used for incident reconstruction or regression replay.

---

## 8. Required Recorded Events

A run is replay-eligible if and only if its event stream contains, at minimum:

| Event Class | When Required |
|---|---|
| `system_lifecycle.boot` | At supervisor boot |
| `system_lifecycle.node_*` | For every safety-relevant lifecycle transition |
| `safety_transition.entered` | For every state transition |
| `motion_arbitration.*` | For every clamp, drop, or zero |
| `sensor_health.*` | For every freshness or disagreement event |
| `watchdog.expired` | For every watchdog expiration |
| `fault_injection.*` | For every fault arming, firing, and clearing |
| `operator_action.*` | For every operator E-stop, reset, activation, or scenario load |

A run that lacks `safety_transition.entered` events corresponding to observed `/safety/state` transitions is invalid.

---

## 9. Storage Layout

Each run produces a directory under `runs/`:

```text
runs/
  <run_id>/
    metadata.json
    events.jsonl
    bags/
    traces/
    foxglove-layout.json
    incident-summary.md
```

### 9.1 `metadata.json`

Contains:

- `run_id`
- `scenario_id`
- start and end timestamps (wall and sim)
- supervisor version, fault subsystem version, simulator version
- rover description hash
- world hash
- event schema version
- list of recorded topics
- list of armed faults at scenario start
- declared determinism level (`pinned`, `best_effort`, `unknown`)

### 9.2 `events.jsonl`

The structured event stream as defined in `docs/EVENT_MODEL.md`. One JSON object per line. Append-only.

### 9.3 `bags/`

The rosbag2 / MCAP files for the run. May be a single MCAP file per run, or split per topic group if size warrants.

### 9.4 `traces/`

`ros2_tracing` outputs when collected. Optional.

### 9.5 `foxglove-layout.json`

A saved Foxglove layout configured for this scenario. Reviewers open this layout against the bag and event stream to inspect the run.

### 9.6 `incident-summary.md`

A reviewer-readable summary generated by replay tooling. It must include:

- run identity (`run_id`, `scenario_id`)
- run duration
- final safety state
- list of `safety_transition.entered` events with timestamps and reason codes
- list of fired faults
- list of watchdog expirations
- top-level "what happened" narrative grouped by `correlation_id`

The narrative is generated mechanically from the event stream. It is not a free-form text artifact.

---

## 10. Incident Reconstruction Workflow

A reviewer reconstructing an incident follows this workflow:

1. Locate the run directory by `run_id`.
2. Open `incident-summary.md` for context.
3. Inspect `events.jsonl` filtered by `correlation_id` of interest.
4. Open `bags/` in Foxglove using `foxglove-layout.json`.
5. Use the event stream to align Foxglove playback to the moment of interest.
6. Inspect motion topics: `/cmd_vel_requested`, `/cmd_vel_authorized`, `/safety/state`.
7. Inspect sensor topics: `/scan`, `/imu`, `/odom`.
8. Cross-check fault timeline against `/faults/injected` and `fault_injection.*` events.
9. If concurrency analysis is needed, load `traces/` in the `ros2_tracing` analysis tools.
10. Capture findings in a separate document; do not mutate the run directory.

---

## 11. Replay Acceptance Criteria

A subsystem is considered to "participate in replay" only if all of the following hold:

1. Its outputs that are required for replay (per section 7) are recorded by default.
2. Its operationally significant facts are emitted as events conforming to `docs/EVENT_MODEL.md`.
3. Its events use stable `reason_code` values.
4. Its events include `run_id`, `scenario_id`, `safety_state`, and `correlation_id` where applicable.
5. A pinned scenario re-run produces the same event sequence within deterministic replay limits.
6. Its data is consumable in Foxglove via the saved layout for the relevant scenario.

A subsystem that does not satisfy these criteria is not considered complete, regardless of its functional behavior.

---

## 12. Replay Tooling Requirements

The `rover_observability` package must provide:

- a CLI that allocates a `run_id` and creates the run directory at run start
- a CLI that finalizes a run, writes `metadata.json`, and generates `incident-summary.md`
- a validator that asserts an `events.jsonl` conforms to `docs/EVENT_MODEL.md`
- a validator that asserts a run directory contains all required topics and events
- a CLI that filters events by `correlation_id`, `reason_code`, or `safety_state`

Validators must be runnable in CI against representative recorded runs.

---

## 13. Storage and Retention

Run storage is local-first. The MVP does not require cloud storage.

Recommended practices:

- store runs under a top-level `runs/` directory in a separate filesystem mount when bench testing
- retain runs that are referenced by tests, ADRs, or incident analyses indefinitely
- retain other runs for at least the lifetime of the active development branch
- compress `bags/` for long-term retention
- never delete a run directory referenced by an `incident-summary.md` in a published artifact

Cloud or shared-storage policies are out of scope for this document and are deferred until the platform has a hardware deployment that requires them.
