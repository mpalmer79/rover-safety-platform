# ARCHITECTURE.md
## Project Boundary
### Deterministic Autonomy Validation & Safety Orchestration Platform

---

# 1. System Overview

Project Boundary is a simulation-first robotics autonomy platform designed to validate deterministic rover behavior under degraded operational conditions.

The platform focuses on:

- bounded autonomy
- deterministic execution
- replayable operational state
- explainable safety decisions
- fault-aware orchestration
- observability-first robotics
- resilient control pipelines
- lifecycle-managed autonomy
- operational traceability

This platform is intentionally designed to resemble the architectural discipline found in:

- advanced industrial robotics
- aerospace autonomy validation systems
- defense-adjacent unmanned mobility platforms
- warehouse robotics safety systems
- mission-critical robotic runtime environments

Project Boundary is not intended to optimize for:
- novelty AI
- consumer robotics
- experimental humanoid systems
- uncontrolled autonomy
- viral demonstrations

The primary architectural objective is operational trustworthiness under uncertainty.

---

# 2. Core Architectural Principles

## 2.1 Deterministic Execution

The system prioritizes deterministic operational behavior over probabilistic autonomy.

Critical decision pathways must:
- produce explainable outputs
- preserve bounded state transitions
- support replay and reconstruction
- expose operational causality
- avoid hidden side effects

Safety-critical decisions must remain:
- explicit
- auditable
- replayable
- inspectable

---

## 2.2 Safety-Centric Autonomy

The rover is architecturally incapable of bypassing the safety supervisor.

All actuator commands must flow through:

```text
Safety Supervisor → Motion Arbitration → Hardware Gateway
```

Mission systems may request motion.
Only the safety system may authorize motion.

This boundary is non-negotiable.

---

## 2.3 Simulation-First Development

Simulation is treated as the primary development environment.

The platform is designed such that:
- simulation and physical hardware share message contracts
- hardware abstraction layers isolate transport concerns
- replay environments can reproduce operational incidents
- fault injection remains independent from physical deployment

Simulation parity is treated as a first-class architectural concern.

---

## 2.4 Observability-First Design

Operational visibility is considered a core subsystem.

The platform must support:
- structured event streams
- replayable autonomy timelines
- telemetry inspection
- transition auditing
- safety causality reconstruction
- fault correlation
- deterministic replay analysis

A robotics system that cannot explain itself is operationally incomplete.

---

## 2.5 Bounded Complexity

The platform intentionally constrains:
- sensor count
- environmental complexity
- autonomy scope
- perception stack depth
- deployment topology

This prevents:
- uncontrolled architectural expansion
- premature optimization
- observability collapse
- debugging impossibility

---

# 3. System Architecture

# 3.1 High-Level Runtime Topology

```text
┌──────────────────────────────────────────────────────┐
│                  Mission Layer                       │
│  Behavior Trees / Waypoint Execution / Recovery      │
└──────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────┐
│          Confidence & Validation Layer               │
│  Sensor Confidence / Disagreement / Freshness        │
└──────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────┐
│               Safety Supervisor                      │
│  Restricted Mode / Safe Stop / E-Stop Arbitration    │
└──────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────┐
│              Motion Arbitration Layer                │
│     Final Velocity Authorization & Constraints       │
└──────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────┐
│                 Hardware Gateway                     │
│    Simulated Actuators / Physical Actuators          │
└──────────────────────────────────────────────────────┘
```

---

# 3.2 Subsystem Boundaries

The architecture intentionally isolates:
- sensing
- estimation
- mission intent
- safety enforcement
- actuator control
- telemetry
- replay systems

This isolation exists to:
- reduce blast radius
- simplify debugging
- preserve replay determinism
- support fault containment
- enable independent subsystem validation

---

# 4. Runtime State Architecture

# 4.1 Safety State Machine

```text
BOOT
↓
INACTIVE
↓
ACTIVE_NORMAL
↓
ACTIVE_RESTRICTED
↓
ACTIVE_DEGRADED
↓
SAFE_STOP
↓
E_STOP_LATCHED
↓
RECOVERY
```

---

# 4.2 State Definitions

## BOOT
System initialization and dependency validation.

Movement prohibited.

---

## INACTIVE
Operationally healthy but awaiting activation.

Movement prohibited.

---

## ACTIVE_NORMAL
Nominal autonomous operation.

All validated sensor pathways healthy.

---

## ACTIVE_RESTRICTED
Reduced operational envelope.

Examples:
- reduced velocity
- restricted navigation zones
- constrained rotational acceleration

---

## ACTIVE_DEGRADED
One or more sensing pathways invalidated while minimum safe mobility remains.

Examples:
- auxiliary sensor loss
- degraded localization confidence
- partial environmental awareness

---

## SAFE_STOP
Minimal-risk operational halt.

Actuator commands reduced to zero.

---

## E_STOP_LATCHED
Human intervention required.

Cannot self-recover.

---

## RECOVERY
Controlled revalidation phase before reactivation.

---

# 5. ROS 2 Runtime Model

# 5.1 Middleware Selection

The platform standardizes on:

```text
ROS 2 Jazzy
Ubuntu 24.04
DDS-backed communication
Gazebo Harmonic
```

This stack was selected for:
- long-term support stability
- ecosystem maturity
- deterministic middleware controls
- lifecycle support
- simulator interoperability

---

# 5.2 Communication Patterns

## Topics

Used for:
- sensor streams
- telemetry
- transforms
- state updates

Characteristics:
- asynchronous
- high-frequency
- streaming-oriented

---

## Services

Used for:
- configuration requests
- health queries
- parameter inspection

Characteristics:
- synchronous
- request/response

---

## Actions

Used for:
- waypoint execution
- recovery behaviors
- navigation goals

Characteristics:
- long-running
- cancellable
- feedback-capable

---

# 5.3 Execution Strategy

The runtime avoids uncontrolled concurrency.

Critical control pathways may use:
- callback groups
- wait-set sequencing
- dedicated executors

to preserve:
- deterministic ordering
- bounded latency
- predictable arbitration

Unstructured thread pools are prohibited in safety-critical pathways.

---

# 6. Mission Architecture

# 6.1 Behavior Tree Runtime

Mission orchestration uses:

```text
BehaviorTree.CPP
```

The behavior tree layer is responsible for:
- navigation goals
- waypoint sequencing
- recovery behaviors
- non-blocking orchestration
- mission-level decisions

The behavior tree layer is NOT safety-authoritative.

---

# 6.2 Mission Constraints

Mission systems may:
- request movement
- request recovery
- request rerouting

Mission systems may NOT:
- bypass safety arbitration
- write actuator commands
- override degraded states

---

# 7. Safety Architecture

# 7.1 Safety Supervisor

The safety supervisor is the highest-authority runtime subsystem.

Responsibilities:
- safety-state transitions
- confidence enforcement
- motion inhibition
- restricted-mode activation
- stale-stream detection
- emergency stop handling
- actuator authorization

---

# 7.2 Confidence Engine

The confidence subsystem evaluates:
- freshness
- disagreement
- drift
- reliability
- estimator divergence

Outputs:
- confidence scores
- disagreement events
- degradation recommendations

---

# 7.3 Watchdog Model

The architecture includes:
- software watchdogs
- DDS freshness monitoring
- heartbeat verification
- command timeout enforcement
- actuator timeout failsafes

No control stream may silently fail.

---

# 8. Sensor Architecture

# 8.1 MVP Sensor Stack

Initial sensor model:

```text
2D LiDAR
Wheel Encoders
IMU
Contact/Bumper Sensor
```

This stack was selected because it:
- minimizes calibration complexity
- preserves deterministic validation
- supports meaningful fault injection
- enables replayable localization analysis

---

# 8.2 Sensor Abstraction Layer

All sensor inputs flow through:
- adapter nodes
- normalized message contracts
- timestamp validation
- freshness enforcement

The autonomy stack must remain agnostic to:
- simulation origin
- physical origin
- transport implementation

---

# 8.3 Sensor Failure Modeling

The platform intentionally models:
- LiDAR staleness
- encoder drift
- IMU bias
- wheel slip
- delayed packets
- dropped frames
- disagreement events

Failure modeling is a core platform feature.

---

# 9. Simulation Architecture

# 9.1 Primary Simulator

Primary environment:

```text
Gazebo Harmonic
```

Reasons:
- ROS-native integration
- mature plugin architecture
- strong DDS interoperability
- deterministic launch orchestration
- operational realism

---

# 9.2 Hardware Abstraction Strategy

Simulation and hardware share:
- message contracts
- control interfaces
- telemetry pathways
- replay infrastructure

Only gateway implementations differ.

---

# 9.3 Fault Injection Layer

Fault injection exists independently from:
- simulation engine
- hardware drivers
- mission logic

This allows:
- reproducible failures
- replayable incidents
- deterministic validation

---

# 10. Observability Architecture

# 10.1 Telemetry Philosophy

Observability is a platform subsystem, not a debugging afterthought.

The platform records:
- state transitions
- actuator commands
- confidence shifts
- disagreement events
- mission transitions
- safety interventions
- replay indexes

---

# 10.2 Core Telemetry Stack

```text
rosbag2
MCAP
ros2_tracing
Foxglove
Structured Event Streams
```

---

# 10.3 Replay Architecture

Replay systems support:
- incident reconstruction
- deterministic debugging
- transition analysis
- operator training
- validation testing

Replay fidelity is treated as an operational requirement.

---

# 10.4 Event Schema

All critical events include:

```json
{
  "timestamp": "",
  "run_id": "",
  "scenario_id": "",
  "node": "",
  "safety_state": "",
  "confidence_score": 0.0,
  "requested_motion": {},
  "final_motion": {},
  "reason_code": ""
}
```

---

# 11. Hardware Architecture

# 11.1 Physical Runtime Model

Initial deployment model:

```text
Raspberry Pi 5
+
Dedicated MCU Safety Layer
```

This split exists because:
Linux SBCs are not deterministic motor-control platforms.

---

# 11.2 micro-ROS Integration

micro-ROS provides:
- MCU communication
- ROS interoperability
- serial/UDP/TCP transport
- embedded watchdog coordination

---

# 11.3 Hardware Escalation Strategy

Jetson-class hardware is deferred until:
- perception workloads justify it
- replay architecture stabilizes
- observability matures
- operational safety proven

Hardware escalation must follow system requirements.

---

# 12. Repository Structure

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

# 13. Architectural Non-Goals

The platform intentionally avoids:
- uncontrolled AI autonomy
- camera-first architecture
- humanoid robotics
- generalized robotics research
- cloud-dependent autonomy
- multi-agent swarm systems
- end-to-end neural control
- uncontrolled reinforcement learning

The objective is operational trustworthiness.

---

# 14. Key Architectural Risks

## Primary Risks

### Observability Debt
Complexity exceeding introspection capability.

### Concurrency Nondeterminism
Unsafe callback ordering or race conditions.

### Simulator Drift
Simulation assumptions diverging from hardware reality.

### Safety Boundary Erosion
Mission logic bypassing safety arbitration.

### Premature AI Expansion
Perception complexity overwhelming architecture maturity.

---

# 15. Long-Term Evolution

Future expansion MAY include:
- camera pipelines
- learned anomaly detection
- advanced replay analytics
- multi-rover coordination
- Isaac Sim experimentation
- digital twin synchronization

These remain subordinate to:
- deterministic operation
- safety explainability
- replay fidelity
- operational transparency

---

# 16. Final Architectural Principle

Project Boundary is designed around a single governing principle:

> Autonomy must remain inspectable, bounded, replayable, and operationally explainable under degraded conditions.

The system is successful when:
- failures are understandable
- transitions are traceable
- safety behavior is deterministic
- replay reproduces causality
- operational trust exceeds novelty