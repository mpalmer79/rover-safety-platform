You are acting as a principal robotics systems architect and documentation engineer.

You are working inside my existing GitHub repository for a robotics portfolio project currently named:

`rover-safety-platform`

This repository is intended to become a 2026-level, principal-quality autonomous robotics portfolio project inspired by serious robotics R&D environments such as DEKA Research and Development, industrial robotics, safety-critical autonomy, medical-device-grade engineering discipline, and mission-aware robotic systems.

This is NOT a hobby rover.

The project direction is:

# Autonomous Safety Validation Rover Platform

A simulation-first robotics platform for validating deterministic autonomous rover behavior under degraded operational conditions.

The system should demonstrate:

- ROS 2 Jazzy-based autonomy architecture
- Gazebo Harmonic simulation-first workflow
- deterministic rover execution
- lifecycle-managed nodes
- explicit safety supervisor authority
- bounded operational design domain
- fault injection
- degraded-mode operation
- replayable incident timelines
- telemetry-first observability
- rosbag2 / MCAP replay strategy
- Foxglove-based visualization
- future Raspberry Pi 5 + MCU hardware split
- Jetson-class hardware only when perception workloads justify it

The repository currently has early architecture material. Your job in this pass is NOT to implement runtime code.

Your job is to create the foundational documentation authority layer that will control all later implementation work.

These files must be written as if they are guiding a serious engineering team, not explaining a beginner robotics tutorial.

Avoid hype.
Avoid shallow marketing language.
Avoid overclaiming.
Avoid pretending this is safety-certified.
Avoid claiming medical, industrial, or automotive compliance unless clearly framed as design inspiration only.

Use clear engineering language.

---

# Primary Objective

Create or update the following documentation files:

```text
docs/ODD.md
docs/SAFETY_MODEL.md
docs/EVENT_MODEL.md
docs/FAULT_INJECTION.md
docs/REPLAY_SYSTEM.md
docs/ROADMAP.md
docs/SYSTEM_CONTEXT.md
docs/TESTING_STRATEGY.md
docs/adr/ADR-001-ros2-jazzy-selection.md
docs/adr/ADR-002-gazebo-harmonic-selection.md
docs/adr/ADR-003-simulation-first-strategy.md
docs/adr/ADR-004-safety-supervisor-authority-model.md
docs/adr/ADR-005-companion-computer-mcu-split.md
```

If `docs/` or `docs/adr/` does not exist, create it.

If any file already exists, preserve valuable existing content, but rewrite weak, generic, or conflicting sections so the documentation is internally consistent.

Do not delete unrelated files.

Do not implement application code in this pass.

---

# Source of Truth

Use the following technical direction as the controlling architecture:

```text
ROS 2 Jazzy
Ubuntu 24.04
Gazebo Harmonic
Nav2
BehaviorTree.CPP
robot_localization
rosbag2 / MCAP
ros2_tracing
Foxglove
Raspberry Pi 5 + dedicated MCU safety layer later
Jetson only if camera/perception is justified later
```

The preferred repository-level workspace shape is:

```text
rover_ws/
  src/
    rover_msgs/
    rover_description/
    rover_bringup/
    rover_sim_gazebo/
    rover_hw_gateway/
    rover_sensor_adapters/
    rover_state_estimation/
    rover_world_model/
    rover_safety_supervisor/
    rover_mission_bt/
    rover_observability/
    rover_fault_injection/
    rover_dashboard_gateway/
    rover_tests/
    rover_docs/
```

Do not change repo structure unless needed for docs directories.

---

# Core Architectural Rules

All created files must reinforce these rules:

1. ROS 2 is middleware, not the full system architecture.
2. The safety supervisor has final authority over actuator commands.
3. Mission logic may request motion, but may not authorize motion.
4. The motor gateway is the only subsystem allowed to write actuator commands.
5. Simulation and hardware must share message contracts.
6. Fault injection must be independent from mission logic.
7. Observability is a first-class subsystem, not a debugging afterthought.
8. Replayability is a platform requirement.
9. Camera-first perception, GNSS-first autonomy, SLAM-heavy work, Isaac Sim, and Jetson hardware are deferred.
10. The project succeeds only if degraded behavior is bounded, explainable, and replayable.

---

# File Requirements

## 1. `docs/ODD.md`

Create the Operational Design Domain.

Must include:

- purpose of the ODD
- supported environment
- unsupported environment
- operational assumptions
- allowed terrain
- indoor/outdoor assumptions
- lighting assumptions
- obstacle assumptions
- connectivity assumptions
- velocity limits
- slope limits
- sensor assumptions
- simulation assumptions
- safe-stop triggers
- ODD exit conditions
- recovery requirements
- explicit non-goals

Use realistic MVP constraints.

Do NOT write broad “works anywhere” language.

The ODD should make clear that the MVP operates in constrained indoor or semi-structured simulated environments first.

Include a table for:

```text
Condition
Supported Range
Out-of-Domain Trigger
Expected System Response
```

---

## 2. `docs/SAFETY_MODEL.md`

Create the safety authority and state-transition model.

Must include:

- purpose
- safety authority hierarchy
- motion authorization rules
- safety supervisor responsibilities
- mission layer restrictions
- hardware gateway restrictions
- state machine
- state definitions
- transition rules
- watchdog model
- freshness monitoring
- degraded-mode semantics
- safe-stop semantics
- E-stop latch semantics
- recovery semantics
- failure escalation examples
- anti-bypass rules

Use these states:

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

Make clear:

- `SAFE_STOP` commands zero motion.
- `E_STOP_LATCHED` requires explicit operator reset.
- `RECOVERY` must revalidate required streams before reactivation.
- The planner cannot override safety.

Include a Mermaid state diagram if appropriate.

---

## 3. `docs/EVENT_MODEL.md`

Create the canonical event model.

Must include:

- purpose
- event design principles
- event envelope schema
- required fields
- optional fields
- severity levels
- event categories
- reason code strategy
- event ordering rules
- timestamp strategy
- correlation IDs
- run IDs
- scenario IDs
- replay requirements
- example events

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

Event severity levels:

```text
DEBUG
INFO
NOTICE
WARNING
ERROR
CRITICAL
```

Event categories should include:

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

Include JSON examples for:

- stale LiDAR event
- degraded-mode transition
- safe-stop event
- E-stop latched event

---

## 4. `docs/FAULT_INJECTION.md`

Create the fault injection strategy.

Must include:

- purpose
- fault injection principles
- supported MVP fault classes
- fault scope boundaries
- fault lifecycle
- injection points
- expected system responses
- observability requirements
- replay requirements
- safety constraints
- test acceptance criteria

Initial fault classes:

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

For each fault class include:

```text
Description
Injection Point
Expected Detection
Expected Safety Response
Required Events
Replay Requirement
```

Make clear that fault injection must not directly mutate safety state. It should alter inputs or timing and allow the safety system to respond through normal mechanisms.

---

## 5. `docs/REPLAY_SYSTEM.md`

Create the replay and incident reconstruction architecture.

Must include:

- purpose
- replay goals
- replay non-goals
- rosbag2 / MCAP role
- structured event index role
- Foxglove role
- replay timeline model
- synchronization strategy
- deterministic replay limits
- incident reconstruction workflow
- required recorded topics
- required event types
- replay acceptance criteria
- storage layout proposal

Required recorded data should include:

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

Include a proposed storage layout:

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

---

## 6. `docs/ROADMAP.md`

Create the phased implementation roadmap.

Must include:

- project vision
- phase gates
- deliverables
- acceptance criteria
- risks
- deferred features
- portfolio value

Use these phases:

```text
Phase 0: Architecture Authority Layer
Phase 1: Gazebo Simulation Bringup
Phase 2: Deterministic Autonomy Core
Phase 3: Safety Supervision & Degraded Modes
Phase 4: Replay, Telemetry & Incident Reconstruction
Phase 5: Bench Hardware Integration
Phase 6: Optional Perception Expansion
```

Each phase must include:

```text
Objectives
Deliverables
Acceptance Criteria
Risks
Deferred Work
Portfolio Signal
```

Make this practical enough that later Claude Code sessions can build from it.

---

## 7. `docs/SYSTEM_CONTEXT.md`

Create the system context document.

Must include:

- system purpose
- primary actors
- external systems
- runtime environments
- trust boundaries
- simulation boundary
- hardware boundary
- operator boundary
- telemetry boundary
- data flow summary
- system context diagram

Primary actors:

```text
Operator
Developer
Simulation Runtime
Safety Supervisor
Mission Runtime
Hardware Gateway
Telemetry Consumer
Replay Analyst
```

External systems:

```text
Gazebo Harmonic
ROS 2 graph
Foxglove
rosbag2
Future physical rover
Future MCU safety island
```

Include one Mermaid context diagram.

---

## 8. `docs/TESTING_STRATEGY.md`

Create the testing strategy.

Must include:

- testing philosophy
- test layers
- deterministic simulation tests
- safety-state transition tests
- fault injection tests
- replay validation tests
- event schema tests
- watchdog tests
- timeout tests
- sim-vs-hardware parity tests
- acceptance gates
- CI expectations

Test categories:

```text
unit
integration
simulation
fault_injection
replay
contract
hardware_bench
```

Include examples of tests that should exist later.

Make clear that no feature is complete until:

- it emits events
- it participates in replay
- it has safety-state tests where applicable
- it does not bypass the safety supervisor

---

# ADR Requirements

Create the ADR directory and these files.

Use a consistent ADR structure:

```md
# ADR-XXX: Title

## Status
Accepted

## Context

## Decision

## Consequences

## Alternatives Considered

## Follow-up Work
```

---

## ADR-001: ROS 2 Jazzy Selection

Must state why ROS 2 Jazzy is selected:

- LTS release
- Ubuntu 24.04 alignment
- ecosystem support
- DDS communication
- lifecycle nodes
- Nav2 compatibility
- simulation integration

Alternatives:
- ROS 2 Rolling
- older ROS 2 distributions
- custom middleware

---

## ADR-002: Gazebo Harmonic Selection

Must state why Gazebo Harmonic is primary:

- ROS 2 Jazzy alignment
- ROS-native simulation path
- physics and sensor simulation
- plugin ecosystem
- ros_gz_bridge support
- lower practical risk than Isaac Sim for MVP

Alternatives:
- Webots
- PyBullet
- Isaac Sim

---

## ADR-003: Simulation-First Strategy

Must state why simulation precedes hardware:

- deterministic iteration
- safety testing before physical motion
- fault injection
- cost control
- repeatable scenarios
- faster debugging
- hardware abstraction validation

Alternatives:
- hardware-first
- hybrid-first
- perception-first

---

## ADR-004: Safety Supervisor Authority Model

Must state:

- safety supervisor owns final motion authorization
- mission layer cannot write actuator commands
- hardware gateway accepts only authorized commands
- fault injection cannot directly set safety state
- safety transitions must emit events
- degraded and safe-stop states are enforced centrally

Alternatives:
- planner-direct actuator control
- distributed safety decisions
- mission-owned safety transitions

---

## ADR-005: Companion Computer + MCU Split

Must state:

- Raspberry Pi 5 or similar SBC handles ROS 2 companion compute
- MCU handles timing-sensitive safety and actuator control later
- Linux SBC is not treated as hard real-time motor controller
- micro-ROS or narrow MCU protocol remains a future integration option

Alternatives:
- SBC-only control
- Jetson-first hardware
- MCU-only robotics control

---

# Style Requirements

Write these documents with:

- serious engineering tone
- direct language
- precise constraints
- realistic scope
- strong boundaries
- implementation-ready detail

Do not use:
- sales language
- AI hype
- vague claims
- generic filler
- “cutting edge” without architectural meaning
- claims of certification
- claims of production safety compliance

Use Markdown tables where helpful.

Use Mermaid diagrams only where they add clarity.

Use consistent terminology:

```text
safety supervisor
motion arbitration
authorized command
requested command
degraded mode
safe-stop
E-stop latched
run_id
scenario_id
event_id
ODD
```

---

# Quality Bar

Before finishing, self-review all created files for:

1. Internal consistency
2. No contradiction with ARCHITECTURE.md
3. No premature hardware commitment
4. No AI/perception scope creep
5. Clear safety authority model
6. Clear replay expectations
7. Clear testing expectations
8. Usable as source-of-truth docs for future implementation prompts

---

# Final Response Required

When finished, report:

- files created
- files updated
- major decisions encoded
- any conflicts found in existing docs
- recommended next Claude Code build phase

Do not implement runtime code in this pass.
