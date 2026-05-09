You are acting as a Principal Robotics Systems Engineer and Autonomy Platform Architect operating at the level of an advanced R&D robotics organization.

You are continuing implementation of:

# Project Boundary
## Deterministic Autonomy Validation & Safety Orchestration Platform

This repository already contains:
- authority architecture documents
- deterministic simulation runtime
- safety supervisor
- motion arbitration
- event system
- replay-ready recording
- fault injection framework
- scenario runner
- API layer
- substantial test coverage

This pass is NOT a greenfield build.

You must preserve architectural consistency with:
- `docs/ARCHITECTURE.md`
- `docs/ODD.md`
- `docs/SAFETY_MODEL.md`
- `docs/EVENT_MODEL.md`
- `docs/FAULT_INJECTION.md`
- `docs/REPLAY_SYSTEM.md`
- `docs/ROADMAP.md`

Read all architecture docs before implementation.

This pass transitions the project from:
- abstract deterministic runtime platform

to:

- ROS 2 + Gazebo-backed robotics simulation platform

WITHOUT collapsing architectural discipline.

This must still feel like:
- a resilience engineering platform
- a safety-aware autonomy runtime
- a replayable robotics validation environment

NOT:
- a random Nav2 demo
- a toy Gazebo rover
- a tutorial project
- a pile of launch files

---

# Primary Objective

Implement:

# Phase 1B
## ROS 2 + Gazebo Harmonic Simulation Bringup Layer

The goal is to create:
- a functioning ROS 2 workspace
- Gazebo simulation integration
- simulated rover runtime
- ROS-native sensor streams
- lifecycle-aware launch orchestration
- ros_gz_bridge integration
- replay-capable telemetry pathways
- adapter integration into the existing deterministic runtime platform

while preserving:
- safety authority boundaries
- replay architecture
- deterministic operational semantics
- fault injection discipline
- observability-first design

---

# Critical Constraints

DO NOT:
- add SLAM
- add computer vision
- add cameras
- add ML
- add reinforcement learning
- add Jetson dependencies
- add Isaac Sim
- add Kubernetes
- add cloud robotics
- add distributed swarms
- add manipulation/robot arm systems
- add autonomous exploration logic
- add planner-direct actuator control

DO NOT:
- bypass the safety supervisor
- bypass motion arbitration
- allow Gazebo plugins to directly own safety decisions

DO NOT:
- treat Gazebo as the architecture

The deterministic runtime platform remains the architectural center.

Gazebo and ROS 2 are infrastructure integration layers.

---

# Implementation Goals

This pass should create a substantial robotics-oriented implementation including:

- ROS 2 Jazzy workspace
- colcon workspace structure
- rover URDF/Xacro
- Gazebo Harmonic integration
- differential drive rover
- ROS topic architecture
- TF tree
- simulated sensors
- ros_gz_bridge configuration
- launch orchestration
- replay-oriented recording hooks
- observability hooks
- adapter integration into backend runtime
- scenario-driven simulation execution
- simulation configuration assets
- tests and validation scripts

This should be a major implementation pass.

Do not underbuild.

---

# Required Workspace Structure

Create or adapt:

```text
rover_ws/
  src/
    rover_msgs/
    rover_description/
    rover_bringup/
    rover_sim_gazebo/
    rover_sensor_adapters/
    rover_observability/
    rover_safety_bridge/
```

If additional packages are required, add them only if justified.

Preserve clean package separation.

---

# Required ROS 2 Packages

# 1. `rover_msgs`

Create custom ROS interfaces.

Include:
- custom messages
- custom services
- custom status messages

Required messages:

```text
SafetyState.msg
MotionAuthorization.msg
SystemHealth.msg
SensorHealth.msg
FaultEvent.msg
ReplayMarker.msg
```

Required fields should align with:
- `EVENT_MODEL.md`
- `SAFETY_MODEL.md`

Use realistic ROS message patterns.

Do not overbuild.

---

# 2. `rover_description`

Create the simulated rover description.

Must include:
- URDF/Xacro
- modular robot description
- differential drive base
- LiDAR mounting point
- IMU mounting point
- wheel joints
- collision geometry
- inertial properties
- TF consistency

Keep the rover:
- simple
- realistic
- maintainable

Avoid:
- highly detailed meshes
- unnecessary visual complexity
- overengineered physics

The goal is systems validation, not CAD perfection.

---

# Rover Requirements

Use:
- differential drive
- stable wheelbase
- simple rectangular chassis
- realistic dimensions
- realistic inertia

Include:
- base_link
- odom
- lidar_link
- imu_link
- wheel links
- wheel joints

Ensure:
- TF tree sanity
- clean naming
- ROS conventions

---

# 3. `rover_sim_gazebo`

Implement Gazebo Harmonic integration.

Must include:
- Gazebo world
- rover spawning
- bridge configuration
- simulation launch
- physics settings
- deterministic startup sequencing

Create:
- small indoor or semi-structured validation world
- bounded obstacle environment
- repeatable conditions

DO NOT:
- create massive worlds
- create photorealistic environments
- optimize visuals over observability

---

# Gazebo Integration Requirements

Implement:
- ros_gz_bridge YAML config
- clock bridging
- TF bridging
- sensor bridging
- command topic bridging

Bridge at minimum:

```text
/clock
/cmd_vel
/odom
/tf
/tf_static
/scan
/imu
/contact
```

Use launch-based configuration.

Avoid manual shell-dependent workflows where possible.

---

# 4. `rover_sensor_adapters`

Implement adapter nodes that convert ROS-native sensor streams into the deterministic runtime platform contracts.

These adapters are critical.

They are the architectural boundary between:
- ROS/Gazebo infrastructure

and:
- deterministic autonomy runtime

Implement adapters for:
- LiDAR
- IMU
- wheel odometry
- contact sensor

Each adapter must:
- validate timestamps
- normalize freshness semantics
- emit structured events where applicable
- preserve replay metadata
- support fault injection compatibility

Do NOT:
- embed business logic in adapters
- make adapters safety-authoritative

---

# 5. `rover_safety_bridge`

Critical package.

Implement the integration layer between:
- ROS runtime
- deterministic safety supervisor
- motion arbitration

Responsibilities:
- consume requested motion
- invoke safety supervisor
- publish authorized motion
- enforce safe-stop
- publish safety state
- publish health state
- publish structured safety events

Required topics:

```text
/cmd_vel_requested
/cmd_vel_authorized
/safety/state
/safety/events
/system/health
```

The rover must NEVER consume raw requested motion directly.

Only authorized motion reaches simulated actuators.

This is a core architectural requirement.

---

# 6. `rover_observability`

Implement observability infrastructure.

Must include:
- rosbag2 recording launch integration
- replay metadata hooks
- Foxglove-ready topic structure
- telemetry namespace organization
- runtime status publishing

Implement:
- run_id propagation
- scenario_id propagation
- replay markers
- event topic publishing

Prepare the system for:
- incident reconstruction
- replay workflows
- timeline visualization

---

# Launch Architecture

Create:
- structured launch hierarchy
- composable launch patterns
- deterministic startup ordering

Required launches:

```text
simulation.launch.py
rover_spawn.launch.py
observability.launch.py
safety_runtime.launch.py
full_system.launch.py
```

The launch structure should:
- isolate concerns
- support partial bringup
- support testing
- support replay runs

---

# Runtime Integration Requirements

The existing backend deterministic runtime platform must integrate with ROS.

You may:
- wrap backend runtime services
- expose runtime APIs to ROS nodes
- bridge events into ROS topics

You may NOT:
- duplicate business logic
- fork safety logic into separate implementations

ROS nodes should consume the same authoritative runtime logic already implemented in Python.

---

# Motion Pipeline Requirements

The command path MUST be:

```text
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
Gazebo Diff Drive
```

This separation is mandatory.

Implement runtime validation ensuring:
- unauthorized commands are never forwarded
- safe-stop zeros motion
- E-stop latches motion inhibition

---

# Sensor Requirements

Simulated sensors must include:

```text
2D LiDAR
IMU
Wheel Odometry
Contact/Bumper
```

Each sensor path should:
- publish ROS-native topics
- integrate with replay recording
- support fault injection
- expose freshness semantics

DO NOT add cameras yet.

---

# Fault Injection Integration

Integrate the existing fault framework into ROS simulation.

Fault injection must support:
- stale LiDAR
- delayed messages
- odometry divergence
- wheel slip
- IMU bias
- bridge disconnect simulation
- command timeout

Faults should:
- alter data
- alter timing
- alter freshness

Faults should NOT:
- directly mutate safety state

The safety system must react naturally.

---

# Replay & Recording Requirements

Integrate replay-aware runtime recording.

Implement:
- rosbag2 launch integration
- run metadata generation
- replay marker events
- structured run folders

Required structure:

```text
runs/
  <run_id>/
    metadata.json
    events.jsonl
    bags/
    traces/
    incident-summary.md
```

Do not fully implement replay playback yet.

Prepare the architecture for it.

---

# Foxglove & Observability

Prepare for Foxglove integration.

Implement:
- structured topic naming
- safety topics
- replay topics
- health topics
- event topics

Include documentation for:
- launching Foxglove bridge
- viewing telemetry
- observing safety transitions

---

# Testing Requirements

Create meaningful tests and validation tooling.

Required coverage:

## ROS Integration
- launch validation
- topic existence
- TF tree validation
- bridge configuration validation

## Safety
- authorized motion only
- safe-stop zero motion
- E-stop latch enforcement

## Sensor Pipeline
- freshness propagation
- timestamp validation
- adapter normalization

## Fault Injection
- stale LiDAR propagation
- delayed topic handling
- odometry divergence behavior

## Recording
- bag recording starts
- run metadata written
- replay markers emitted

---

# Documentation Requirements

Update docs only where needed.

Update:
- `ROADMAP.md`
- `ARCHITECTURE.md`
- `REPLAY_SYSTEM.md`
- `SYSTEM_CONTEXT.md`

Add:
- ROS graph diagrams
- TF tree documentation
- launch topology diagrams
- Gazebo architecture notes

---

# Expected Technical Quality

Write code and architecture consistent with:
- advanced robotics R&D discipline
- operational systems thinking
- replay-first observability
- deterministic validation principles

The resulting repo should feel like:
- an internal autonomy validation platform

NOT:
- a robotics tutorial repo

---

# Acceptance Criteria

This pass is complete only if:

1. Gazebo Harmonic launches successfully.
2. The rover spawns correctly.
3. TF tree is valid.
4. Sensor topics publish correctly.
5. Motion flows only through authorized command path.
6. Safety supervisor controls actuator authorization.
7. ros_gz_bridge configuration works.
8. rosbag2 recording integration exists.
9. Fault injection integrates into ROS simulation.
10. Structured launch hierarchy exists.
11. The deterministic runtime remains authoritative.
12. Tests and validation tooling exist.

---

# Final Response Required

When complete, report:

- packages created
- launch files created
- ROS topics implemented
- bridges configured
- tests added
- Gazebo worlds added
- TF structure
- approximate LOC added
- known limitations
- recommended next implementation phase

Do not claim completion if:
- Gazebo does not launch
- TF is broken
- topics are inconsistent
- motion bypasses safety supervisor
- replay recording is nonfunctional
- tests fail
```
