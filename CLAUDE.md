You are acting as a principal robotics systems engineer and senior software architect.

You are working inside my existing repository:

`rover-safety-platform`

The repo already contains the foundational authority documents:

- `docs/ARCHITECTURE.md`
- `docs/ODD.md`
- `docs/SAFETY_MODEL.md`
- `docs/EVENT_MODEL.md`
- `docs/FAULT_INJECTION.md`
- `docs/REPLAY_SYSTEM.md`
- `docs/ROADMAP.md`
- `docs/SYSTEM_CONTEXT.md`
- `docs/TESTING_STRATEGY.md`
- `docs/adr/`

Your job is to perform the first substantial implementation pass.

This is NOT a toy rover project.

This is a simulation-first autonomous safety validation platform intended to demonstrate principal-level robotics architecture, deterministic control, fault-aware autonomy, replayable operational state, and safety-supervisor authority.

Do not build shallow demo code.

Do not build UI cosmetics.

Do not add AI, camera perception, SLAM, Jetson-specific code, cloud infrastructure, Kubernetes, or hardware drivers yet.

This pass must build the core software foundation that future ROS 2 / Gazebo integration can plug into.

---

# Primary Goal

Build the first executable core of the platform:

## Phase 1A: Deterministic Autonomy Simulation Core

Implement a substantial, testable backend/domain foundation that models:

- rover state
- motion commands
- sensor readings
- sensor freshness
- confidence scoring
- safety states
- safety transitions
- motion arbitration
- fault injection
- structured event emission
- replay-ready run recording
- deterministic simulation stepping
- scenario execution

The implementation should be large enough and complete enough to become the real foundation for later ROS 2 / Gazebo integration.

Target substantial implementation depth. Do not stop after a thin scaffold. Build meaningful modules, models, tests, and examples.

---

# Hard Rules

1. Read the docs first.
2. Treat the docs as source of truth.
3. Do not contradict `ARCHITECTURE.md`, `SAFETY_MODEL.md`, `EVENT_MODEL.md`, or `FAULT_INJECTION.md`.
4. Mission logic may request motion, but only the safety supervisor may authorize motion.
5. The motor gateway may only receive authorized commands.
6. Fault injection must not directly mutate safety state.
7. Every meaningful safety decision must emit an event.
8. Every simulation run must be replay-addressable by `run_id`.
9. Keep code deterministic and testable.
10. Prefer clean domain models over framework-heavy code.
11. Do not add real ROS 2 dependencies yet unless the repo already has them configured. Build ROS-compatible domain boundaries first.
12. Do not create placeholder files with empty classes just to inflate scope.
13. Do not write vague TODO-only modules.
14. No generated fluff.
15. No runtime code that bypasses tests.

---

# Expected Implementation Scale

This should be a substantial first build pass.

Aim to create a real internal platform foundation across multiple packages/modules, with meaningful tests.

Do not optimize for raw line count, but do not underbuild. A strong implementation here should naturally produce several thousand lines across:

- domain models
- safety supervisor
- motion arbitration
- sensor simulation
- fault injection
- event system
- replay recording
- scenario runner
- tests
- examples
- docs updates

---

# Recommended Backend Structure

If the repo already has a backend structure, adapt carefully.

If not, create this structure:

```text
backend/
  app/
    __init__.py

    domain/
      __init__.py
      enums.py
      identifiers.py
      motion.py
      rover_state.py
      sensors.py
      safety.py
      events.py
      faults.py
      scenarios.py
      replay.py
      time.py

    safety/
      __init__.py
      supervisor.py
      transitions.py
      confidence.py
      freshness.py
      arbitration.py
      watchdog.py

    simulation/
      __init__.py
      engine.py
      vehicle_model.py
      sensor_simulator.py
      scenario_runner.py
      clock.py

    faults/
      __init__.py
      injector.py
      models.py
      profiles.py

    telemetry/
      __init__.py
      event_bus.py
      event_store.py
      schemas.py
      run_recorder.py

    replay/
      __init__.py
      manifest.py
      loader.py
      recorder.py

    api/
      __init__.py
      main.py
      routes/
        __init__.py
        health.py
        simulation.py
        runs.py

  tests/
    test_event_model.py
    test_safety_transitions.py
    test_motion_arbitration.py
    test_freshness_monitoring.py
    test_confidence_scoring.py
    test_fault_injection.py
    test_simulation_engine.py
    test_replay_recorder.py
    test_scenario_runner.py
```

If the repo uses another structure, preserve it unless it conflicts with the docs.

---

# Domain Model Requirements

Implement strong typed domain models using Python.

Use:

- dataclasses or Pydantic models
- enums for controlled states
- explicit validation
- immutable-style behavior where useful
- clear serialization methods
- deterministic timestamps through injectable clock abstraction

Avoid global mutable state.

---

## Required Enums

Create enums for:

```text
SafetyState
LifecycleState
SensorType
SensorStatus
FaultType
FaultStatus
EventSeverity
EventCategory
MotionDecision
MotionConstraintReason
ScenarioStatus
ReplayStatus
```

Safety states must include exactly:

```text
BOOT
INACTIVE
ACTIVE_NORMAL
ACTIVE_RESTRICTED
ACTIVE_DEGRADED
SAFE_STOP
E_STOP_LATCHED
RECOVERY
```

Event severity must include exactly:

```text
DEBUG
INFO
NOTICE
WARNING
ERROR
CRITICAL
```

Event categories must include at least:

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

---

# Motion Model Requirements

Implement models for:

```text
MotionCommand
RequestedMotionCommand
AuthorizedMotionCommand
MotionLimits
MotionArbitrationResult
```

Motion command fields should include:

```text
linear_velocity
angular_velocity
source
issued_at
expires_at
```

Motion arbitration must support:

- full authorization
- restricted authorization
- zero-motion safe stop
- rejection due to stale input
- rejection due to E-stop
- rejection due to degraded confidence
- clamping velocity to restricted limits

---

# Rover State Requirements

Implement a canonical rover state model with:

```text
pose_x
pose_y
heading_rad
linear_velocity
angular_velocity
safety_state
lifecycle_state
last_update
```

Include deterministic update logic for a differential-drive style simplified simulation.

Do not overbuild physics. Keep it deterministic and explainable.

---

# Sensor Model Requirements

Implement sensor models for:

```text
LiDAR
IMU
Wheel Encoder
Contact/Bumper
```

Each reading should include:

```text
sensor_id
sensor_type
timestamp
status
confidence
data
source
sequence_number
```

Implement freshness evaluation:

```text
is_fresh(reading, now, max_age_ms)
```

Implement confidence evaluation rules:

- stale readings reduce confidence
- missing required readings reduce system confidence
- contradictory distance readings produce disagreement
- IMU/encoder divergence produces disagreement
- contact/bumper activation produces high-priority safety signal

Do not use ML.

This pass is deterministic validation only.

---

# Safety Supervisor Requirements

Implement a real safety supervisor.

It must:

- maintain current safety state
- evaluate sensor freshness
- evaluate sensor confidence
- evaluate disagreement
- evaluate active faults
- evaluate command freshness
- decide next safety state
- authorize or reject motion
- emit structured events for transitions
- enforce safe-stop
- enforce E-stop latch
- require explicit reset from E-stop
- support recovery validation

---

## Safety Transition Expectations

Implement transition logic for at least:

```text
BOOT -> INACTIVE
INACTIVE -> ACTIVE_NORMAL
ACTIVE_NORMAL -> ACTIVE_RESTRICTED
ACTIVE_NORMAL -> ACTIVE_DEGRADED
ACTIVE_RESTRICTED -> ACTIVE_DEGRADED
ACTIVE_DEGRADED -> SAFE_STOP
ACTIVE_NORMAL -> SAFE_STOP
ACTIVE_RESTRICTED -> SAFE_STOP
SAFE_STOP -> RECOVERY
RECOVERY -> ACTIVE_NORMAL
ANY -> E_STOP_LATCHED
```

Prevent invalid transitions.

Invalid transitions must emit an event or return a clear rejection reason.

---

# Fault Injection Requirements

Implement deterministic fault injection.

Fault injection must alter inputs, timing, or simulated sensor outputs.

It must NOT directly set safety state.

Required fault classes:

```text
stale_lidar
encoder_drift
imu_bias
bridge_disconnect
command_timeout
watchdog_expiration
packet_delay
sensor_disagreement
wheel_slip
```

For each fault, implement:

- fault profile model
- activation time
- duration
- target sensor/subsystem
- deterministic effect
- event emission
- deactivation behavior

Examples:

- `stale_lidar` stops updating LiDAR readings.
- `encoder_drift` modifies encoder delta.
- `imu_bias` biases heading.
- `packet_delay` shifts timestamps.
- `sensor_disagreement` forces LiDAR and ultrasonic/proximity readings apart.
- `command_timeout` causes requested command expiration.
- `watchdog_expiration` simulates missed heartbeat.

---

# Event System Requirements

Implement canonical structured events matching `docs/EVENT_MODEL.md`.

Required event fields:

```text
timestamp
run_id
scenario_id
event_id
event_type
severity
subsystem
node
lifecycle_state
safety_state
source_topic
confidence_score
requested_motion
final_motion
reason_code
message
```

Implement:

- event factory helpers
- JSON serialization
- event validation
- event bus
- in-memory event store
- JSONL writer for run recording

Events must be emitted for:

- system startup
- scenario start
- scenario completion
- fault injection activation
- fault injection deactivation
- sensor stale detection
- confidence degradation
- safety transition
- motion arbitration
- safe-stop
- E-stop latch
- recovery attempt
- replay recording start/stop

---

# Replay Recording Requirements

Implement a replay-ready run recorder.

Use local filesystem storage.

Proposed structure:

```text
runs/
  <run_id>/
    metadata.json
    events.jsonl
    states.jsonl
    commands.jsonl
    sensor_readings.jsonl
    incident-summary.md
```

Implement:

- run creation
- metadata writing
- append event
- append state
- append command
- append sensor reading
- incident summary generation
- deterministic run IDs or injectable run ID generation for tests

Do not implement rosbag2 yet.

But design the recorder so rosbag2 / MCAP can be added later.

---

# Simulation Engine Requirements

Implement a deterministic simulation engine.

It should support:

- fixed timestep
- injectable clock
- rover state update
- sensor generation
- fault application
- safety supervisor evaluation
- motion arbitration
- run recording
- event emission
- scenario completion

The engine should support a scenario definition such as:

```json
{
  "scenario_id": "stale-lidar-safe-stop-demo",
  "duration_seconds": 30,
  "time_step_ms": 100,
  "initial_state": {},
  "requested_motion": {},
  "faults": []
}
```

Implement several example scenario profiles in code or JSON:

```text
nominal_run
stale_lidar_restricted_mode
odometry_divergence_safe_stop
command_timeout_safe_stop
estop_latched_manual_reset_required
```

---

# API Requirements

If FastAPI is already present, integrate lightly.

If not present, add a minimal FastAPI app only if dependency files already support it or can be safely updated.

API should include:

```text
GET /health
POST /simulation/run
GET /runs
GET /runs/{run_id}
GET /runs/{run_id}/events
GET /runs/{run_id}/summary
```

Do not build frontend in this pass.

The API should call real simulation services, not dummy placeholders.

---

# Testing Requirements

Build a meaningful test suite.

Tests must verify:

## Event Model
- required fields exist
- JSON serialization works
- invalid severity fails
- event IDs are unique or deterministic under injected generator

## Safety Transitions
- valid transitions succeed
- invalid transitions fail
- E-stop latches
- E-stop cannot self-clear
- recovery requires valid streams

## Motion Arbitration
- normal state authorizes request
- restricted state clamps velocity
- safe-stop forces zero
- E-stop forces zero
- expired command rejected

## Freshness Monitoring
- stale LiDAR detected
- missing required sensor reduces confidence
- packet delay triggers stale reading

## Confidence Scoring
- healthy sensors produce high confidence
- stale sensor lowers confidence
- disagreement lowers confidence
- bumper/contact trigger escalates

## Fault Injection
- faults alter inputs but do not directly set safety state
- stale_lidar produces stale sensor event
- encoder_drift creates odometry divergence
- command_timeout expires command

## Simulation Engine
- nominal scenario completes
- stale LiDAR scenario transitions out of normal
- odometry divergence reaches safe-stop
- E-stop scenario latches
- run recorder writes expected files

## Replay Recorder
- creates run directory
- writes metadata
- writes events.jsonl
- writes state/command/sensor files
- writes incident summary

---

# Documentation Updates Required

After implementation, update docs only where necessary:

- `docs/ROADMAP.md`: mark Phase 1A foundation as implemented or partially implemented.
- `docs/TESTING_STRATEGY.md`: add implemented test categories.
- `docs/EVENT_MODEL.md`: align any final event field names.
- `docs/FAULT_INJECTION.md`: align fault class names if needed.

Do not rewrite all docs unnecessarily.

---

# Quality Requirements

Code should be:

- typed
- readable
- deterministic
- testable
- modular
- boring where safety matters
- explicit about tradeoffs

Avoid:

- clever abstractions
- hidden global state
- uncontrolled async behavior
- random timestamps in tests
- silent failures
- broad exception swallowing
- direct safety-state mutation by faults
- planner-direct actuator authorization

---

# Acceptance Criteria

This pass is complete only if:

1. The platform has a working deterministic simulation core.
2. Safety supervisor authority is enforced.
3. Motion requests are separated from authorized commands.
4. Fault injection exists and does not directly mutate safety state.
5. Events are emitted for safety-relevant behavior.
6. Run recording writes replay-ready artifacts.
7. Multiple scenario profiles can execute.
8. Tests cover safety transitions, faults, events, replay, and simulation.
9. Docs remain consistent with implementation.
10. The implementation is substantial, not a thin placeholder scaffold.

---

# Final Response Required

When finished, report:

- files created
- files modified
- approximate LOC added
- tests added
- tests passing or failing
- major architectural decisions made
- known limitations
- recommended next implementation phase

Do not claim completion if tests fail.
Do not hide partial implementation.
Do not add unrelated features.
