# Autonomous Safety Validation Rover Platform Research Brief

## Executive Summary

The strongest direction for this portfolio project is a simulation-first autonomous rover built on ROS 2 Jazzy on Ubuntu 24.04, with Gazebo Harmonic as the primary simulator, a lifecycle-managed node graph, an explicit safety supervisor, and a full observability pipeline built around logs, bags, traces, and replay.

That recommendation is not based on popularity. It is based on:
- support horizon
- ecosystem fit
- deterministic middleware behavior
- simulator maturity
- operational tooling
- realistic implementation scope

The MVP should be intentionally narrow and rigorous:

- differential-drive rover
- semi-structured environment
- 2D LiDAR
- wheel encoders
- IMU
- bumper/contact channel
- confidence scoring
- disagreement detection
- degraded-mode transitions
- replayable incident timelines

The project should optimize for:
- resilience engineering
- observability
- deterministic orchestration
- safety-state enforcement
- operational transparency

NOT:
- novelty AI
- humanoid robotics
- viral demos
- full self-driving research
- research-paper SLAM experiments

---

# Recommended Technical Direction

## Core Stack

```text
Ubuntu 24.04
ROS 2 Jazzy
Gazebo Harmonic
Nav2
BehaviorTree.CPP
robot_localization
rosbag2
Foxglove
```

---

## Why ROS 2 Matters

ROS 2 should be treated as middleware infrastructure, not as the entire architecture.

Professionally, ROS 2 provides:
- DDS-backed communication
- QoS controls
- pub/sub transport
- actions/services/topics
- simulator interoperability
- lifecycle-managed orchestration

Topics should carry:
- sensor streams
- telemetry
- state updates

Services should handle:
- short-lived synchronous requests

Actions should orchestrate:
- waypoint execution
- navigation goals
- recovery flows

---

## Recommended Architecture Style

The recommended architecture is:

### Layered Event-Driven Autonomy Stack

```text
Sensor Adapters
↓
State Estimation
↓
Confidence & Disagreement Evaluation
↓
Mission Layer
↓
Safety Supervisor
↓
Motor Gateway
```

This separation matters.

The rover should never allow:
- planners
- behavior trees
- navigation modules

to write directly to actuators.

The safety supervisor owns:
- command arbitration
- degraded transitions
- emergency stops
- final authority

That is a critical principal-level architectural signal.

---

# Repository Structure

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

---

# Mission Logic vs Safety Logic

These should NOT use the same abstraction.

## Mission Layer
Use:
- BehaviorTree.CPP
- waypoint execution
- recovery behaviors
- navigation goals

Behavior trees are excellent for:
- asynchronous orchestration
- reactive behaviors
- modular control flow

---

## Safety Layer
Use:
- explicit finite state machine

Safety behavior must remain:
- deterministic
- auditable
- bounded
- explainable

This distinction separates:
- architecture thinking

from:
- hobby robotics

---

# Safety Architecture

## Recommended Safety States

```text
Boot
Inactive
Active-Normal
Active-Restricted
Active-Degraded
Safe-Stop
E-Stop-Latched
Recovery
```

---

## State Definitions

### Active-Normal
All systems healthy.

### Active-Restricted
Movement allowed with reduced speed or constrained zones.

### Active-Degraded
One noncritical sensing pathway lost.

### Safe-Stop
Minimal-risk stop state.

### E-Stop-Latched
Manual reset required.

---

# Freshness & Watchdog Strategy

The platform should monitor freshness at multiple layers.

## DDS Layer
QoS deadlines.

## Software Layer
Heartbeat monitoring.
Command timeout rules.

## Embedded Layer
Watchdog timers.
Motor power disable path.

---

# Recommended MVP Safety Controls

Include:
- freshness checks
- timeout-to-zero
- disagreement detection
- restricted-speed enforcement
- emergency stop handling
- replayable incidents

Defer:
- aircraft-grade redundancy
- fail-operational autonomy
- distributed voting clusters

---

# Event Model

Every critical state transition should emit structured events.

Example:

```json
{
  "timestamp": "2026-05-09T20:44:00Z",
  "event_type": "sensor_disagreement",
  "safety_state": "Active-Degraded",
  "source": "lidar",
  "confidence_score": 0.41,
  "final_motion_command": {
    "linear_velocity": 0.0,
    "angular_velocity": 0.0
  },
  "reason_code": "LIDAR_TIMEOUT"
}
```

---

# Recommended Failure Modes

The MVP should intentionally model:

- stale LiDAR
- delayed telemetry
- bridge disconnects
- wheel-slip divergence
- encoder drift
- IMU bias drift
- command timeout
- recovery failure
- planner disagreement

This project becomes valuable when:
- failures are observable
- transitions are explainable
- incidents are replayable

---

# Simulation Strategy

## Recommended Simulator

### Gazebo Harmonic

Why:
- official ROS ecosystem alignment
- mature ROS integration
- supported Jazzy pairing
- strong plugin architecture
- operational realism

---

# Secondary Simulator

### Webots

Useful for:
- repeatable scenario reset
- desktop simplicity
- rapid iteration

But Gazebo should remain primary.

---

# Simulator To Defer

### Isaac Sim

Do NOT start here.

Reasons:
- workstation-level GPU expectations
- operational complexity
- heavy infrastructure burden
- premature optimization risk

Isaac Sim becomes appropriate ONLY after:
- replay systems
- telemetry
- degraded-mode orchestration
- hardware abstraction

already exist.

---

# Sensor Strategy

## Recommended MVP Sensors

### 2D LiDAR
Primary obstacle awareness.

### Wheel Encoders
Deterministic motion validation.

### IMU
Orientation and motion consistency.

### Bumper / Contact Channel
Last-resort collision awareness.

---

# Sensors To Avoid Initially

## Cameras
Explodes complexity prematurely.

## GNSS
Introduces frame-alignment overhead.

## Advanced Sensor Fusion
Premature before observability matures.

---

# Common Sensor Failure Modes

## Wheel Odometry
- slip
- drift
- integration error

## IMU
- bias drift
- instability

## Ultrasonic
- angled surfaces
- soft materials
- inconsistent reflection

These are GOOD for the project because:
they create meaningful fault-injection scenarios.

---

# Hardware Recommendations

## Recommended Physical MVP

```text
Raspberry Pi 5
+
Microcontroller Safety Island
```

The architecture should separate:
- companion compute
- actuator safety control

A Linux SBC should NOT be treated as:
- deterministic motor control hardware

---

# Why micro-ROS Matters

micro-ROS allows:
- ROS-compatible MCU communication
- serial/UDP/TCP transport
- embedded watchdog integration

This creates:
- realistic robotics architecture
- scalable subsystem separation

---

# Upgrade Path

## Jetson Orin Nano

ONLY justify this if:
- camera pipelines
- onboard inference
- learned perception

become actual requirements.

Hardware escalation should happen because of:
- system requirements

NOT:
- excitement

---

# Observability & Telemetry

This is the strongest differentiator in the project.

Most robotics portfolios fail here.

Your advantage is:
- replayability
- telemetry architecture
- incident reconstruction
- operational introspection

---

# Required Observability Components

## rosbag2
Default runtime recording.

## MCAP
Structured storage format.

## ros2_tracing
Low-level trace instrumentation.

## Foxglove
Operational visualization and replay.

---

# Dashboard Requirements

## Required Panels

### Rover State
Current:
- lifecycle state
- safety state
- confidence score

### Telemetry Stream
Live event flow.

### Replay Timeline
Critical feature.

### Fault Injection Controls
Scenario triggering.

### Topic Freshness
Heartbeat visualization.

---

# Telemetry Categories

Separate:
- raw streams
- incident events
- health metrics
- replay indexes

Do NOT merge everything into one datastore.

---

# Phase Roadmap

# Phase 0
## Architecture & Contracts

Deliver:
- ODD definition
- state machine
- subsystem contracts
- ADRs
- event schema
- package boundaries

The biggest mistake here is:
starting implementation before operational boundaries exist.

---

# Phase 1
## Simulation Bringup

Deliver:
- Gazebo rover
- ROS bridges
- diff-drive control
- reproducible launch
- baseline telemetry

Risk:
overbuilding environments.

---

# Phase 2
## Deterministic Autonomy Core

Deliver:
- state estimation
- mission behavior tree
- waypoint execution
- deterministic sequencing

Risk:
hidden concurrency nondeterminism.

---

# Phase 3
## Safety Supervision

Deliver:
- freshness monitoring
- degraded transitions
- safe-stop
- E-stop
- confidence scoring

This is the highest-value phase.

---

# Phase 4
## Replay & Observability

Deliver:
- replay workflows
- telemetry dashboards
- incident indexing
- timeline reconstruction

Most hobby projects never reach this level.

---

# Phase 5
## Hardware Integration

Deliver:
- Pi + MCU integration
- encoder validation
- watchdog validation
- stop-latency testing

Important:
bench testing first.

NOT:
outdoor rover chaos.

---

# Phase 6
## Optional Perception Expansion

Possible additions:
- camera pipelines
- Jetson migration
- Isaac Sim
- advanced perception

Only proceed if:
core architecture remains deterministic and explainable.

---

# Principal-Level Portfolio Signals

This project becomes senior-level when reviewers see:

- subsystem decomposition
- lifecycle-managed orchestration
- safety-state enforcement
- replayable incidents
- telemetry discipline
- operational boundaries
- explicit deferred-scope reasoning
- deterministic recovery behavior

NOT:
because of robotics hardware.

---

# Required Documentation

## Critical Documents

```text
ARCHITECTURE.md
SAFETY_MODEL.md
EVENT_MODEL.md
TELEMETRY.md
REPLAY_SYSTEM.md
FAULT_INJECTION.md
ODD.md
ADR/
```

---

# Highest-Value Demo

The best portfolio demo is NOT:
a perfect autonomous run.

The best demo is:

1. Normal mission execution
2. Inject stale LiDAR
3. Transition into Restricted mode
4. Inject odometry divergence
5. Trigger Safe-Stop
6. Replay incident timeline
7. Show telemetry-driven root cause

That compresses:
- resilience engineering
- observability
- deterministic orchestration
- explainability
- operational maturity

into a single demonstration.

---

# Key Risks

The project fails architecturally if it becomes:

- generic Nav2 demo
- AI-first rover
- simulator obsession
- camera pipeline rabbit hole
- hardware-first chaos
- dashboard-only cosmetics

The project succeeds when:
- failures are understandable
- autonomy is bounded
- state transitions are deterministic
- incidents are reconstructable
- operational reasoning is visible

---

# Immediate Next Steps

1. Freeze:
   - ROS 2 Jazzy
   - Ubuntu 24.04
   - Gazebo Harmonic

2. Write:
   - ODD
   - safety contracts
   - degraded-mode definitions

3. Create:
   - workspace skeleton
   - package boundaries
   - event schema

4. Bring up:
   - Gazebo rover
   - LiDAR
   - IMU
   - encoder topics
   - rosbag2 recording

5. Implement:
   - stale scan fault
   - wheel-slip divergence
   - command timeout stop

6. DO NOT buy expensive hardware yet.
