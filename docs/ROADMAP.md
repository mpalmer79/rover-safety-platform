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

### Status Snapshot

| Phase | Status |
|---|---|
| Phase 0 — Architecture Authority Layer | Implemented |
| Phase 1A — Deterministic Autonomy Simulation Core (Python backend) | Implemented under `backend/` |
| Phase 1B — ROS 2 + Gazebo Harmonic Simulation Bringup | Implemented under `rover_ws/` (static-validation tests pass; end-to-end Gazebo launch requires a Jazzy host — see `rover_ws/tests/manual.md`) |
| Phase 1C — Runtime Validation, Operational Hardening, and Integration Verification | Implemented; see section 3c |
| Phase 2 — Deterministic Autonomy Core (ROS 2) | Pending |
| Phase 3 — Safety Supervision and Degraded Modes (ROS 2) | Pending |
| Phase 4 — Replay, Telemetry, and Incident Reconstruction (ROS 2 / Foxglove) | Pending |
| Phase 5 — Bench Hardware Integration | Pending |
| Phase 6 — Optional Perception Expansion | Pending |

Phase 1A is a pre-ROS-2 software foundation. It implements the safety
authority model, motion arbitration, freshness gates, watchdogs,
confidence scoring, fault injection, structured event emission, run
recording, and a deterministic scenario engine entirely in Python with
no external runtime dependencies. The contracts established in this
foundation (events, motion authority, fault injection boundaries,
replay layout) are the same contracts the ROS 2 implementation will
honour.

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

## 3a. Phase 1A: Deterministic Autonomy Simulation Core

### Status

Implemented under `backend/`. See `backend/README.md`.

### Objectives

- Establish a deterministic, Python-only software foundation for the
  safety authority model, fault injection, observability, and replay.
- Make the safety supervisor, motion arbitration, freshness gates,
  watchdog registry, confidence scorer, and fault injector all
  testable in isolation, before any ROS 2 dependencies are introduced.
- Provide a clean ROS-compatible domain boundary so the Phase 1
  ROS 2 / Gazebo integration can plug into the existing types and
  events without redesign.

### Deliverables

- Domain layer (`backend/app/domain/`): enums, identifiers, time
  abstractions, motion commands, rover state, sensor readings,
  events, faults, scenarios, replay metadata.
- Safety layer (`backend/app/safety/`): allowed transition table,
  freshness evaluator, confidence scorer, motion arbiter, watchdog
  registry, full safety supervisor.
- Simulation engine (`backend/app/simulation/`): manual clock,
  differential-drive vehicle model, deterministic sensor simulator,
  scenario runner, end-to-end engine.
- Fault injection subsystem (`backend/app/faults/`): fault profiles
  for all nine MVP fault classes; injector that perturbs inputs and
  timing without mutating safety state.
- Telemetry (`backend/app/telemetry/`): synchronous event bus,
  in-memory event store, JSONL run recorder writing the canonical
  run directory layout from `docs/REPLAY_SYSTEM.md`.
- Replay (`backend/app/replay/`): manifest, recorder facade, run
  loader.
- Optional FastAPI gateway (`backend/app/api/`): `/health`,
  `POST /simulation/run`, `GET /runs`, `GET /runs/{id}`,
  `GET /runs/{id}/events`, `GET /runs/{id}/summary`. Disabled
  unless the `api` extra is installed.
- Five bundled scenarios (nominal, stale-LiDAR, odometry divergence,
  command timeout, E-stop latched).
- Three runnable example scripts under `backend/examples/`.
- Pytest suite (82 tests at the time of writing) covering events,
  transitions, arbitration, freshness, confidence, fault injection,
  replay, and the simulation engine.

### Acceptance Criteria

- Authority model enforced: only the supervisor produces
  `AuthorizedMotionCommand`; the gateway only consumes it.
- Faults alter inputs and timing only; an explicit test asserts the
  fault subsystem emits no `safety_transition.*` events itself.
- Every safety state transition is reachable through scenario runs
  and is recorded to `events.jsonl`.
- A pinned scenario re-run produces the same event timeline.
- Run directories conform to `docs/REPLAY_SYSTEM.md` section 9.

### Risks

- The Python core will diverge from the future ROS 2 implementation if
  the contracts (event envelope, motion topics, fault classes) are not
  kept in sync. Mitigated by treating these documents as binding.
- Confidence scoring uses fixed weights chosen for explainability,
  not for fidelity. They will need tuning when real sensor data is
  available.

### Deferred Work

- Real ROS 2 nodes, real Gazebo Harmonic integration, real rosbag2 /
  MCAP recording, Foxglove integration.

### Portfolio Signal

- Demonstrates a deterministic, replay-grade safety architecture
  enforced by types and tests, independent of any robotics framework.
- Demonstrates that the same contracts can be transplanted into ROS 2
  without redesign.

---

## 3b. Phase 1B: ROS 2 + Gazebo Harmonic Simulation Bringup

### Status

Implemented under `rover_ws/`. See `rover_ws/README.md`.

### Objectives

- Wrap the deterministic Phase 1A runtime with a ROS 2 Jazzy graph and
  a Gazebo Harmonic simulation, without ceding architectural authority
  to either layer.
- Establish a colcon workspace, custom interfaces, the rover URDF, the
  ros_gz_bridge configuration, sensor adapter nodes, the safety bridge
  node (which embeds the deterministic supervisor), and the
  observability layer.
- Preserve the motion authority pipeline: only `/cmd_vel_authorized`
  reaches the Gazebo diff-drive plugin, and only the safety bridge
  publishes that topic.

### Deliverables

- `rover_ws/src/rover_msgs` — six custom interfaces (`SafetyState`,
  `MotionAuthorization`, `SystemHealth`, `SensorHealth`, `FaultEvent`,
  `ReplayMarker`).
- `rover_ws/src/rover_description` — Xacro URDF with chassis, two drive
  wheels, caster, LiDAR, IMU, and contact links; Gazebo plugin
  declarations.
- `rover_ws/src/rover_sim_gazebo` — bounded indoor validation world,
  `ros_gz_bridge` YAML, simulation and rover-spawn launches.
- `rover_ws/src/rover_sensor_adapters` — four adapter nodes (LiDAR,
  IMU, odometry, contact) that publish per-sensor `SensorHealth`
  summaries and re-publish raw streams under the
  `/rover/sensors/<name>/normalized` namespace.
- `rover_ws/src/rover_safety_bridge` — `SafetyBridgeCore` (pure logic)
  + `safety_bridge_node` (rclpy facade). The core hosts
  `app.safety.SafetySupervisor` from the Python backend; the node is
  the only producer of `/cmd_vel_authorized` in the system.
- `rover_ws/src/rover_observability` — `run_manager` (allocates run
  directories, publishes `ReplayMarker` records), `event_recorder`
  (subscribes to `/safety/events` and appends validated JSON to
  `events.jsonl`), and the rosbag2 record launch integration.
- `rover_ws/src/rover_bringup` — top-level launches: `full_system`,
  `simulation`, `safety_runtime`, `observability`, `rover_spawn`.
- `rover_ws/tests/` — pytest suite that runs without ROS 2 / Gazebo:
  manifests, message definitions, URDF structure, ros_gz_bridge YAML,
  launch files, node modules, and the `SafetyBridgeCore` integration
  contract. End-to-end Jazzy / Gazebo validation steps live in
  `rover_ws/tests/manual.md`.

### Acceptance Criteria

- All seven packages exist with valid manifests and build files.
- The URDF declares the documented links and joints; the Gazebo
  plugin block subscribes to `/cmd_vel_authorized` only.
- `ros_gz_bridge.yaml` forwards `/cmd_vel_authorized` ROS_TO_GZ and
  forwards none of `/cmd_vel`, `/cmd_vel_requested` to Gazebo. A test
  enforces this.
- `SafetyBridgeCore` produces `AuthorizedMotionCommand` values whose
  `source` field is `safety.supervisor.arbitration`. A test enforces
  this.
- Operator E-stop latches and is not self-cleared by the supervisor.
- A pytest run in this repository (without ROS 2 / Gazebo) passes
  every static-validation test.
- A Jazzy host running `colcon build && ros2 launch rover_bringup
  full_system.launch.py` produces a populated `runs/<run_id>/` with
  `metadata.json`, `events.jsonl`, an MCAP bag, and the expected
  `safety_transition.entered` event sequence (manual validation, see
  `rover_ws/tests/manual.md`).

### Risks

- The Phase 1B implementation cannot be exercised end-to-end inside
  this repo's CI sandbox: ROS 2 and Gazebo are not installed there.
  Static validation catches structural regressions; the manual
  acceptance script catches behavioural regressions on a Jazzy host.
- The `app.*` Python package must be importable to the ROS nodes.
  `rover_safety_bridge` and `rover_observability` declare it as a
  pip-installed dependency (`rover-safety-platform-backend>=0.1.0`).
  Forgetting `pip install -e ../backend` before `colcon build` is the
  most likely setup error and should be checked in `manual.md`.
- The diff_drive plugin's exact topic conventions evolve across
  Gazebo Harmonic patch releases; the URDF pins
  `gz-sim-diff-drive-system` and the bridge YAML pins the
  ROS-side topic name, so any drift is contained to the URDF.

### Deferred Work

- A second-stage Phase 1 / 2 / 3 / 4 will replace static-validation
  tests with launch-based integration tests that actually start
  Gazebo and assert TF / topic behaviour.
- BehaviorTree.CPP-based mission orchestration.
- Nav2 integration (gated by an ADR; out of scope for the ODD until
  the supervisor's freshness gates cover Nav2's outputs).

### Portfolio Signal

- Demonstrates that the deterministic core remains authoritative when
  wrapped in a ROS 2 graph: the supervisor's logic is reused verbatim
  rather than duplicated.
- Demonstrates topic-level architectural enforcement: the supervisor's
  authority is visible in the bridge YAML, in the URDF plugin
  configuration, and in the contract tests under `rover_ws/tests/`.

---

## 3c. Phase 1C: Runtime Validation, Operational Hardening, and Integration Verification

### Status

Implemented. See `tools/`, `backend/app/validation/`,
`backend/app/diagnostics/`, and
`rover_ws/src/rover_runtime_diagnostics/`.

### Objectives

- Move the integration from "structurally correct" to "operationally
  trustworthy": every Phase 1B contract is now exercised end-to-end by
  the deterministic engine against the seven Phase 1C scenarios, and
  every contract has a CLI-runnable validator under `tools/`.
- Add live runtime diagnostics: a `rover_runtime_diagnostics` package
  that monitors topic freshness, ros_gz_bridge health, TF graph, and
  publishes an aggregated `/diagnostics/runtime_summary`.
- Harden the launch hierarchy: deterministic startup ordering,
  argument validation (`record_bag`, `enable_diagnostics`), and a
  `runtime_validation.launch.py` that attaches diagnostics to a
  running stack without restarting it.
- Build a scenario validation suite that drives every required
  scenario through the deterministic engine and asserts each outcome,
  producing replay-validated run directories under
  `runs/scenario_suite/`.

### Deliverables

- `backend/app/validation/` — five validators:
  - `replay_validator.py` (run directory layout, metadata schema,
    `events.jsonl` schema, per-producer ordering, linked-event
    resolution),
  - `event_validator.py` (standalone event-stream validator with
    duplicate-id detection),
  - `bridge_validator.py` (ros_gz_bridge YAML against ADR-004),
  - `tf_validator.py` (URDF link/joint topology, root, reachability),
  - `safety_pipeline_validator.py` (six in-process supervisor
    invariants: only-supervisor authorisation, SAFE_STOP zero motion,
    E_STOP_LATCHED persistence, clamping events, fault subsystem
    cannot emit `safety_transition.*`, AuthorizedMotionCommand
    constructed only inside the arbiter),
  - `scenario_suite.py` (runs the seven Phase 1C scenarios and
    validates each).
- `backend/app/diagnostics/` — pure-logic monitors:
  - `topic_monitor.py` (`TopicFreshnessMonitor`, `TopicSpec`,
    `DEFAULT_TOPIC_SPECS`),
  - `bridge_health.py` (`BridgeHealthMonitor`),
  - `runtime_summary.py` (`HealthReport`, `HealthSeverity`,
    `RuntimeSummary`, `aggregate_health`).
- `tools/` — six CLI scripts:
  `validate_bridge_topics.py`, `validate_tf_tree.py`,
  `validate_event_integrity.py`, `validate_replay_run.py`,
  `validate_safety_pipeline.py`, `run_scenario_suite.py`. Each accepts
  `--json` for CI piping.
- New scenarios:
  `backend/scenarios/bridge_disconnect_safe_stop.json` and
  `backend/scenarios/wheel_slip_degraded_mode.json`.
- `rover_ws/src/rover_runtime_diagnostics/` — ament_python package
  with four nodes (`topic_freshness_node`, `bridge_health_node`,
  `tf_validator_node`, `runtime_summary_node`) plus
  `runtime_diagnostics.launch.py`.
- Hardened `full_system.launch.py` and `safety_runtime.launch.py`
  with deterministic timer-based ordering, declared
  `enable_diagnostics` and `record_bag` arguments, and
  `LogInfo` markers for every subsystem startup.
- New `rover_bringup/launch/runtime_validation.launch.py`.
- Backend tests: `test_diagnostics_core.py`,
  `test_validation_module.py`, `test_scenario_suite.py`.
- rover_ws tests: `test_runtime_diagnostics.py`; updates to
  `test_package_manifests.py` and `test_launch_files.py` to require
  the new package and launch.

### Acceptance Criteria

- The seven required scenarios all pass through the deterministic
  engine with the documented final state, with replay validation
  passing on each run directory.
- The safety-pipeline validator's six invariants hold (the validator
  exits 0).
- The bridge YAML validator rejects any attempt to bridge `/cmd_vel`
  or `/cmd_vel_requested`.
- The URDF validator rejects unreachable links.
- The diagnostics core produces consistent freshness severity under
  the documented warmup / warn / error thresholds.

### Risks

- The runtime diagnostics nodes import `rclpy` and so cannot be
  exercised in this repo's CI sandbox. They are AST-validated and
  their pure-logic core is fully tested. Behavioural validation on a
  Jazzy host is documented in `rover_ws/tests/manual.md`.
- The `wheel_slip` scenario reaches `ACTIVE_DEGRADED` only when paired
  with an additional signal (here: a small co-occurring `imu_bias`).
  Single-fault wheel-slip detection is a state-estimator concern and
  is intentionally deferred to Phase 2.
- The scenario suite produces real run directories; if disk space is
  constrained, point `--runs_root` at a path that the runner can
  delete and recreate (`clean=True` by default).

### Deferred Work

- Live launch-based integration tests (would require a Jazzy host in
  CI).
- Foxglove layout files for the new diagnostic topics (Phase 4).
- A `ros2_tracing`-based latency study of the safety pathway (Phase
  4).

### Portfolio Signal

- Demonstrates a runtime that is not just structurally correct but
  validated end-to-end through every documented scenario.
- Demonstrates a diagnostics subsystem that respects the safety
  authority boundary: the diagnostic monitors describe liveliness,
  not safety state.

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
