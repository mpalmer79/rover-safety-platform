# Project Boundary

**A deterministic autonomy validation and safety orchestration platform for unmanned ground vehicles.**

Project Boundary is a simulation-first robotics platform that demonstrates how to design an autonomous rover whose safety behavior is *architecturally enforceable, deterministic, and replayable* — and how to generate the engineering evidence to prove it.

> This project is **not safety-certified**. It demonstrates safety-oriented architecture, deterministic validation, and evidence generation patterns drawn from aerospace and defense-adjacent unmanned systems work. It is built as a portfolio and engineering-learning artifact.

---

## Why this project exists

Most portfolio robotics projects optimize for "the robot moved." Project Boundary optimizes for a harder question:

> *When the robot moves, how do you prove the autonomy stack could not have moved it unsafely — and how do you reconstruct exactly what happened if something goes wrong?*

That question is the daily reality of industrial, aerospace, defense, and warehouse robotics teams. The architectural patterns required to answer it — bounded autonomy, deterministic execution, separated authority, replayable state, traceable requirements — are the focus of this repository.

---

## The architectural thesis

The rover is **architecturally incapable** of bypassing the safety supervisor. Every actuator command flows through a single, auditable pipeline:

```text
Mission Runtime  ─requests──▶  Safety Supervisor  ─authorizes──▶  Motion Arbitration  ─actuates──▶  Hardware Gateway
                                       ▲
                  Freshness gates ─────┤
                  Watchdogs       ─────┤
                  Confidence      ─────┤
                  Operator inputs ─────┘
```

- Mission systems may **request** motion.
- Only the safety supervisor may **authorize** motion.
- This boundary is enforced in code, exercised by scenarios, and audited by tooling.

Every safety state transition (`ACTIVE_NORMAL`, `ACTIVE_DEGRADED`, `RESTRICTED`, `SAFE_STOP`, `E_STOP_LATCHED`, `RECOVERY`) is explicit, allowed-list checked, reason-coded, and replayable from event logs.

---

## What's in the repository

| Area | What it contains |
|---|---|
| `backend/app/safety/` | Safety supervisor, motion arbitration, freshness gates, watchdogs, confidence scoring, transition rules |
| `backend/app/mission/` | Mission orchestrator, waypoint execution, recovery framework, mission constraints |
| `backend/app/world_model/` | Keepout / restricted zones, occupancy, world snapshots |
| `backend/app/faults/` | Fault injection (sensor, command, bridge, watchdog) — never mutates safety state directly |
| `backend/app/replay/` | Event recording, run manifests, replayable artifacts |
| `backend/app/verification/` | Requirements registry, scenario verifier, evidence generator, command-path audit, replay-integrity audit, safety-transition audit, traceability matrix |
| `backend/app/simulation/` | Deterministic scenario engine (no external dependencies) |
| `rover_ws/` | Parallel ROS 2 Jazzy / Gazebo Harmonic implementation honoring the same contracts |
| `tools/` | CLI auditors and report generators (`validate_*`, `audit_*`, `verify_*`, `generate_*`) |
| `docs/` | ODD, safety model, event model, fault-injection contract, replay contract, verification strategy, traceability matrix, ADRs |
| `evidence/` | Generated per-scenario evidence artifacts (JSON + Markdown) |

Two parallel implementations — a **dependency-free Python core** and a **ROS 2 / Gazebo workspace** — share the same event, motion-authority, fault-injection, and replay contracts. The Python side runs anywhere; the ROS 2 side passes static validation and is designed for end-to-end execution on a Jazzy host.

---

## Verification evidence

The repository ships with a working verification pipeline, not just documentation about one.

- **18 stable requirement IDs** (`REQ-SAFE-001` … `REQ-RUNTIME-005`) across safety, fault, replay, mission, world, diagnostics, operator, and runtime categories. Each has architecture references, implementation pointers, scenario bindings, and test bindings.
- **14 verified scenarios** including stale-lidar restricted mode, odometry divergence, command timeout, bridge disconnect, wheel slip, e-stop latched manual reset, keepout-zone violation, safe-stop during active mission, and mission abort after fault escalation.
- **~34 test modules** across the Python backend and ROS 2 workspace.
- **5 ADRs** covering ROS 2 / Gazebo selection, simulation-first strategy, the safety supervisor authority model, and the companion-computer / MCU split.
- **Per-scenario evidence artifacts** under `evidence/scenarios/` — `evidence.json`, `events-summary.md`, `replay-integrity.json`, `command-audit.json`, `safety-transition-audit.json`.
- **Honest report status codes**: `passed`, `failed`, `partial`, `skipped`, `not_executed` — no green-washing.

The current `docs/SCENARIO_VERIFICATION_REPORT.md` shows 14/14 scenarios passing in the deterministic engine. Live ROS 2 / Gazebo runtime verification is reported separately and falls back to static validation when a Jazzy host isn't available; the report says so explicitly rather than skipping the gap.

---

## Engineering principles this project takes seriously

These are explicit constraints in the repository, not aspirations:

1. **Safety authority is non-negotiable.** No mission, navigation, or perception path can authorize motion. Ever.
2. **Determinism over novelty.** Critical paths produce explainable, bounded, replayable outputs. Probabilistic behavior stays out of safety-critical code.
3. **Faults alter inputs, not state.** Fault injection mutates sensor readings and watchdog pets — the supervisor reacts through normal mechanisms. Faults never reach into the safety state machine.
4. **Replay reconstructs causality.** Every scenario emits ordered, schema-validated events sufficient to reconstruct safety and mission transitions.
5. **Traceability is mechanical, not aspirational.** Requirements link to architecture sections, modules, scenarios, tests, and evidence artifacts via a generated matrix.
6. **No fake green.** Reports distinguish passed, failed, partial, skipped, and not_executed. If something can't run in the current environment, it says so.
7. **No safety-certification claims.** Anywhere. The disclaimer is in the docs, the reports, and this README.

---

## Quick start

The Python backend has zero runtime dependencies and runs the full verification suite locally.

```bash
# From the repo root
cd backend
pip install -e ".[dev]"
pytest                                    # run the test suite

# Generate evidence and reports
cd ..
python tools/run_scenario_suite.py        # execute the scenario verifier
python tools/generate_evidence.py         # write per-scenario evidence/
python tools/generate_traceability.py     # regenerate docs/TRACEABILITY_MATRIX.md
python tools/generate_verification_report.py  # regenerate docs/SCENARIO_VERIFICATION_REPORT.md
```

The ROS 2 workspace under `rover_ws/` requires a ROS 2 Jazzy + Gazebo Harmonic host; static-validation tests run without it. See `rover_ws/README.md` and `rover_ws/tests/manual.md`.

---

## Where to read next

If you have **two minutes** — read this README and skim `docs/SCENARIO_VERIFICATION_REPORT.md`.

If you have **ten minutes**:
1. `ARCHITECTURE.md` — system overview, principles, authority model
2. `docs/SAFETY_MODEL.md` — state machine, transition rules, reason codes
3. `docs/TRACEABILITY_MATRIX.md` — requirements → tests → evidence

If you have **an hour**:
- `docs/EVENT_MODEL.md`, `docs/FAULT_INJECTION.md`, `docs/REPLAY_SYSTEM.md` for the contracts
- `docs/VERIFICATION_STRATEGY.md` and `docs/TESTING_STRATEGY.md` for how the evidence is generated
- `docs/adr/` for the major architectural decisions

---

## Status

| Phase | Status |
|---|---|
| 0 — Architecture authority layer | Implemented |
| 1A — Deterministic Python autonomy core | Implemented |
| 1B — ROS 2 / Gazebo bringup | Implemented (static validation passes; end-to-end requires Jazzy host) |
| 1C — Runtime validation & integration verification | Implemented |
| 2 — Mission runtime & deterministic navigation orchestration | Implemented |
| 3 — Verification, scenario certification, evidence generation | Implemented |
| 4 — Live ROS 2 / Gazebo runtime verification | Implemented (static-only fall-back where applicable) |
| 3-ROS, 5, 6 | Pending — see `docs/ROADMAP.md` |

---

## A note on intent

I built Project Boundary to develop and demonstrate the engineering disciplines I think matter most for trustworthy autonomous systems: separated authority, bounded behavior, deterministic execution, and honest verification. The patterns here are deliberately drawn from industries where "the robot moved" is the easy part and "prove it couldn't have moved unsafely" is the job.

The code, docs, and evidence artifacts are meant to be read together. Each is incomplete without the others.

— Michael
