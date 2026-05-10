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
| Phase 2 — Mission Runtime & Deterministic Navigation Orchestration | Implemented; see section 3d |
| Phase 3 — Verification, Scenario Certification, and Evidence Generation | Implemented; see section 3e |
| Phase 4 — Live ROS 2 / Gazebo Runtime Verification and Evidence Capture | Implemented (static-only fall-back); see section 3f |
| Phase 5 — ROS Host Qualification and Continuous Runtime Validation | Implemented (static-only fall-back); see section 3g |
| Phase 6 — Incident Reconstruction, Telemetry Correlation, and Operational Replay Analysis | Implemented; see section 3h |
| Phase 7 — Live Foxglove Replay Integration and Operational Review Sessions | Implemented (static-only fall-back); see section 3i |
| Phase 8 — Replay Coverage Analytics and Cross-Incident Operational Intelligence | Implemented; see section 3j |
| Phase 9 — Source-to-Replay Regression Correlation and Reliability Impact Analysis | Implemented; see section 3k |
| Phase 10 — Reliability Programme Review and Longitudinal Governance | Implemented; see section 3l |
| Phase 3-ROS — Safety Supervision and Degraded Modes (ROS 2) | Pending |
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

## 3d. Phase 2: Mission Runtime & Deterministic Navigation Orchestration

### Status

Implemented. See `backend/app/mission/`, `backend/app/world_model/`,
the seven new `backend/scenarios/*_*.json` files, the new ROS
packages (`rover_mission_runtime`, `rover_world_model`,
`rover_mission_diagnostics`), and `tools/validate_mission_run.py`.

### Objectives

- Add a deterministic mission orchestration layer that produces
  bounded waypoint navigation, recovery behaviour, world-state
  awareness, and replayable mission execution — without conceding the
  safety supervisor's authority.
- Allow constrained Nav2 participation through a single architectural
  bridge (the velocity-clamp boundary), proving that the platform can
  use Nav2 controllers without ever putting Nav2 on the actuator
  path.
- Extend replay so a recorded run can be reconstructed at the mission
  level (state transitions, waypoint timeline, recovery engagements,
  world-model snapshots) in addition to the safety / sensor level.

### Deliverables

- `backend/app/mission/` — pure-logic mission runtime:
  - `enums.py` (`MissionState`, `RecoveryBehavior`, `WaypointStatus`),
  - `transitions.py` (allowed mission transitions with refusal events),
  - `waypoints.py` (`Waypoint`, `WaypointQueue`, `WaypointProgress`),
  - `constraints.py` (`MissionConstraints`, `evaluate_constraints`),
  - `controller.py` (deterministic geometric waypoint controller),
  - `recovery.py` (`RecoveryPolicy` with budgeted attempts),
  - `mission_plan.py` (`MissionPlan`),
  - `orchestrator.py` (`MissionOrchestrator`).
- `backend/app/world_model/` — bounded world model:
  - `keepout.py`, `boundaries.py`, `occupancy.py`, `snapshot.py`,
  - `world_model.py` (`WorldModel`, `HazardReport`).
- Seven new mission scenarios:
  `nominal_waypoint_patrol`, `waypoint_timeout_recovery`,
  `degraded_sensor_navigation`, `keepout_zone_violation`,
  `restricted_mode_navigation`, `safe_stop_during_active_mission`,
  `mission_abort_after_fault_escalation`.
- Extended `RunRecorder`: `mission_state_transitions.jsonl`,
  `waypoint_events.jsonl`, `recovery_events.jsonl`,
  `world_model_snapshots.jsonl`. Incident summaries now include
  mission lifecycle, completed/timed-out waypoints, and recovery
  engagements.
- Extended `EventCategory` with `mission_lifecycle`,
  `mission_waypoint`, `mission_recovery`, `world_model`. Six new
  ``rover_msgs`` interfaces.
- Three new ROS packages:
  - `rover_mission_runtime/mission_node.py` (embeds the orchestrator;
    sole producer of `/cmd_vel_requested`),
  - `rover_mission_runtime/nav2_velocity_clamp.py` (Nav2 boundary;
    accepts `/cmd_vel_nav2`, clamps to the per-state envelope,
    republishes onto `/cmd_vel_requested`),
  - `rover_world_model/world_model_node.py`,
  - `rover_mission_diagnostics/mission_diagnostics_node.py`.
- New launches:
  `rover_mission_runtime/launch/mission_runtime.launch.py`,
  `rover_mission_runtime/launch/nav2_clamp.launch.py`,
  `rover_world_model/launch/world_model.launch.py`,
  `rover_mission_diagnostics/launch/mission_diagnostics.launch.py`,
  `rover_bringup/launch/mission_only.launch.py`. The top-level
  `full_system.launch.py` accepts `enable_mission` and
  `mission_plan_path`.
- `tools/validate_mission_run.py` and
  `app.validation.mission_validator` (run-directory mission integrity).
- New backend tests: `test_mission_state.py`, `test_waypoints.py`,
  `test_mission_constraints.py`, `test_recovery_policy.py`,
  `test_world_model.py`, `test_orchestrator.py`,
  `test_mission_replay.py`. Scenario suite extended with the seven
  Phase 2 cases.
- New rover_ws test: `test_mission_runtime_packages.py`. Launch /
  manifest / message tests extended.

### Acceptance Criteria

- Mission runtime exists and reaches MISSION_COMPLETE on the nominal
  patrol scenario.
- Waypoint execution is deterministic across re-runs (verified in
  the scenario suite).
- Recovery executes for timeout, keepout, and operator paths; budget
  exhaustion forces MISSION_ABORT.
- Mission replay artefacts are present in every run directory and
  validated by `tools/validate_mission_run.py`.
- World model integrates keepout / restricted / boundary zones and
  emits `world_model.*` events.
- Safety authority remains centralized: source-level scan asserts
  the mission orchestrator never constructs ``AuthorizedMotionCommand``
  and the Nav2 clamp never references `/cmd_vel_authorized`.
- Mission diagnostics expose mission state, active waypoint,
  recovery counts, and world-model hazards on `/diagnostics/mission`.
- All 312 backend + rover_ws tests pass.
- All seven CLI tools exit 0.

### Risks

- The orchestrator's geometric controller is intentionally simple. A
  Nav2 controller is the supported path for production-class
  navigation; the orchestrator is the bounded path that survives in
  CI.
- The wheel-slip-only path still reaches `MISSION_COMPLETE`
  numerically because the platform has no state estimator; the
  scenario uses a co-occurring IMU bias to demonstrate
  ``MISSION_DEGRADED`` honestly. State-estimator-based slip detection
  remains future work.
- The ROS-side mission node reads the supervisor's confidence from
  `/safety/state` but does not see the live `SensorFrame`; the
  supervisor's freshness gates own that channel. The deterministic
  engine, by contrast, drives the orchestrator with the full
  `SensorFrame`. This asymmetry is intentional: ROS-side mission
  state should not duplicate sensor-level reasoning.

### Deferred Work

- Full Nav2 integration (`Nav2 lifecycle node bring-up, costmap,
  planner_server, controller_server) is out of scope; the velocity-
  clamp boundary is the agreed integration surface.
- BehaviorTree.CPP is intentionally not introduced; the orchestrator
  is a deterministic state machine + waypoint queue. A behaviour-tree
  layer is candidate Phase 3+ work if mission complexity warrants.
- Live launch-based integration tests still require a Jazzy host;
  manual.md instructions cover the end-to-end check.

### Portfolio Signal

- Demonstrates a mission orchestration layer that is deterministic by
  construction, replay-grade by design, and architecturally unable to
  bypass the safety supervisor.
- Demonstrates a Nav2 integration model that preserves all earlier
  contracts (only the supervisor authorises motion; only the gateway
  consumes authorised motion; only the bridge YAML forwards it to
  Gazebo).

---

## 3e. Phase 3: Verification, Scenario Certification, and Evidence Generation

### Status

Implemented. See `backend/app/verification/`,
`tools/audit_*.py`, `tools/verify_replay_integrity.py`,
`tools/generate_evidence.py`, `tools/generate_traceability.py`,
`tools/generate_verification_report.py`,
[`docs/VERIFICATION_STRATEGY.md`](VERIFICATION_STRATEGY.md),
[`docs/TRACEABILITY_MATRIX.md`](TRACEABILITY_MATRIX.md), and
[`docs/SCENARIO_VERIFICATION_REPORT.md`](SCENARIO_VERIFICATION_REPORT.md).

### Objectives

- Convert the platform from "implemented systems" into "engineering
  evidence". Every safety-critical guarantee is bound to a stable
  `REQ-*` ID, an architecture reference, an implementation, a test,
  a scenario, and an evidence artefact.
- Reuse — not replace — the Phase 1C / Phase 2 validators
  (`replay_validator`, `mission_validator`, `safety_pipeline_validator`,
  scenario suite). Phase 3 composes them into a verification surface
  that distinguishes ``passed``, ``failed``, ``partial``, ``skipped``,
  and ``not_executed``.
- Produce reproducible artefacts (JSON + Markdown) that a reviewer
  can scrub through to understand what was checked, where the
  evidence is, and what is intentionally out of scope.

### Deliverables

- `backend/app/verification/` — nine modules:
  - `acceptance.py` (status vocabulary + aggregation),
  - `requirements.py` (13 stable `REQ-*` requirements with
    architecture / implementation / test / scenario bindings),
  - `command_audit.py` (audits `commands.jsonl` against the safety
    contract: source provenance, forced-zero states, per-state
    limit envelopes, expired-request handling),
  - `safety_audit.py` (audits `events.jsonl` safety transitions
    against `app.safety.transitions`; enforces `E_STOP_LATCHED`
    and `SAFE_STOP` outbound restrictions),
  - `replay_integrity.py` (Phase 3 wrapper around the Phase 1C +
    Phase 2 validators),
  - `scenario_verifier.py` (per-scenario expectations + verifier),
  - `evidence.py` (per-scenario artefact directory + Markdown
    summary + events timeline),
  - `traceability.py` (registry-driven matrix to JSON + Markdown),
  - `report_generator.py` (`docs/SCENARIO_VERIFICATION_REPORT.md`).
- `tools/` — six new CLIs:
  - `audit_command_path.py`,
  - `audit_safety_transitions.py`,
  - `verify_replay_integrity.py`,
  - `generate_evidence.py`,
  - `generate_traceability.py`,
  - `generate_verification_report.py`.
- `verification/traceability.json`, `verification/verification_report.json`,
  `evidence/scenarios/<id>/...` — artefacts checked into the repo on
  the latest deterministic-engine run.
- `docs/VERIFICATION_STRATEGY.md`, `docs/TRACEABILITY_MATRIX.md`,
  `docs/SCENARIO_VERIFICATION_REPORT.md`.
- New backend tests: `test_requirements_registry.py`,
  `test_command_audit.py`, `test_safety_audit.py`,
  `test_scenario_verifier.py`, `test_evidence_and_traceability.py`.

### Acceptance Criteria

- Requirement registry exists with at least one requirement per
  category and stable IDs (REQ-SAFE-*, REQ-FAULT-*, REQ-REPLAY-*,
  REQ-MISSION-*, REQ-WORLD-*, REQ-DIAG-*, REQ-OP-*).
- Traceability matrix is generated from the registry plus a real
  verification run; every requirement appears once with status.
- Scenario verifier runs every Phase 1C / Phase 2 scenario and
  produces a `ScenarioVerification` with at least 8 checks each.
- Evidence directories are written per scenario with the documented
  artefact set.
- Command-path audit, safety-transition audit, and replay-integrity
  verifier all run as standalone tools and from inside the
  scenario verifier.
- Report distinguishes `passed`, `failed`, `partial`, `skipped`,
  and `not_executed` and surfaces failed-check details + known
  limitations.
- Tests cover the verification infrastructure (48 new tests).
- Safety authority model remains intact: the scenario verifier's
  `command_path_audit` would fail any scenario that bypasses the
  supervisor.

### Risks

- The verification layer reads only the deterministic engine's
  artefacts. ROS 2 / Gazebo runs on a Jazzy host produce
  interchangeable run directories that pass the same verifiers, but
  this Phase 3 implementation does not invoke those runs in CI; the
  Jazzy procedure stays in `rover_ws/tests/manual.md`.
- Requirements coverage is bounded by the requirement registry. A
  guarantee that has no `REQ-*` ID is invisible to the matrix; the
  registry must be expanded as the platform grows.
- The report's "passed" status reflects scenarios + tests only.
  Architecture, ADRs, and design rationale remain narrative
  documents; they are referenced but not parsed.

### Deferred Work

- Live launch-based ROS 2 verification in CI (still requires a
  Jazzy host).
- Foxglove-driven evidence: video / topic captures attached to
  evidence directories.
- Long-running soak scenarios.
- Cross-build artefact comparison (Phase 4 candidate).

### Portfolio Signal

- Demonstrates verification discipline appropriate for a
  safety-oriented robotics codebase: every guarantee has an ID, a
  test, a scenario, and an evidence artefact.
- Demonstrates honest reporting: skipped and not-executed checks
  are surfaced; the report explicitly disclaims certification.

---

## 3f. Phase 4: Live ROS 2 / Gazebo Runtime Verification and Evidence Capture

### Status

Implemented in this branch. Static-only mode runs in CI; live mode
requires a Jazzy host with Gazebo Harmonic.

### Objectives

- Prove the documented architectural guarantees against the live ROS 2
  graph (when a Jazzy host is available), not only via the
  deterministic engine.
- Capture honest evidence in `evidence/runtime/<run_id>/` whose status
  vocabulary matches Phase 3's (`passed`, `failed`, `partial`,
  `skipped`, `not_executed`).
- Provide a CI-friendly static-only fallback so the runtime contract
  is enforced even off Jazzy.

### Deliverables

- `backend/app/runtime_validation/` — pure-logic library declaring the
  expected topics, nodes, and TF frames, plus the static validator
  and the report renderer.
- `rover_ws/tools/_probe_common.py` — shared CLI helpers.
- `rover_ws/tools/launch_smoke_test.py` — bring up
  `rover_bringup full_system.launch.py` and verify the node graph.
- `rover_ws/tools/topic_probe.py` — verify required topics are
  advertised with the right type and freshness.
- `rover_ws/tools/tf_probe.py` — verify the TF tree links every
  expected frame to the documented root.
- `rover_ws/tools/command_path_probe.py` — verify only the
  safety bridge publishes `/cmd_vel_authorized`.
- `rover_ws/tools/runtime_capture.py` — drive a fault scenario and
  capture transitions; live capture is opt-in.
- `rover_ws/tools/live_runtime_validator.py` — orchestrates every probe
  and writes the aggregate `runtime-validation.{json,md}`.
- `docs/RUNTIME_VALIDATION_RUNBOOK.md` — developer-facing runbook.
- `docs/RUNTIME_VALIDATION_REPORT.md` — generated canonical report.
- `evidence/runtime/<run_id>/` — per-run evidence directory.
- `REQ-RUNTIME-001..005` and the corresponding traceability rows.

### Acceptance Criteria

- The static-only orchestrator returns a non-zero exit code when any
  static check fails, and writes the canonical Markdown report.
- The orchestrator marks every live-only probe as `not_executed` with
  an explicit reason on environments without rclpy / Gazebo.
- The runtime tests under
  `rover_ws/tests/test_runtime_validation_tooling.py` exercise the
  static-only path end-to-end without requiring ROS.
- The traceability matrix lists `REQ-RUNTIME-001..005`, each bound to
  at least one test and one evidence artefact.

### Risks

- Drift between the expected runtime contract and the actual launch /
  bridge / URDF artefacts. Mitigated by the static validator running
  in CI.
- Live probes false-failing during the launch settle period.
  Mitigated by configurable `--settle-seconds`.

### Deferred Work

- Live runtime fault-injection capture against the live ROS stack
  (currently `not_executed` with a reason; the deterministic engine
  path is exercised in static-only mode).
- Foxglove integration for visual replay of the runtime evidence is
  reserved for a later phase.

### Portfolio Signal

- Demonstrates discipline that distinguishes “the static workspace is
  consistent” from “the live graph behaved as documented.”
- Demonstrates a CI-friendly fallback that never claims live success
  unless live evidence was actually captured.

---

## 3g. Phase 5: ROS Host Qualification and Continuous Runtime Validation

### Status

Implemented in this branch. Static-only mode runs in CI; live mode
requires a self-hosted Jazzy + Gazebo Harmonic runner.

### Objectives

- Qualify a ROS 2 Jazzy host (Ubuntu, ROS, Gazebo, colcon, packages,
  workspace structure) before the runtime stack is launched.
- Orchestrate a complete qualification run: host -> Phase-4 probes ->
  scenario evaluation -> regression detection -> baseline comparison ->
  qualification report -> evidence index.
- Detect runtime regressions across runs via per-category baseline
  comparison.
- Publish CI workflows that distinguish static-only checks (every
  push) from self-hosted live qualification (manual / opt-in).

### Deliverables

- `backend/app/runtime_validation/host_qualification.py` — host
  qualifier (Ubuntu, ROS, Gazebo, colcon, packages, workspace,
  launch files, bridge config).
- `backend/app/runtime_validation/qualification_scenarios.py` —
  YAML scenario format + loader/validator.
- `backend/app/runtime_validation/baselines.py` — per-category
  baseline + diff classifier.
- `backend/app/runtime_validation/regression.py` — per-run regression
  detector.
- `backend/app/runtime_validation/evidence_index.py` — evidence
  index manifest.
- `backend/app/runtime_validation/qualification_report.py` —
  qualification report + live-runtime status renderer.
- `rover_ws/tools/qualify_ros_host.py` — host qualification CLI.
- `rover_ws/tools/compare_runtime_baseline.py` — baseline capture +
  comparison CLI.
- `rover_ws/tools/qualified_runtime_run.py` — qualification
  orchestrator.
- `qualification/scenarios/*.yaml` — six qualification scenario
  packs.
- `.github/workflows/{backend-tests,runtime-static-validation,docs-traceability,evidence-validation}.yml`
  + the manual `ros-jazzy-runtime.yml`.
- `docs/RUNTIME_QUALIFICATION_RUNBOOK.md` — operational runbook.
- `docs/RUNTIME_QUALIFICATION_REPORT.md` — generated canonical
  qualification report.
- `docs/LIVE_RUNTIME_STATUS.md` — generated short-form status page.
- `docs/EVIDENCE_INDEX.md` — generated evidence index.
- REQ-RUNTIME-006..010 with traceability rows.

### Acceptance Criteria

- The qualification orchestrator returns non-zero only on a `failed`
  aggregate; `not_executed` is honest reporting and does not fail CI.
- The orchestrator writes every documented evidence file even when
  some live probes are `not_executed`.
- The qualification report and live-runtime status report **label
  every check by origin** (`static-source`, `static-workspace`, or
  `live-runtime`) and never claim a static check as a live pass.
- The baseline comparator classifies each delta as
  `expected_difference`, `warning`, `regression`, or
  `critical_regression`. No regression is silently auto-ignored.
- Tests exercise host qualification, scenario validation, baseline
  comparison, regression detection, evidence indexing, and report
  rendering without requiring ROS.

### Risks

- Drift between qualification scenarios and the runtime contract.
  Mitigated by static workspace cross-references during evaluation.
- Self-hosted runner availability for live qualification. Mitigated
  by static-only mode remaining first-class.

### Deferred Work

- Foxglove integration for visual replay (Phase 6).
- Cross-run trend analysis on the evidence index.

### Portfolio Signal

- Demonstrates engineering qualification discipline: host
  qualification, scenario packs, baseline comparison, regression
  classification, and a CI workflow that does not fake live success.
- Demonstrates honest reporting: static and live evidence are
  distinguished in every artefact.

---

## 3h. Phase 6: Incident Reconstruction, Telemetry Correlation, and Operational Replay Analysis

### Status

Implemented in this branch. The package is read-only with respect
to runtime evidence and produces engineering analysis artefacts.

### Objectives

- Load runtime + scenario evidence and reconstruct deterministically
  ordered incident timelines.
- Build rule-based causality chains with explicit confidence levels;
  inferred links are labelled and missing links downgrade the chain.
- Classify incidents on three axes (severity, outcome, evidence
  status) using only the evidence; contradictions force `inconclusive`.
- Produce Markdown + JSON reports plus Mermaid timeline diagrams,
  Foxglove replay hints, and an evidence manifest.
- Support cross-incident comparison and a filterable index.

### Deliverables

- `backend/app/incident_analysis/` — 11 modules: `models`, `loader`,
  `normalizer`, `timeline`, `causality`, `classifier`, `reporter`,
  `foxglove`, `compare`, `index`, `reconstruct`.
- `rover_ws/tools/reconstruct_incident.py` — CLI for incident
  reconstruction.
- `rover_ws/tools/index_incidents.py` — CLI for the incident index.
- `rover_ws/tools/compare_incidents.py` — CLI for cross-incident
  comparison.
- `foxglove/layouts/incident-review-layout.json` — canonical
  Foxglove layout (5 panels).
- `incidents/` — directory layout for retained bundles + comparisons.
- `docs/INCIDENT_RECONSTRUCTION.md`, `docs/INCIDENT_ANALYSIS_STRATEGY.md`,
  `docs/FOXGLOVE_REPLAY_WORKFLOW.md`, `docs/INCIDENT_INDEX.md` (generated).
- REQ-INCIDENT-001..005 with traceability rows.

### Acceptance Criteria

- The reconstructor never mutates source evidence.
- Every incident report carries the certification disclaimer
  verbatim.
- Inferred causal links are labelled `inferred=yes` and downgrade
  chain confidence below `direct`.
- Missing files become `LoaderWarning` entries; reports surface them
  in dedicated sections.
- Contradictory evidence forces `evidence_status=inconsistent` and
  `outcome=inconclusive`.
- Tests cover loader, normaliser, timeline, causality, classifier,
  reporter, Foxglove hints, index filters, comparison, and the three
  CLIs without requiring ROS / Gazebo.

### Risks

- Causality rules are deterministic but heuristic; they make
  assumptions about scenario semantics. Mitigated by the
  `confidence` and `inferred` labels.
- Source evidence schema drift; the loader's structured warnings
  surface drift instead of silently failing.

### Deferred Work

- Live Foxglove integration (Phase 7) — the canonical layout is
  ready, but actually streaming a live bag is reserved for a
  Jazzy / Gazebo host.
- Cross-incident clustering, anomaly detection, and trend analysis.

### Portfolio Signal

- Demonstrates incident-forensics discipline: explicit confidence,
  named missing links, labelled contradictions, deterministic
  ordering, evidence-origin preservation.
- Demonstrates Foxglove integration as metadata + workflow support
  rather than a runtime dependency.

---

## 3i. Phase 7: Live Foxglove Replay Integration and Operational Review Sessions

### Status

Implemented in this branch. Read-only with respect to runtime
evidence and rosbag2 artefacts; produces metadata only.

### Objectives

- Inspect rosbag2 / MCAP artefacts in the documented bag locations
  without opening them.
- Generate per-incident replay manifests (expected topics, available
  topics, missing topics, bag status, layout pointer, marker count).
- Align incident-timeline markers to replay time with explicit
  alignment status (`exact` / `partial` / `unaligned`).
- Produce a Foxglove session metadata document (internal
  `rover-replay-review/1` schema) plus per-incident replay review
  reports.
- Provide a self-hosted GitHub workflow that runs the full live
  pipeline on a Jazzy + Gazebo runner and uploads the artefacts.

### Deliverables

- `backend/app/replay_review/` — package with `models`, `bag_index`,
  `marker`, `manifest`, `foxglove_session`, `validator`, `reporter`,
  `bundle`.
- `rover_ws/tools/build_replay_review_bundle.py` — CLI for replay
  bundle generation.
- `rover_ws/tools/validate_replay_review.py` — CLI for static
  validation.
- `rover_ws/tools/list_replay_reviews.py` — CLI for the replay
  review index.
- `.github/workflows/ros-jazzy-replay-review.yml` — self-hosted
  workflow (workflow_dispatch only).
- `docs/REPLAY_REVIEW_RUNBOOK.md` — operator runbook.
- `docs/REPLAY_REVIEW_INDEX.md` — generated index of replay-ready
  incidents.
- Three canonical replay review bundles under
  `incidents/canonical-{stale-lidar,estop-latched,static-qualification}/`.
- REQ-REPLAY-006..010 with traceability rows.

### Acceptance Criteria

- The replay review layer never opens a bag file; tests do not
  require Foxglove or ROS.
- Missing bags are reported as `missing_bag` (or `static_only` for
  static-only incidents); never silently treated as `passed`.
- Markers without `sim_time_ns` carry `alignment=partial`; markers
  are never invented when the timeline lacks the corresponding
  index.
- The Foxglove session JSON declares a `schema_version`
  (`rover-replay-review/1`) so reviewers know it is internal, not an
  official Foxglove import.
- The self-hosted workflow is `workflow_dispatch` only and uses a
  `self-hosted, ros-jazzy` runner.

### Risks

- Bag files may move between runs; mitigated by the manifest's
  per-candidate inspection log.
- Foxglove layout drift across versions; mitigated by checking the
  layout into the repo and reading it as plain JSON in tests.

### Deferred Work

- Live bag replay automation (script-driven Foxglove playback) —
  requires a runner with a graphical Foxglove or `foxglove-studio` CLI.
- Cross-incident comparison of replay coverage — currently the
  Phase-6 `compare_incidents` tool surfaces causality / classifier
  deltas; a replay-only comparator could come in a future phase.

### Portfolio Signal

- Demonstrates honest replay-review discipline: missing bags reported
  honestly, marker alignment downgraded when sim_time_ns is absent,
  the Foxglove session JSON labelled internal.
- Demonstrates a self-hosted-only live workflow that does not run on
  github-hosted runners.

---

## 3j. Phase 8: Replay Coverage Analytics and Cross-Incident Operational Intelligence

### Status

Implemented in this branch. Read-only with respect to incident
bundles + replay-review bundles + rosbag2 artefacts. Produces
deterministic analytics; no fabricated coverage.

### Objectives

- Derive deterministic coverage metrics from Phase-6 / Phase-7
  artefacts (six metrics per incident).
- Score replay quality on a 0..100 scale with explicit band caps
  (static-only ≤ 39, missing-bag ≤ 59, contradictions ≤ 39).
- Detect gaps + emit deterministic recommendations citing the
  underlying artefacts.
- Audit operator review completion via explicit acknowledgement
  only (never inferred).
- Aggregate trends + cross-incident comparisons + a filterable
  index across the incidents directory.

### Deliverables

- `backend/app/replay_analytics/` — package with `models`,
  `loader`, `coverage`, `scoring`, `review_audit`,
  `recommendations`, `trends`, `comparison`, `reporting`, `index`.
- `rover_ws/tools/analyze_replay_coverage.py`,
  `compare_replay_reviews.py`,
  `generate_replay_analytics.py`,
  `audit_replay_reviews.py`.
- `.github/workflows/replay-analytics-review.yml` (github-hosted
  by default, self-hosted optional).
- `docs/REPLAY_ANALYTICS.md`, `docs/REPLAY_QUALITY_SCORING.md`,
  `docs/REPLAY_REVIEW_AUDIT.md`, `docs/REPLAY_GAP_ANALYSIS.md`,
  `docs/REPLAY_ANALYTICS_INDEX.md`.
- Canonical analytics under `incidents/analytics/`.
- REQ-ANALYTICS-001..005 with traceability rows.

### Acceptance Criteria

- Static-only and missing-bag incidents stay below their respective
  caps (39 / 59).
- Operator review completion requires an explicit
  `review-audit.json` acknowledgement.
- Same inputs always yield byte-identical metrics + scores.
- The aggregate report distinguishes static-only / missing-bag /
  partial / bag-backed buckets.
- Tests cover coverage, scoring, trends, comparison, audit,
  recommendations, index, and the four CLIs without ROS / Gazebo /
  Foxglove.

### Risks

- Drift between scoring and the runbook bands. Mitigated by the
  test suite's explicit-band-cap tests.
- Recommendations becoming stale. Mitigated by deterministic
  gap-to-recommendation mapping.

### Deferred Work

- Fleet-style per-day / per-week aggregations (this phase indexes
  by incident only).
- Operator-comment ingestion (the audit module accepts free text
  but does no NLP).

### Portfolio Signal

- Demonstrates honest analytics discipline: missing bags reported,
  contradictions cap the score, review completion requires explicit
  acknowledgement, every report is deterministic.
- Demonstrates evidence-grounded recommendations that cite the
  artefacts they refer to.

---

## 3k. Phase 9: Source-to-Replay Regression Correlation and Reliability Impact Analysis

### Status

Implemented in this branch. Read-only with respect to source code,
evidence artefacts, and replay analytics. Produces deterministic
impact bundles; CI gate honours the missing-live-evidence exception.

### Objectives

- Inspect git diffs / changed file lists and classify each path
  by subsystem (deterministic prefix table).
- Map subsystems to existing REQ-* ids (via the live registry) and
  recommend the tools / artefacts to regenerate.
- Compare current replay analytics against a pinned baseline under
  `reliability-baselines/`; classify deltas as
  improvement / neutral / warning / regression / critical_regression.
- Assess conservative risk and emit a deterministic CI gate
  decision that fails only on the documented critical conditions.
- Provide a github-hosted CI workflow that runs on every PR and
  uploads the resulting bundle.

### Deliverables

- `backend/app/reliability_impact/` — 10-module package
  (`models`, `git_changes`, `subsystem_classifier`,
  `requirement_mapper`, `evidence_mapper`, `analytics_delta`,
  `baseline`, `risk_assessor`, `ci_gate`, `report`).
- `rover_ws/tools/analyze_source_impact.py`,
  `rover_ws/tools/reliability_impact_gate.py`.
- `.github/workflows/reliability-impact.yml` (github-hosted, runs
  on PR and dispatch).
- `docs/RELIABILITY_IMPACT_ANALYSIS.md`,
  `docs/SOURCE_TO_EVIDENCE_TRACEABILITY.md`,
  `docs/CI_RELIABILITY_GATE.md`.
- `reliability-baselines/` directory + README + pinned baseline
  files.
- `reliability-impact/canonical/` — canonical fixture-driven
  impact bundle.
- REQ-IMPACT-001..005 with traceability rows.

### Acceptance Criteria

- Changed files are classified into one of the documented buckets;
  unknown paths are surfaced, never silently dropped.
- Subsystem -> requirement mapping uses the live registry; new
  REQ-* ids appear automatically.
- Replay analytics deltas are compared against the pinned baseline;
  missing baseline is a warning, not a failure.
- The CI gate fails only on the documented critical conditions and
  never on missing live runtime evidence in github-hosted CI.
- Baselines never refresh automatically; `--write-baseline` is the
  only path that mutates them.
- Tests cover classifier, mapper, delta engine, risk assessor,
  gate, and the two CLIs without ROS, Gazebo, Foxglove, or network.

### Risks

- Subsystem prefix table drift. Mitigated by the classifier tests
  and by surfacing `unknown` files.
- Baseline staleness. Mitigated by the intentional-update workflow
  and the warning surface.

### Deferred Work

- AI-style summary generation (intentionally out of scope).
- Per-PR git-blame attribution (out of scope; not evidence-backed
  enough to be deterministic).

### Portfolio Signal

- Demonstrates source-to-evidence traceability discipline: every
  changed file lands in a documented bucket, every bucket points to
  a regen recipe, every regression is classified deterministically.
- Demonstrates honest CI gating: missing live runtime evidence
  never fails the gate; baselines are pinned; warnings never
  promote themselves into failures.

---

## 3l. Phase 10: Reliability Programme Review and Longitudinal Governance

### Status

Implemented in this branch. Read-only longitudinal layer over
Phase 3..9 artefacts. Deterministic, evidence-backed, conservative.

### Objectives

- Aggregate reliability-impact, replay analytics, runtime
  qualification, replay review, and incident artefacts across runs.
- Compute deterministic trends, drift, governance health,
  subsystem-risk aggregates, coverage evolution, gate history, and
  evidence freshness.
- Provide a github-hosted CI workflow that builds the programme
  review on every push and dispatch.

### Deliverables

- `backend/app/programme_review/` — 12 modules.
- `rover_ws/tools/generate_programme_review.py`,
  `analyze_reliability_trends.py`,
  `detect_reliability_drift.py`,
  `review_governance_health.py`,
  `review_evidence_freshness.py`.
- `.github/workflows/programme-review.yml`.
- `programme-review/` — canonical bundle (18 files).
- `docs/PROGRAMME_REVIEW.md`,
  `docs/GOVERNANCE_HEALTH_MODEL.md`,
  `docs/RELIABILITY_TREND_ANALYSIS.md`,
  `docs/EVIDENCE_FRESHNESS_POLICY.md`,
  `docs/SUBSYSTEM_RISK_AGGREGATION.md`.
- REQ-PROGRAMME-001..010 with traceability rows.

### Acceptance Criteria

- Missing history is reported as `insufficient_history` /
  `unknown`, never as regression.
- Mixed-origin samples are labelled explicitly; static-only stays
  static-only.
- Operator review completion is never inferred.
- Trends are deterministic projections, not forecasts.
- Subsystem-risk rows record observations + counts, never causal
  claims.
- Freshness is driven by an explicit reference time supplied by
  the caller (CI passes UTC `now`; tests supply fixtures).
- CI workflow never fails for missing live runtime evidence.

### Risks

- Drift between the loader's expectations and upstream artefact
  shapes. Mitigated by the loader's structured warnings.
- Trend windows misleading when histories are short. Mitigated by
  the `insufficient_history` label.

### Deferred Work

- Per-day / per-week roll-ups inside trend windows (out of scope).
- Probabilistic forecasting (intentionally excluded).

### Portfolio Signal

- Demonstrates longitudinal governance discipline: deterministic
  trend classification, conservative drift rules, honest treatment
  of missing history, and a governance-grade six-discipline rollup.

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
