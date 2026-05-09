# ADR-002: Gazebo Harmonic Selection

## Status
Accepted

## Context

The platform is simulation-first. The simulator is the primary integration surface for the MVP and remains a peer environment to bench hardware throughout the platform's life. The choice of simulator is therefore a foundational decision, not a tooling preference.

Required properties of the simulator:

- ROS 2 Jazzy alignment, with a stable bridge to the ROS 2 graph
- ROS-native simulation path that does not require custom adapters per sensor
- Mature physics and sensor simulation suitable for differential-drive rovers, 2D LiDAR, IMU, wheel encoders, and contact sensors
- Plugin ecosystem for simulating faults at the simulator level where appropriate (e.g., wheel slip)
- `ros_gz_bridge` support for mapping simulator topics to ROS 2 topics consistent with the platform's message contracts
- Reasonable practical risk profile for an MVP team that must reach a working scenario in a bounded time

Alternatives considered:

- Webots: capable simulator with ROS 2 support, but a smaller ROS-native ecosystem and weaker alignment with the broader Gazebo / ROS toolchain.
- PyBullet: excellent for control research and lightweight tasks, but lacks a ROS-native sensor and topic surface; building one for a serious safety platform is unjustified scope.
- Isaac Sim: powerful, but operationally heavier, dependent on specific GPU classes, and more complex to pin and reproduce. Higher practical risk for an MVP team. Considered as a future option only when perception workloads justify it.
- Gazebo Classic: end-of-life relative to Gazebo Harmonic and not aligned with ROS 2 Jazzy.

## Decision

The platform uses **Gazebo Harmonic** as the primary simulator.

`ros_gz_bridge` is the bridging mechanism between the simulator and the ROS 2 graph. The simulator publishes sensor topics and consumes actuator commands through the bridge. ROS 2 nodes interact only with the bridged topics, never with simulator-internal state.

## Consequences

### Positive

- Aligned with ROS 2 Jazzy and Ubuntu 24.04.
- Native ROS-side topic surface via `ros_gz_bridge` requires minimal custom integration for the MVP sensor stack.
- Plugin ecosystem supports simulator-level effects that are useful for fault injection (e.g., simulated wheel slip).
- Lower practical risk for an MVP than Isaac Sim, both in setup and in long-term reproducibility.
- Compatible with deterministic launch orchestration.
- `/clock` publication is supported and used as the primary timeline for replay where applicable.

### Negative

- Higher fidelity perception simulation (e.g., photorealistic cameras) is weaker than in Isaac Sim. Acceptable, because camera-first perception is deferred.
- `ros_gz_bridge` itself is a moving target; mapping issues across simulator versions must be tracked.
- Some advanced robotics tooling targets Isaac Sim first; the platform may pay an "ecosystem ramp" later if those tools become required.

### Neutral

- Bench hardware bring-up (Phase 5) does not depend on the simulator. Choosing Gazebo Harmonic does not constrain hardware decisions beyond what the message contracts already imply.

## Alternatives Considered

| Alternative | Reason rejected |
|---|---|
| Webots | Capable, but smaller ROS-native ecosystem; weaker alignment with the broader ROS 2 / Gazebo toolchain. |
| PyBullet | No ROS-native sensor and topic surface. Building one is out of scope for an MVP. |
| Isaac Sim | Higher practical risk for an MVP. GPU dependence and reproducibility complexity outweigh fidelity gains for a non-perception-first platform. May be revisited under ADR for perception workloads. |
| Gazebo Classic | End-of-life relative to Harmonic; not aligned with ROS 2 Jazzy. |

## Follow-up Work

- Pin the Gazebo Harmonic version used by CI and bench developers in `metadata.json` per `docs/REPLAY_SYSTEM.md`.
- Document the `ros_gz_bridge` mapping in `rover_sim_gazebo` so simulator and ROS 2 topics are demonstrably consistent.
- Establish a reduced-fidelity world that runs in CI within a bounded time budget; preserve the higher-fidelity worlds for full simulation tests.
- Revisit Isaac Sim only if and when perception expansion (Phase 6) justifies it, with its own ADR.
