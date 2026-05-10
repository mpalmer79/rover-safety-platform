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
4. Open `bags/` in Foxglove using
   `foxglove/layouts/incident-review-layout.json`
   (canonical layout shipped with the repo from Phase 6).
5. Use the event stream to align Foxglove playback to the moment of interest.
6. Inspect motion topics: `/cmd_vel_requested`, `/cmd_vel_authorized`, `/safety/state`.
7. Inspect sensor topics: `/scan`, `/imu`, `/odom`.
8. Cross-check fault timeline against `/faults/injected` and `fault_injection.*` events.
9. If concurrency analysis is needed, load `traces/` in the `ros2_tracing` analysis tools.
10. Capture findings in a separate document; do not mutate the run directory.

The Phase 6 incident analysis layer
(`backend/app/incident_analysis/`) automates steps 1–8: loading
evidence, normalising events, building a deterministic timeline,
reconstructing causality with explicit confidence levels, and
emitting Markdown + JSON reports plus Foxglove replay hints under
`incidents/<incident_id>/`. See
[docs/INCIDENT_RECONSTRUCTION.md](INCIDENT_RECONSTRUCTION.md) and
[docs/FOXGLOVE_REPLAY_WORKFLOW.md](FOXGLOVE_REPLAY_WORKFLOW.md).

The Phase 7 replay review layer
(`backend/app/replay_review/`) extends the incident bundle with a
replay manifest, marker file, Foxglove session metadata, and
replay-review report. The layer is read-only with respect to
runtime evidence and rosbag2 artefacts; missing bags are reported as
`missing_bag`, static-only incidents stay `static_only`, and the
Foxglove session JSON is explicitly labelled internal
(`rover-replay-review/1`) — not an official Foxglove import. See
[docs/REPLAY_REVIEW_RUNBOOK.md](REPLAY_REVIEW_RUNBOOK.md).

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

---

## 14. Phase 1B ROS 2 / Gazebo Wiring

Phase 1B implements the replay contract on the ROS 2 side without
relaxing it. Concretely:

| Concern | Phase 1B implementation |
|---|---|
| Run lifecycle | `rover_observability/run_manager.py` allocates `run_id`, creates the run directory, publishes `ReplayMarker` records on `/replay/markers`, and finalises the recorder on shutdown. |
| Structured event index | `rover_safety_bridge/safety_bridge_node.py` publishes canonical-JSON events on `/safety/events`. `rover_observability/event_recorder.py` validates each line against `app.telemetry.schemas.validate_event_dict` and appends it to `runs/<run_id>/events.jsonl`. |
| rosbag2 / MCAP | `rover_observability/observability.launch.py` invokes `ros2 bag record -s mcap` against the topics enumerated in section 7. The bag is written to `runs/<run_id>/bags/`. |
| Run directory layout | Identical to section 9 (`metadata.json`, `events.jsonl`, `bags/`, `traces/`, `incident-summary.md`). The recorder is the same `app.replay.RecorderFacade` used by the deterministic engine. |
| Determinism level | Recorded as `pinned` when the launch was driven by a pinned scenario file; otherwise `best_effort`. |

Run directories produced by the deterministic Python engine and by the
ROS 2 launch are interchangeable as far as the replay validators are
concerned: the metadata schema, event schema, and storage layout are
identical.

---

## 15. Phase 1C Replay Integrity Validation

Phase 1C operationalises the replay contract through executable
validators. Every claim made in this document has a corresponding
check.

| Validator | What it asserts | How to run |
|---|---|---|
| `app.validation.replay_validator.validate_run_directory` | Run directory layout (section 9), `metadata.json` schema, every line of `events.jsonl` validates against `app.telemetry.schemas.validate_event_dict`, per-producer event ordering, `parent_event_id` resolution within the run. | `python tools/validate_replay_run.py <runs/<run_id>>` |
| `app.validation.event_validator.validate_events_file` | Canonical event envelope on every line; rejects duplicate `event_id` values. | `python tools/validate_event_integrity.py <events.jsonl>` |
| `app.validation.scenario_suite.run_scenario_suite` | Each of the seven Phase 1C scenarios produces a replay-validated run directory with the documented final state. | `python tools/run_scenario_suite.py <runs_root>` |
| `app.validation.bridge_validator.validate_bridge_yaml` | The bridge YAML conforms to ADR-004 (only `/cmd_vel_authorized` ROS_TO_GZ; no `/cmd_vel*` forwarding). | `python tools/validate_bridge_topics.py <bridge.yaml>` |
| `app.validation.tf_validator.validate_urdf_tf_tree` | URDF link/joint topology is a single connected tree rooted at `base_footprint`. | `python tools/validate_tf_tree.py <rover.urdf.xacro>` |
| `app.validation.safety_pipeline_validator.validate_safety_pipeline` | Six in-process supervisor invariants. | `python tools/validate_safety_pipeline.py` |

These tools run without ROS 2 or Gazebo; they exercise the
deterministic engine and the static artefacts in the workspace. The
ROS 2 path produces interchangeable run directories that pass the same
validators. A run is considered replay-eligible only when every
applicable validator returns OK.

---

## 16. Phase 2 Mission Replay Artefacts

Phase 2 adds four new JSONL streams to the run directory layout. The
recorder writes them on every run (with zero records when no mission
is configured), so replay tooling can rely on their presence:

| Stream | Producer | Purpose |
|---|---|---|
| `mission_state_transitions.jsonl` | `MissionOrchestrator` (via `mission_lifecycle.entered` events) | One row per mission state transition (`MISSION_IDLE` → `MISSION_PREPARING` → … → `MISSION_COMPLETE` / `MISSION_ABORTED`) with `from_state`, `to_state`, `reason_code`. |
| `waypoint_events.jsonl` | `MissionOrchestrator` (via `mission_waypoint.*` events) | `mission_waypoint.activated` / `.completed` / `.timed_out` rows with `waypoint_id`, `elapsed_ms`. |
| `recovery_events.jsonl` | `RecoveryPolicy` (via `mission_recovery.engaged` / `mission_recovery.cleared`) | One row per recovery transition with `recovery_behavior`, `attempt_count`, `waypoint_id`. |
| `world_model_snapshots.jsonl` | `WorldModel` | One row per recording tick with pose, forward-clearance summary, inside/near keepout, inside restricted, boundary violations, and effective speed limits. |

The validator `app.validation.mission_validator.validate_mission_run`
extends `validate_run_directory` with mission-side checks: every
mission state value must come from the controlled vocabulary in
`app.mission.enums`; every recovery behaviour must come from
`RecoveryBehavior`; per-stream sim_time_ns must be monotonic; every
world-model snapshot must carry the documented set of keys.

`tools/validate_mission_run.py` is the CLI entry point; it accepts
`--json` and exits non-zero on failure. The Phase 1C validators
(replay, events, bridge YAML, TF tree, safety pipeline) all continue
to apply unchanged — Phase 2 is additive.

The incident summary now includes a Mission lifecycle section listing
every transition with its reason code, a Waypoints section with
completed and timed-out lists, and a Recovery engagements section
listing each behavioural change.
