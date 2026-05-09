You are acting as a Principal Robotics Runtime Engineer and Autonomous Systems Validation Architect operating at the level of an advanced robotics R&D organization.

You are continuing work on:

# Project Boundary
## Deterministic Autonomy Validation & Safety Orchestration Platform

The repository already contains:

- architecture authority documents
- deterministic autonomy runtime
- safety supervisor
- motion arbitration
- replay/event system
- fault injection framework
- ROS 2 Jazzy workspace
- Gazebo Harmonic integration
- rover URDF/Xacro
- ros_gz_bridge configuration
- simulated sensors
- structured launch hierarchy
- observability infrastructure
- replay-aware run recording
- static validation tests

This pass is NOT a feature-expansion phase.

This pass is:

# Phase 1C
## Runtime Validation, Operational Hardening, and Integration Verification

The objective is to transform the current ROS/Gazebo integration from:
- structurally correct

into:
- operationally trustworthy
- runtime validated
- replay verified
- diagnostically observable
- integration hardened

This is a critical phase.

Most robotics projects fail here because:
- launch systems drift
- TF trees become inconsistent
- bridges silently fail
- safety authority gets bypassed
- replay becomes nondeterministic
- observability collapses under runtime complexity

Your job is to aggressively validate and harden the existing architecture WITHOUT introducing unnecessary new systems.

---

# Primary Objective

Perform a comprehensive runtime-hardening pass across:

- ROS 2 launch orchestration
- Gazebo integration
- TF consistency
- ros_gz_bridge reliability
- safety-command routing
- sensor freshness propagation
- replay/run recording
- event integrity
- fault injection execution
- observability validation
- deterministic startup sequencing
- runtime diagnostics
- operational visibility

This phase should make the platform:
- demonstrably robust
- diagnostically transparent
- operationally explainable

---

# Hard Constraints

DO NOT:
- add SLAM
- add Nav2 autonomy behaviors yet
- add camera pipelines
- add computer vision
- add ML
- add perception stacks
- add Jetson dependencies
- add Isaac Sim
- add cloud robotics
- add Kubernetes
- add web UI cosmetics
- add unrelated features

DO NOT:
- replace existing architecture
- rewrite working domain logic
- duplicate safety logic
- bypass replay/event systems
- bypass motion arbitration

The current architecture is already correct.

This phase is about:
- runtime verification
- integration rigor
- operational trustworthiness

---

# Critical Engineering Goals

You must validate and harden:

1. Gazebo launch stability
2. ROS graph consistency
3. TF tree integrity
4. Topic freshness semantics
5. Motion authorization path
6. ros_gz_bridge correctness
7. Fault propagation behavior
8. Replay recording correctness
9. Event emission completeness
10. Startup/shutdown sequencing
11. Failure observability
12. Deterministic runtime behavior

---

# Required Work Categories

# 1. Runtime Launch Validation

Audit and harden all launch files.

Required launch files:

```text
simulation.launch.py
rover_spawn.launch.py
observability.launch.py
safety_runtime.launch.py
full_system.launch.py
```

Goals:
- deterministic startup ordering
- clean shutdown handling
- dependency-aware bringup
- launch argument validation
- namespace consistency
- clock synchronization validation
- reusable launch composition

Add:
- launch-time diagnostics
- missing dependency warnings
- bridge availability checks
- runtime readiness validation

---

# 2. Gazebo Runtime Hardening

Audit:
- Gazebo world
- rover spawning
- sensor plugins
- differential drive plugin
- update rates
- frame naming
- collision geometry
- inertial properties

Validate:
- stable spawn behavior
- correct physics stepping
- repeatable startup
- consistent wheel behavior
- stable sensor publishing

Add:
- runtime assertions where appropriate
- simulation configuration documentation
- deterministic simulation notes

Do NOT overcomplicate the world.

This is still:
- a validation platform
- not a photorealistic environment

---

# 3. TF Tree Validation

This is one of the most important phases.

Audit and validate:
- base_link
- odom
- lidar_link
- imu_link
- wheel links
- wheel joints

Validate:
- no disconnected frames
- no duplicate publishers
- no unstable transforms
- no naming inconsistencies

Add:
- TF validation tooling/scripts
- TF documentation
- TF topology diagrams

Implement runtime validation checks if reasonable.

---

# 4. Motion Authorization Hardening

Critically validate:

```text
/cmd_vel_requested
↓
Safety Supervisor
↓
Motion Arbitration
↓
/cmd_vel_authorized
↓
Gazebo Diff Drive
```

The rover must NEVER consume:
- raw requested motion

directly.

Implement:
- runtime checks
- assertions
- diagnostics
- tests

to prove:
- only authorized commands reach actuators
- safe-stop forces zero motion
- E-stop fully inhibits motion
- expired commands are rejected

Add explicit logging/events for:
- rejected commands
- clamped commands
- stale commands
- E-stop inhibition

---

# 5. ros_gz_bridge Hardening

Audit all bridge configuration.

Validate:
- message type alignment
- QoS compatibility
- bridge startup ordering
- topic direction correctness
- clock synchronization
- TF propagation

Required bridged topics:

```text
/clock
/cmd_vel_authorized
/odom
/tf
/tf_static
/scan
/imu
/contact
```

Add:
- bridge validation tooling
- diagnostics output
- bridge failure detection
- bridge timeout warnings

Detect:
- missing topics
- bridge startup failures
- stale bridge traffic

---

# 6. Sensor Pipeline Validation

Audit all sensor adapters.

Validate:
- timestamp propagation
- freshness semantics
- confidence propagation
- sequence handling
- replay metadata
- event generation

Sensors:

```text
LiDAR
IMU
Wheel Odometry
Contact/Bumper
```

Implement:
- runtime freshness monitors
- adapter diagnostics
- stale sensor detection events
- sensor-rate validation
- adapter integration tests

Ensure:
- adapters remain non-authoritative
- safety logic remains centralized

---

# 7. Fault Injection Runtime Integration

Deeply validate fault behavior in live simulation.

Faults:

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

For each fault:
- validate activation
- validate propagation
- validate observability
- validate replay capture
- validate safety response

Ensure:
- faults alter inputs/timing only
- faults do NOT directly mutate safety state

Add:
- runtime fault status visibility
- fault diagnostics
- replay markers
- fault lifecycle events

---

# 8. Replay & Recording Validation

Audit replay recording architecture.

Validate:
- run folder creation
- metadata integrity
- event integrity
- replay marker integrity
- recording startup/shutdown
- rosbag2 recording integration

Required structure:

```text
runs/
  <run_id>/
    metadata.json
    events.jsonl
    states.jsonl
    commands.jsonl
    sensor_readings.jsonl
    bags/
    traces/
    incident-summary.md
```

Add:
- integrity validation scripts
- replay manifest validation
- recording diagnostics
- run summary generation improvements

Validate:
- replay artifacts are complete
- timestamps are coherent
- event ordering is stable

---

# 9. Observability Hardening

This is a major priority.

Audit:
- topic naming
- telemetry consistency
- event visibility
- replay visibility
- health visibility

Add:
- runtime diagnostics topics
- health heartbeat topics
- subsystem status topics
- launch-time health reports
- safety-state visibility
- fault-state visibility

Ensure:
- Foxglove workflows remain coherent
- telemetry is operationally useful
- events are traceable across subsystems

---

# 10. Runtime Diagnostics System

Implement a dedicated diagnostics subsystem.

Suggested package:

```text
rover_runtime_diagnostics
```

Responsibilities:
- topic freshness auditing
- bridge health auditing
- safety-state monitoring
- TF validation
- launch validation
- subsystem heartbeat monitoring
- event-rate monitoring

Publish:
- structured diagnostics
- warnings
- health summaries

This should feel like:
- internal robotics runtime tooling

NOT:
- debug print statements

---

# 11. Scenario Validation Suite

Expand scenario execution validation.

Required runtime scenarios:

```text
nominal_run
stale_lidar_restricted_mode
odometry_divergence_safe_stop
command_timeout_safe_stop
bridge_disconnect_safe_stop
wheel_slip_degraded_mode
estop_latched_manual_reset_required
```

For each scenario:
- validate runtime behavior
- validate event emission
- validate replay recording
- validate final safety state
- validate command arbitration

Generate:
- scenario summaries
- incident summaries
- validation outputs

---

# 12. Runtime Validation Tooling

Create operational validation tooling.

Suggested scripts/tools:

```text
tools/validate_tf_tree.py
tools/validate_replay_run.py
tools/validate_event_integrity.py
tools/validate_bridge_topics.py
tools/validate_safety_pipeline.py
```

These should:
- perform real checks
- produce actionable diagnostics
- support CI integration later

---

# 13. Testing Expansion

Add meaningful runtime-oriented tests.

Required categories:

## Launch Validation
- launch success
- node presence
- bridge availability

## TF Validation
- expected frames exist
- transform consistency

## Safety Pipeline
- only authorized commands reach actuator path
- safe-stop zeros motion
- E-stop latches

## Sensor Validation
- freshness propagation
- stale sensor detection
- timestamp consistency

## Fault Integration
- fault activation behavior
- replay capture
- event emission

## Replay Integrity
- event ordering
- metadata integrity
- replay completeness

## Diagnostics
- heartbeat detection
- stale subsystem warnings
- bridge failure warnings

---

# 14. Documentation Updates

Update docs ONLY where required.

Update:
- `ARCHITECTURE.md`
- `REPLAY_SYSTEM.md`
- `TESTING_STRATEGY.md`
- `SYSTEM_CONTEXT.md`
- `ROADMAP.md`

Add:
- runtime validation diagrams
- TF topology diagrams
- launch sequencing diagrams
- diagnostics architecture notes
- replay integrity notes

Document:
- known runtime limitations
- deterministic guarantees
- nondeterministic boundaries
- simulation assumptions

---

# Required Quality Level

This implementation should feel like:
- an internal robotics validation runtime
- operational robotics infrastructure
- resilience-engineering tooling

NOT:
- tutorial code
- toy simulation glue
- ROS demo boilerplate

Code should:
- preserve architectural discipline
- preserve safety authority
- preserve replay-first design
- expose operational visibility
- fail loudly and observably

---

# Acceptance Criteria

This phase is complete only if:

1. Gazebo launches reliably.
2. TF tree validates cleanly.
3. ros_gz_bridge topics validate correctly.
4. Only authorized motion reaches actuators.
5. Safe-stop forces zero motion.
6. E-stop fully inhibits motion.
7. Fault injection propagates correctly.
8. Replay artifacts are coherent.
9. Event timelines remain consistent.
10. Runtime diagnostics exist.
11. Sensor freshness is validated.
12. Scenario validation suite executes correctly.
13. Tests meaningfully validate runtime behavior.
14. The architecture remains internally consistent.

---

# Final Response Required

When complete, report:

- files created
- files modified
- runtime diagnostics added
- validation tooling added
- launch improvements
- TF validation results
- bridge validation results
- replay validation improvements
- tests added
- tests passing/failing
- approximate LOC added
- known runtime limitations
- recommended next implementation phase

Do not claim completion if:
- TF is unstable
- actuator authorization is bypassable
- replay integrity is broken
- bridge validation fails
- diagnostics are incomplete
- scenario validation is unreliable
```
