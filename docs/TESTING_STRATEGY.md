# Testing Strategy

## 1. Purpose

This document defines the testing strategy for the Autonomous Safety Validation Rover Platform.

The strategy is engineered to enforce three things:

1. The safety authority hierarchy defined in `docs/SAFETY_MODEL.md` is preserved.
2. The replay contract defined in `docs/REPLAY_SYSTEM.md` is upheld.
3. The fault injection contract defined in `docs/FAULT_INJECTION.md` is honored.

A feature is not complete until it satisfies the acceptance gates in section 11. "Working code" is not sufficient.

This document does not claim certification under any functional safety regime. It defines an engineering test program calibrated for a portfolio platform with serious architectural discipline.

---

## 2. Testing Philosophy

### 2.1 Tests assert architecture, not just behavior

Behavior tests verify that the rover does what was asked. Architecture tests verify that the rover cannot do what is forbidden. The latter is at least as important.

Examples of architecture tests:

- the hardware gateway has no subscription to `/cmd_vel_requested`
- only the safety supervisor publishes `/cmd_vel_authorized`
- the fault injection subsystem cannot transition `/safety/state` directly

### 2.2 Tests are reproducible

Every test runs against pinned inputs. Where simulation is involved, the simulator world, the rover description, the launch parameters, and the seed are pinned. Non-reproducible tests are bugs.

### 2.3 Tests live close to the code they exercise

Unit tests live with the package. Integration and simulation tests live in `rover_tests` (or equivalent) with clearly named scenarios. The separation is not theoretical: a unit test must not depend on a live simulator.

### 2.4 Tests produce evidence

Simulation tests, fault tests, and replay tests produce run directories conforming to `docs/REPLAY_SYSTEM.md`. The evidence is part of the test artifact, not a side effect.

### 2.5 Tests fail loudly

Determinism violations, schema violations, and topic-contract violations cause the test to fail with an explicit reason code. They are never warnings.

---

## 3. Test Layers

The test program has the following layers, ordered by scope:

| Layer | Scope |
|---|---|
| `unit` | Pure functions, single classes, single nodes in isolation. |
| `integration` | Multiple nodes within a single process or launch group, no simulator. |
| `simulation` | Full ROS 2 graph with Gazebo Harmonic and a pinned world. |
| `fault_injection` | Simulation runs with the fault injection subsystem armed against a specific fault class. |
| `replay` | Validation of recorded runs against the event schema and required-event coverage. |
| `contract` | Architectural invariants: who publishes what, who subscribes to what, who owns what topic. |
| `hardware_bench` | Bench hardware tests with operator presence, restricted to the hardware-allowed fault subset. |

A test belongs to exactly one layer. Cross-layer dependencies are flags that the test design is wrong.

---

## 4. Deterministic Simulation Tests

Simulation tests must:

- pin the simulator version, world file, rover description, and launch parameters
- use simulated time (`/clock`) for all timing assertions
- record a bag and event stream conforming to `docs/REPLAY_SYSTEM.md`
- produce a run directory under `runs/test/<test_name>/<run_id>/`
- assert on events and topic states, not on screenshots or wall-clock timing

Simulation test acceptance criteria:

- the test re-runs produce the same `safety_transition.entered` sequence
- the test re-runs produce the same `motion_arbitration.*` sequence
- non-determinism in physics that does not change the event timeline is acceptable; non-determinism that changes safety transitions is a failure

---

## 5. Safety-State Transition Tests

For every transition in `docs/SAFETY_MODEL.md` section 5.3, a corresponding test must exist that:

- forces the input conditions for the transition
- asserts that the transition occurs
- asserts that the appropriate `safety_transition.entered` event is emitted
- asserts that `/cmd_vel_authorized` is consistent with the new state's authority (e.g., zero in `SAFE_STOP`)
- asserts that the supervisor does not transition to a less restrictive state without passing through `RECOVERY`

Negative tests must exist for the prohibited transitions:

- mission layer attempts to publish to `/cmd_vel_authorized` are detected and the test fails the offending build
- fault injection that attempts to set `/safety/state` is detected and the test fails the offending build
- `E_STOP_LATCHED` cannot be cleared by anything other than an explicit operator reset

---

## 6. Fault Injection Tests

For every supported fault class in `docs/FAULT_INJECTION.md` section 4, a test must exist that:

- arms the fault from a scenario file
- fires the fault during a controlled run
- asserts the expected detection event(s) are emitted in the expected order
- asserts the expected safety response occurs
- asserts the system returns to `ACTIVE_*` only via `RECOVERY`
- asserts the `fault_injection.armed`, `fault_injection.fired`, and `fault_injection.cleared` events are present

A separate negative test asserts that a misconfigured fault attempting to mutate `/safety/state` does not succeed and is rejected by the architecture.

---

## 7. Replay Validation Tests

Replay tests operate on recorded runs only. They must:

- accept a run directory as input
- validate `metadata.json` against the schema
- validate every line of `events.jsonl` against `docs/EVENT_MODEL.md` section 3
- assert presence of the required topics from `docs/REPLAY_SYSTEM.md` section 7
- assert presence of the required event classes from `docs/REPLAY_SYSTEM.md` section 8
- regenerate the `incident-summary.md` from the event stream and assert determinism

A representative subset of recorded runs is checked into the repository (or referenced by hash) and validated in CI.

---

## 8. Event Schema Tests

Event schema tests are unit-level. They must:

- accept a single event JSON object
- validate required fields, types, and controlled vocabularies
- reject unknown `event_type` categories
- reject unknown `severity` values
- reject events missing `run_id`, `scenario_id`, or `safety_state`
- pass for every valid event in a recorded run

Schema tests are run on every CI build. They are also run by the replay validator as a precondition for higher-level checks.

---

## 9. Watchdog and Timeout Tests

Watchdog tests must:

- register a watchdog with a known deadline
- skip petting it
- assert that it expires at the configured deadline within a tolerance
- assert that the configured `watchdog.expired` event is emitted with the expected `reason_code`
- assert that the configured safety transition is taken

Timeout tests must:

- stop publishing on `/cmd_vel_authorized` (gateway-side)
- assert that the gateway decays to zero motion within the gateway's command timeout
- separately, stop heartbeating from the gateway to the supervisor
- assert that the supervisor's gateway watchdog expires and `SAFE_STOP` is entered

Watchdog and timeout tests must use simulated time when running in simulation, and may use wall time when running on bench hardware. The choice must be recorded in the test metadata.

---

## 10. Sim-vs-Hardware Parity Tests

Parity tests are introduced in Phase 5 (see `docs/ROADMAP.md`). They must:

- run the same scenario in simulation and on bench hardware
- record both runs
- compare event timelines for the same `safety_transition.entered` sequence
- tolerate physics differences that do not change safety state
- flag any divergence in safety state as a failure

A scenario qualifies as "parity-validated" only when both runs pass. Parity-validation status is tracked in `docs/REPLAY_SYSTEM.md` and per-scenario metadata.

---

## 11. Acceptance Gates per Feature

A feature is not complete until all of the following hold:

1. **Events.** It emits structured events conforming to `docs/EVENT_MODEL.md` for every operationally significant fact it produces.
2. **Replay.** It participates in replay: its required topics are recorded, its required events are present, and it can be inspected from the run directory alone.
3. **Safety-state coverage.** Where it interacts with safety, it has tests covering the relevant state transitions and the relevant negative cases.
4. **No bypass.** It does not bypass the safety supervisor, the motion arbitration stage, or the hardware gateway's authorized-command-only contract.
5. **Determinism.** A pinned scenario re-run produces the same event timeline within the limits in `docs/REPLAY_SYSTEM.md` section 6.
6. **Documentation.** Any new reason codes, event types, fault classes, or topics are documented in the relevant `docs/` file.

A pull request that fails any of these gates is rejected. The acceptance gates are not negotiable per-feature; they are properties of the platform.

---

## 12. CI Expectations

Continuous integration must run, at minimum:

| Job | Layer | Always |
|---|---|---|
| Unit tests | `unit` | Yes |
| Lint and static analysis | `unit` | Yes |
| Contract tests | `contract` | Yes |
| Event schema tests on representative events | `unit` | Yes |
| Replay validators on a representative recorded run | `replay` | Yes |
| A short simulation smoke test | `simulation` | When the simulator can be provisioned |
| At least one fault injection scenario | `fault_injection` | When the simulator can be provisioned |

CI must not pass when:

- a contract test detects a forbidden subscription or publication
- the event schema validator rejects any event in a representative run
- a replay validator fails on a representative run
- a deterministic simulation test produces a different `safety_transition.entered` sequence than the pinned reference

---

## 13. Example Tests (Illustrative)

These examples describe tests that should exist in later phases. They are not implemented in this pass; they document expectations.

### 13.1 `test_supervisor_refuses_active_normal_with_stale_lidar`

- Layer: `simulation`
- Setup: launch the full graph, pre-arm `stale_lidar` fault to fire before activation.
- Action: operator activation request.
- Expected: supervisor refuses transition to `ACTIVE_NORMAL`, emits `safety_transition.refused` with `reason_code: stale_lidar`, remains in `INACTIVE`.

### 13.2 `test_safe_stop_zero_authorized_motion`

- Layer: `simulation`
- Setup: drive the rover into `SAFE_STOP` via a fault.
- Action: continue to publish non-zero `/cmd_vel_requested`.
- Expected: every sample on `/cmd_vel_authorized` during `SAFE_STOP` is exactly zero linear and zero angular.

### 13.3 `test_e_stop_latched_persistence`

- Layer: `simulation`
- Setup: assert `E_STOP_LATCHED` via operator pathway.
- Action: clear all underlying conditions; wait.
- Expected: supervisor remains in `E_STOP_LATCHED` until an explicit operator reset event is observed.

### 13.4 `test_fault_injection_cannot_set_safety_state`

- Layer: `contract`
- Setup: load a deliberately misconfigured fault attempting to publish to `/safety/state`.
- Expected: the misconfigured fault is rejected at load time; if loaded, the supervisor ignores or rejects the publication; the test fails the build if the supervisor's state changes as a result.

### 13.5 `test_gateway_only_subscribes_to_authorized`

- Layer: `contract`
- Setup: introspect the gateway node's subscriptions.
- Expected: the gateway has exactly one motion-input subscription, and it is `/cmd_vel_authorized`.

### 13.6 `test_recovery_revalidates_inputs`

- Layer: `simulation`
- Setup: drive to `SAFE_STOP` via stale LiDAR; clear the fault.
- Action: operator-issued recovery request.
- Expected: supervisor enters `RECOVERY`, revalidates LiDAR freshness and other gates, emits `safety_transition.entered RECOVERY` and then `safety_transition.entered ACTIVE_*` only when validation passes; transitions back to `SAFE_STOP` if validation fails.

### 13.7 `test_event_schema_well_formed`

- Layer: `unit`
- Setup: load every event from a pinned `events.jsonl`.
- Expected: each event passes the schema validator from `docs/EVENT_MODEL.md`.

### 13.8 `test_replay_required_events_present`

- Layer: `replay`
- Setup: a recorded run from a fault-injection scenario.
- Expected: the run contains all event classes required by `docs/REPLAY_SYSTEM.md` section 8.

### 13.9 `test_watchdog_expiration_emits_event`

- Layer: `integration`
- Setup: register a test watchdog and skip petting it.
- Expected: a `watchdog.expired` event is emitted at the configured deadline within tolerance.

### 13.10 `test_command_timeout_decays_to_zero`

- Layer: `integration`
- Setup: silence `/cmd_vel_authorized`.
- Expected: the gateway publishes zero linear and zero angular velocity to the actuator interface within the configured command timeout, and emits a `motion_arbitration.zeroed` event with the expected `reason_code`.

---

## 14. Test Inventory and Coverage

The platform tracks test coverage at the architectural level:

- every state transition in `docs/SAFETY_MODEL.md` has at least one positive test
- every prohibited transition in `docs/SAFETY_MODEL.md` has at least one negative test
- every fault class in `docs/FAULT_INJECTION.md` has at least one scenario
- every required topic in `docs/REPLAY_SYSTEM.md` is asserted present in at least one recorded run
- every required event class in `docs/REPLAY_SYSTEM.md` is asserted present in at least one recorded run

Coverage at the line level is a useful but secondary metric. Architectural coverage is primary.
