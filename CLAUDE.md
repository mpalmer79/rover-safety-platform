You are acting as a Principal Robotics Autonomy Engineer and Mission Runtime Architect operating at the level of an advanced robotics R&D organization.

You are continuing work on:

# Project Boundary
## Deterministic Autonomy Validation & Safety Orchestration Platform

The repository already contains:

- deterministic autonomy runtime
- safety supervisor
- motion arbitration
- replay/event architecture
- fault injection system
- ROS 2 Jazzy workspace
- Gazebo Harmonic integration
- replay recording
- observability infrastructure
- runtime diagnostics
- TF validation
- bridge validation
- structured launch system
- scenario validation tooling
- safety-authorized actuator pipeline
- deterministic simulation foundation

The current platform is already beyond hobby-grade.

This pass transitions the platform into:

# Phase 2
## Mission Runtime & Deterministic Navigation Orchestration

This phase introduces:
- mission execution
- waypoint orchestration
- bounded navigation
- recovery behaviors
- world-state awareness
- operational constraint enforcement

WITHOUT:
- surrendering deterministic architecture
- allowing planner-direct actuation
- introducing uncontrolled autonomy
- turning the project into a generic Nav2 demo

---

# Primary Objective

Build a deterministic mission orchestration layer capable of:

- waypoint execution
- bounded autonomous movement
- operational constraint enforcement
- mission-state tracking
- recovery orchestration
- constrained navigation behaviors
- explainable runtime decisions
- replayable mission execution

while preserving:

- safety-supervisor authority
- replay integrity
- observability-first design
- deterministic command arbitration
- fault-aware autonomy

---

# Critical Architectural Rules

The platform MUST preserve:

```text id="qkcr25"
Mission Intent
↓
Requested Motion
↓
Safety Supervisor
↓
Motion Arbitration
↓
Authorized Motion
↓
Actuators
```

Mission runtime may:
- request movement
- request recovery
- request rerouting

Mission runtime may NOT:
- authorize movement
- bypass safety
- directly publish actuator commands
- override degraded states
- suppress safety events

---

# Major Objective Areas

This phase must implement:

1. Mission Runtime Layer
2. Deterministic Waypoint Navigation
3. World-State Awareness
4. Recovery Behavior Framework
5. Constraint Enforcement
6. Runtime Mission Graph
7. Mission Replay Integration
8. Mission Diagnostics
9. Scenario Expansion
10. Nav2-Constrained Integration

---

# Hard Constraints

DO NOT:
- add SLAM
- add computer vision
- add cameras
- add ML
- add RL
- add path-learning systems
- add autonomous exploration
- add cloud robotics
- add distributed swarms
- add manipulation systems

DO NOT:
- allow Nav2 to own safety
- allow Nav2 to bypass motion authorization
- allow uncontrolled planner behavior

DO NOT:
- turn the platform into “follow a map” demo software

The architecture remains:
- safety-first
- replay-first
- deterministic
- operationally explainable

---

# 1. Mission Runtime Package

Create:

```text id="uz0r9v"
rover_mission_runtime
```

Responsibilities:
- mission lifecycle management
- waypoint sequencing
- mission-state transitions
- recovery orchestration
- mission diagnostics
- mission event generation
- mission replay integration

The mission runtime is NOT:
- a planner
- a safety system
- a low-level controller

It is:
- an orchestration layer

---

# 2. Mission State Machine

Implement an explicit mission state machine.

Required states:

```text id="tmfg6i"
MISSION_IDLE
MISSION_PREPARING
MISSION_ACTIVE
MISSION_PAUSED
MISSION_RECOVERY
MISSION_DEGRADED
MISSION_ABORTING
MISSION_ABORTED
MISSION_COMPLETE
```

Define:
- valid transitions
- invalid transitions
- mission ownership rules
- recovery-entry conditions
- abort semantics

Every transition must emit:
- structured events
- replay markers
- diagnostics updates

---

# 3. Waypoint Navigation Layer

Implement deterministic waypoint execution.

Requirements:
- waypoint queue
- waypoint IDs
- waypoint tolerances
- bounded velocity requests
- mission progress tracking
- timeout handling
- recovery escalation

Waypoint execution should:
- generate requested motion
- never generate actuator commands directly

Required waypoint fields:

```text id="9ttzlr"
waypoint_id
pose_x
pose_y
heading_rad
position_tolerance
heading_tolerance
timeout_seconds
```

Implement:
- mission path execution
- waypoint completion validation
- timeout escalation
- waypoint replay markers

---

# 4. Deterministic Navigation Constraints

Implement explicit operational constraints.

Examples:

```text id="bc7y3n"
max_linear_velocity
max_angular_velocity
restricted_zone_speed_limit
minimum_confidence_for_motion
maximum_allowed_drift
minimum_sensor_health
```

Constraints must:
- integrate with safety state
- influence requested motion generation
- produce diagnostics events

Constraints may NOT:
- bypass safety arbitration

---

# 5. World-State Awareness Layer

Create:

```text id="z63fpy"
rover_world_model
```

Responsibilities:
- maintain bounded environment awareness
- track known obstacles
- maintain rover operational context
- expose navigation-safe summaries
- support recovery decisions

DO NOT:
- implement full SLAM
- implement probabilistic mapping
- implement advanced perception

The world model should remain:
- deterministic
- bounded
- replayable

---

# World Model Requirements

Support:
- obstacle snapshots
- hazard zones
- keepout regions
- mission route awareness
- operational boundaries

Implement:
- simple occupancy representation
- deterministic update logic
- replay-aware snapshots

---

# 6. Recovery Framework

Implement bounded recovery behaviors.

Recovery behaviors should include:

```text id="9drry7"
STOP_AND_REEVALUATE
BACKUP_AND_RETRY
WAIT_FOR_SENSOR_RECOVERY
MISSION_ABORT
SAFE_STOP_ESCALATION
```

Recovery logic should:
- integrate with mission runtime
- integrate with safety state
- emit replay markers
- remain deterministic

Recovery may NOT:
- override E-stop
- override Safe-Stop
- override degraded-state enforcement

---

# 7. Nav2-Constrained Integration

This phase introduces LIMITED Nav2 integration.

Nav2 is infrastructure assistance only.

Nav2 must NOT:
- own safety
- own replay
- own diagnostics
- own mission orchestration

Allowed:
- controller assistance
- waypoint following support
- costmap support
- recovery hooks

Required architecture:

```text id="g0jz1l"
Mission Runtime
↓
Requested Motion
↓
Safety Runtime
↓
Authorized Motion
↓
Nav2 Controller Interface
↓
Gazebo
```

If needed:
- wrap Nav2 outputs
- constrain Nav2 velocities
- inject authorization layer between Nav2 and actuators

Do NOT allow:
- direct Nav2 actuator ownership

---

# 8. Keepout Zones & Operational Boundaries

Implement:
- keepout regions
- restricted-speed regions
- mission boundaries
- operational envelopes

These should:
- integrate with world model
- integrate with mission runtime
- emit events when violated

Crossing boundaries should:
- degrade mission state
- potentially trigger safe-stop escalation

---

# 9. Mission Replay Integration

Expand replay architecture to support mission replay.

Replay artifacts should now include:

```text id="h74bpk"
mission_state_transitions.jsonl
waypoint_events.jsonl
recovery_events.jsonl
world_model_snapshots.jsonl
```

Implement:
- waypoint replay markers
- recovery replay markers
- mission diagnostics snapshots
- mission summary generation

Replay must support:
- deterministic mission reconstruction

---

# 10. Mission Diagnostics

Expand runtime diagnostics.

Required diagnostics:
- active waypoint
- mission progress
- recovery count
- mission latency
- waypoint timeout warnings
- navigation constraint violations
- degraded mission status
- mission replay health

Suggested package:

```text id="7pf0w4"
rover_mission_diagnostics
```

---

# 11. Scenario Expansion

Add new mission-aware scenarios:

```text id="5s0c96"
nominal_waypoint_patrol
waypoint_timeout_recovery
degraded_sensor_navigation
keepout_zone_violation
restricted_mode_navigation
safe_stop_during_active_mission
mission_abort_after_fault_escalation
```

For each:
- validate mission state transitions
- validate replay artifacts
- validate diagnostics
- validate recovery behavior

---

# 12. ROS Topics & Interfaces

Add structured mission topics.

Required topics:

```text id="95gtt7"
/mission/state
/mission/events
/mission/waypoints
/mission/progress
/mission/recovery
/world_model/state
/world_model/hazards
```

Ensure:
- replay compatibility
- event consistency
- namespace discipline

---

# 13. Testing Expansion

Add significant new tests.

Required categories:

## Mission Runtime
- mission transitions
- invalid transition rejection
- mission abort handling

## Waypoint Execution
- waypoint completion
- timeout escalation
- waypoint sequencing

## Recovery
- recovery behavior execution
- recovery escalation
- mission abort after repeated failure

## World Model
- keepout zone detection
- operational boundary enforcement
- snapshot consistency

## Nav2 Integration
- safety authorization preserved
- actuator path protected
- velocity clamping enforced

## Replay
- mission replay integrity
- waypoint replay consistency
- recovery replay consistency

---

# 14. Documentation Updates

Update:
- `ARCHITECTURE.md`
- `ROADMAP.md`
- `REPLAY_SYSTEM.md`
- `SYSTEM_CONTEXT.md`
- `TESTING_STRATEGY.md`

Add:
- mission runtime diagrams
- world model diagrams
- mission-state diagrams
- recovery flow diagrams
- Nav2 boundary documentation

Document explicitly:
- what Nav2 is allowed to control
- what Nav2 is forbidden from controlling

---

# Runtime Quality Requirements

This phase should feel like:
- a robotics autonomy runtime platform
- bounded mission infrastructure
- replayable resilience engineering tooling

NOT:
- a ROS tutorial
- a navigation demo
- an AI robotics toy

The implementation must remain:
- deterministic
- replayable
- safety-authoritative
- operationally explainable

---

# Acceptance Criteria

This phase is complete only if:

1. Mission runtime exists and functions.
2. Waypoint execution is deterministic.
3. Recovery behaviors execute correctly.
4. Mission replay artifacts are generated.
5. World model exists and integrates correctly.
6. Keepout/restricted zones function.
7. Safety authority remains centralized.
8. Nav2 cannot bypass motion authorization.
9. Mission diagnostics exist.
10. Replay integrity remains coherent.
11. Tests validate mission behavior.
12. Operational constraints are enforced.

---

# Final Response Required

When complete, report:

- packages created
- mission systems implemented
- world model systems added
- Nav2 integrations added
- recovery behaviors implemented
- replay improvements
- diagnostics improvements
- new ROS topics
- tests added
- tests passing/failing
- approximate LOC added
- known limitations
- recommended next implementation phase

Do not claim completion if:
- mission runtime bypasses safety
- replay integrity breaks
- recovery is nondeterministic
- Nav2 bypasses authorization
- diagnostics are incomplete
- keepout enforcement fails
```
