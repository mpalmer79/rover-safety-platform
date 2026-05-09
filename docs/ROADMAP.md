# Implementation Roadmap

## 1. Project Vision

The Autonomous Safety Validation Rover Platform is a simulation-first robotics platform for validating deterministic autonomous rover behavior under degraded operational conditions.

The platform succeeds when:

- failures are bounded and explainable
- transitions are traceable
- safety behavior is deterministic
- replay reproduces causality
- operational trust exceeds novelty

This roadmap defines the phased path from architecture authority to working hardware integration. It is intentionally conservative on perception scope and aggressive on safety, observability, and replay.

This document is a controlling document. Phase order, gates, and acceptance criteria are not advisory.

---

## 2. Phase Gate Discipline

Each phase has:

- Objectives
- Deliverables
- Acceptance Criteria
- Risks
- Deferred Work
- Portfolio Signal

A phase is complete when all acceptance criteria are demonstrably met against pinned scenarios and recorded runs. A phase is not complete because the work feels done; it is complete when the run directories exist and the validators pass.

Skipping a phase, partially completing a phase, or working ahead of a phase requires an ADR.

---

## 3. Phase 0: Architecture Authority Layer

### Objectives

- Establish the controlling documents that govern all later implementation work.
- Make the safety authority model, ODD, event model, fault injection contract, replay contract, and testing strategy explicit and consistent.
- Record the major architectural decisions as ADRs.

### Deliverables

- `docs/ODD.md`
- `docs/SAFETY_MODEL.md`
- `docs/EVENT_MODEL.md`
- `docs/FAULT_INJECTION.md`
- `docs/REPLAY_SYSTEM.md`
- `docs/SYSTEM_CONTEXT.md`
- `docs/TESTING_STRATEGY.md`
- `docs/ROADMAP.md`
- `docs/adr/ADR-001` through `docs/adr/ADR-005`

### Acceptance Criteria

- All documents above exist and are internally consistent.
- No document contradicts `ARCHITECTURE.md`.
- The safety authority hierarchy is unambiguous.
- The event envelope is fully specified, including required fields and example payloads.
- The fault injection contract explicitly forbids direct mutation of `/safety/state`.
- The replay contract specifies required topics, required events, and storage layout.
- The roadmap defines acceptance gates for every later phase.

### Risks

- Premature commitment to runtime decisions that will be revisited later.
- Inconsistencies between this layer and `ARCHITECTURE.md`.
- Document sprawl without enforcement in code.

### Deferred Work

- Runtime code.
- Workspace scaffolding (`rover_ws/`).
- Simulator world authoring.
- CI configuration.

### Portfolio Signal

- Demonstrates serious systems thinking.
- Demonstrates discipline around safety boundaries.
- Demonstrates understanding that documentation is an architectural artifact, not a deliverable byproduct.

---

## 4. Phase 1: Gazebo Simulation Bringup

### Objectives

- Stand up a reproducible Gazebo Harmonic environment on Ubuntu 24.04 with ROS 2 Jazzy.
- Bring up a differential-drive rover description with the MVP sensor stack (2D LiDAR, wheel encoders, IMU, contact sensor).
- Establish the workspace layout and the message contracts for sensors and motion.
- Establish the rosbag2 / MCAP recording defaults.

### Deliverables

- `rover_ws/` workspace with:
  - `rover_msgs`
  - `rover_description`
  - `rover_bringup`
  - `rover_sim_gazebo`
  - `rover_sensor_adapters`
  - `rover_observability` (recording-only at this phase)
- A Gazebo Harmonic world that satisfies `docs/ODD.md` for an indoor or semi-structured outdoor scene.
- `ros_gz_bridge` configuration mapping simulator topics to ROS 2 topics consistent with the contract.
- Default recording configuration that captures the topics required by `docs/REPLAY_SYSTEM.md`.

### Acceptance Criteria

- The simulator launches deterministically from a pinned launch file.
- Sensor topics publish at their configured rates.
- Wheel encoders, IMU, and 2D LiDAR are visible in Foxglove.
- A short teleoperated drive can be recorded as an MCAP bag and replayed.
- A run directory is produced that satisfies the storage layout in `docs/REPLAY_SYSTEM.md` (bags only; events come in later phases).
- No safety supervisor exists yet; teleop is permitted only in operator-presence mode and is logged.

### Risks

- ros_gz_bridge regressions across simulator versions.
- Drift between simulator topic types and the canonical message contract.
- TF tree mistakes that hide in early development and surface during replay.

### Deferred Work

- Autonomy.
- Safety supervisor.
- Fault injection.

### Portfolio Signal

- Demonstrates ability to set up a non-trivial ROS 2 Jazzy + Gazebo Harmonic environment from a clean Ubuntu 24.04 installation.
- Demonstrates the discipline of recording-by-default.

---

## 5. Phase 2: Deterministic Autonomy Core

### Objectives

- Add the autonomy stack that lets the rover perform bounded missions without yet enforcing safety supervision.
- Establish lifecycle-managed nodes for state estimation, world modeling, and mission orchestration.
- Establish the `/cmd_vel_requested` pathway as the only motion-request channel from mission to arbitration.
- Begin emitting structured events for lifecycle and mission transitions.

### Deliverables

- `rover_state_estimation` using `robot_localization`.
- `rover_world_model` (occupancy grid or equivalent, scoped to MVP).
- `rover_mission_bt` using `BehaviorTree.CPP`.
- A minimal `rover_safety_supervisor` skeleton that publishes `/cmd_vel_authorized` as a passthrough of `/cmd_vel_requested` clamped to `ACTIVE_NORMAL` limits, with `/safety/state` always reporting `ACTIVE_NORMAL`. This is a placeholder, clearly marked, and replaced in Phase 3.
- A `rover_hw_gateway` (simulation gateway) that subscribes only to `/cmd_vel_authorized` and forwards to the simulator.
- Basic event emission for lifecycle and mission transitions.

### Acceptance Criteria

- The rover navigates between a small number of waypoints in a pinned simulator world.
- All motion flows through `/cmd_vel_requested` then `/cmd_vel_authorized` then the gateway.
- The hardware gateway has no subscription to `/cmd_vel_requested`.
- Lifecycle and mission transitions appear in the event stream and replay.
- A scenario re-run reproduces the event timeline within deterministic replay limits.

### Risks

- Implicit coupling between mission and arbitration that bypasses the architecture.
- Premature complexity in the world model.
- Scope creep into perception.

### Deferred Work

- Real safety enforcement.
- Fault injection.
- Recovery semantics.

### Portfolio Signal

- Demonstrates lifecycle-managed ROS 2 design.
- Demonstrates a clean mission/arbitration separation even before safety enforcement is real.

---

## 6. Phase 3: Safety Supervision and Degraded Modes

### Objectives

- Replace the placeholder supervisor with a real implementation of the safety state machine defined in `docs/SAFETY_MODEL.md`.
- Implement watchdogs, freshness gates, motion arbitration, and degraded-mode semantics.
- Implement the operator E-stop pathway.
- Implement fault injection and exercise the supervisor against the MVP fault classes.

### Deliverables

- `rover_safety_supervisor` with the full state machine and all transitions.
- Watchdog registry and freshness gates for LiDAR, IMU, encoders, gateway, TF.
- Motion arbitration that clamps requested commands to per-state limits.
- Operator E-stop pathway and `E_STOP_LATCHED` semantics.
- `rover_fault_injection` implementing the MVP fault classes from `docs/FAULT_INJECTION.md`.
- Scenario library exercising each fault class.

### Acceptance Criteria

- The supervisor's behavior matches `docs/SAFETY_MODEL.md` for every defined transition.
- Each MVP fault class produces the expected events and the expected safety response, captured in a recorded run.
- `E_STOP_LATCHED` cannot be cleared except by an explicit operator reset.
- `RECOVERY` revalidates inputs and refuses to restore `ACTIVE_NORMAL` if a gate is unhealthy.
- No subsystem other than the supervisor publishes to `/cmd_vel_authorized`.
- Fault injection cannot transition `/safety/state` directly. Negative tests assert this.
- A reviewer can identify the cause of any safety transition from the event stream alone.

### Risks

- Subtle freshness or watchdog races.
- Over-coupled supervisor implementation that mixes mission concerns into safety.
- Hidden bypass paths via private topics or services.

### Deferred Work

- Hardware bring-up.
- Perception expansion.
- Sim-vs-hardware parity.

### Portfolio Signal

- Demonstrates safety-supervisor authority enforced by architecture, not just by convention.
- Demonstrates fault-driven validation as a first-class capability.
- Demonstrates degraded-mode operation as bounded behavior, not as ad-hoc fallback.

---

## 7. Phase 4: Replay, Telemetry, and Incident Reconstruction

### Objectives

- Bring the replay subsystem to full conformance with `docs/REPLAY_SYSTEM.md`.
- Establish the run directory layout, event validators, and incident summary tooling.
- Establish saved Foxglove layouts for safety, motion arbitration, and fault timelines.
- Make replay validation part of CI for representative scenarios.

### Deliverables

- `rover_observability` with run lifecycle CLI, event validator, and incident summary generator.
- `runs/` directory layout populated by every recorded scenario.
- Saved Foxglove layouts checked into the repository.
- CI job that validates a representative recorded run against the event schema.
- A small set of canonical scenarios with reference event timelines used for regression replay.

### Acceptance Criteria

- Every CI-validated recorded run produces a directory matching `docs/REPLAY_SYSTEM.md` section 9.
- Event validators pass on every run referenced by tests.
- Incident summaries are generated mechanically and are reviewer-readable.
- Saved Foxglove layouts open against representative bags without manual reconfiguration.
- Determinism evaluations exist for at least three scenarios.

### Risks

- Tooling drift between Foxglove layout files and recorded topic names.
- Determinism degradations that surface only in long runs.
- Storage growth without a retention policy.

### Deferred Work

- Cloud or networked storage.
- Cross-machine replay coordination.
- Long-term archival.

### Portfolio Signal

- Demonstrates that observability and replay are architectural subsystems, not afterthoughts.
- Provides reviewer-facing artifacts: incident summaries and Foxglove layouts.

---

## 8. Phase 5: Bench Hardware Integration

### Objectives

- Integrate the platform with bench hardware: a Raspberry Pi 5 class SBC and a dedicated MCU safety layer.
- Validate sim-vs-hardware parity for the MVP sensor stack and motion arbitration.
- Validate the hardware-allowed subset of fault classes against the bench rover.
- Establish hardware-specific safety procedures for operator presence.

### Deliverables

- `rover_hw_gateway` hardware variant.
- MCU safety-layer firmware with command timeout and basic actuator decay-to-zero.
- micro-ROS or narrow MCU protocol bridge between SBC and MCU.
- Hardware sensor adapters mapping physical devices to the canonical message contract.
- Bench operator runbook including E-stop placement, allowed fault classes, and reset procedure.

### Acceptance Criteria

- Bench rover executes a teleoperated drive under the safety supervisor with the same `/cmd_vel_authorized` path used in simulation.
- The MCU enforces command timeout independently of the SBC.
- Hardware-allowed fault classes (per `docs/FAULT_INJECTION.md` section 12) produce the expected safety responses.
- A run directory is produced for hardware bench tests using wall-clock time and is replay-validated.
- Sim-vs-hardware parity is documented: which message contracts match exactly, which are bridged, and where parity is partial.

### Risks

- SBC scheduling jitter that violates assumed control loop timing.
- MCU firmware bugs causing actuator delays.
- Mismatch between simulated and physical sensor characteristics that breaks supervisor thresholds.

### Deferred Work

- Camera-class perception.
- Outdoor GNSS-based autonomy.
- Multi-rover coordination.
- Jetson-class compute.

### Portfolio Signal

- Demonstrates a Linux SBC + MCU split that respects determinism boundaries.
- Demonstrates that the same safety contract holds across simulation and hardware.

---

## 9. Phase 6: Optional Perception Expansion

### Objectives

- Expand perception scope only when justified by mission needs.
- Add camera-based perception, deeper world modeling, or limited outdoor autonomy as candidate work, gated by ADR.

### Deliverables (candidate, not committed)

- A perception-class compute decision: continue on Pi 5, or escalate to Jetson, recorded as an ADR.
- Camera adapters and any associated safety thresholds.
- Optional GNSS adapter for bounded outdoor scenarios.
- Expanded ODD with new conditions, gates, and exit triggers.

### Acceptance Criteria

- Each new perception capability has an ADR.
- The ODD is updated before any new capability is enabled in a recorded run.
- The supervisor's freshness and disagreement gates are extended to cover new sensors.
- The replay system records and validates the new sensor topics.
- No safety bypass is introduced; the safety supervisor remains the only authorizer of motion.

### Risks

- Scope creep into AI-heavy perception.
- Hardware escalation without operational justification.
- ODD widening without corresponding test coverage.

### Deferred Work

- End-to-end neural control.
- Multi-rover coordination beyond bounded telemetry sharing.
- Cloud-dependent autonomy.

### Portfolio Signal

- Demonstrates restraint in scope expansion.
- Demonstrates that capability growth is gated by architecture, not by enthusiasm.

---

## 10. Cross-Phase Risks

| Risk | Mitigation |
|---|---|
| Observability debt | Replay validators in CI; refuse merges that break required-event coverage. |
| Concurrency nondeterminism | Bounded executors; targeted `ros2_tracing` runs on regressions. |
| Simulator drift | Pin simulator versions in `metadata.json`; treat unpinned runs as non-replayable. |
| Safety boundary erosion | Architectural separation of `/cmd_vel_requested` and `/cmd_vel_authorized`; contract tests; review gates. |
| Premature AI expansion | Perception expansion requires an ADR and an ODD update. |

---

## 11. Deferred Features (Cross-Phase)

The following are deferred until a phase explicitly opens them, and require an ADR and an ODD update:

- camera-first perception
- visual SLAM
- GNSS-based outdoor autonomy
- multi-rover coordination
- Isaac Sim integration
- Jetson-class baseline compute
- cloud-dependent autonomy
- continuous learning at runtime
- end-to-end neural control

---

## 12. Portfolio Value Summary

The roadmap is structured to produce reviewer-facing artifacts at every phase:

| Phase | Reviewer-facing artifact |
|---|---|
| 0 | Architecture authority documents and ADRs |
| 1 | Reproducible simulator launch, recorded teleop runs |
| 2 | Lifecycle-managed autonomy with clean mission/arbitration split |
| 3 | Safety supervisor enforcing the state machine, fault-driven validation runs |
| 4 | Incident summaries, Foxglove layouts, replay-validated CI |
| 5 | Hardware bench parity with documented sim-vs-hardware mapping |
| 6 | Discipline around perception expansion, recorded as ADRs |

A reviewer should be able to enter the repository at any phase and find a coherent story: what the system does, where its boundaries are, how failures are handled, and how a specific incident can be reconstructed.
