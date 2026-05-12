# Project Boundary

**A deterministic autonomy validation and safety orchestration platform for unmanned ground vehicles.**

**Live demo:** https://projectboundary.vercel.app/

Project Boundary is a simulation-first robotics platform that demonstrates how to design an autonomous rover whose safety behaviour is *architecturally enforceable, deterministic, and replayable* — and how to generate the engineering evidence to prove it.

> This project is **not safety-certified**. It demonstrates safety-oriented architecture, deterministic validation, and evidence generation patterns drawn from aerospace and defence-adjacent unmanned systems work. It is built as a portfolio and engineering-learning artefact.

---

## Reviewer paths

Pick the path that matches your role and how much time you have.
The full per-audience playbook is [`docs/REVIEWER_PLAYBOOK.md`](docs/REVIEWER_PLAYBOOK.md).

| You have | Read in order |
| --- | --- |
| **5 minutes** | [`docs/EXECUTIVE_SUMMARY.md`](docs/EXECUTIVE_SUMMARY.md) → [Status table](#status) → [`docs/SCENARIO_VERIFICATION_REPORT.md`](docs/SCENARIO_VERIFICATION_REPORT.md) (summary) |
| **15 minutes** | Add [`docs/WHY_THIS_PROJECT_EXISTS.md`](docs/WHY_THIS_PROJECT_EXISTS.md) + [`ARCHITECTURE.md`](ARCHITECTURE.md) (sections 1–3) + [`docs/diagrams/system-flow.md`](docs/diagrams/system-flow.md) |
| **45 minutes** | Add [`docs/ARCHITECTURE_WALKTHROUGH.md`](docs/ARCHITECTURE_WALKTHROUGH.md) + [`docs/SAFETY_MODEL.md`](docs/SAFETY_MODEL.md) + [`docs/EVENT_MODEL.md`](docs/EVENT_MODEL.md) + one `evidence/scenarios/<id>/evidence.md` + a CSV from `reviewer-export/csv/` |

By audience:

| Audience | Best entry |
| --- | --- |
| Recruiter / non-technical | [`docs/EXECUTIVE_SUMMARY.md`](docs/EXECUTIVE_SUMMARY.md) → [`docs/PORTFOLIO_CASE_STUDY.md`](docs/PORTFOLIO_CASE_STUDY.md) |
| Senior software engineer | [`docs/ARCHITECTURE_WALKTHROUGH.md`](docs/ARCHITECTURE_WALKTHROUGH.md) → [`docs/TECHNICAL_REVIEW_CHECKLIST.md`](docs/TECHNICAL_REVIEW_CHECKLIST.md) |
| Robotics / ROS 2 reviewer | [`docs/LIVE_RUNTIME_STATUS.md`](docs/LIVE_RUNTIME_STATUS.md) → [`rover_ws/README.md`](rover_ws/README.md) → [`docs/RUNTIME_QUALIFICATION_RUNBOOK.md`](docs/RUNTIME_QUALIFICATION_RUNBOOK.md) |
| Verification / reliability reviewer | [`docs/VERIFICATION_STRATEGY.md`](docs/VERIFICATION_STRATEGY.md) → [`docs/TRACEABILITY_MATRIX.md`](docs/TRACEABILITY_MATRIX.md) → [`docs/PROGRAMME_REVIEW.md`](docs/PROGRAMME_REVIEW.md) → [`docs/REVIEWER_EXPORTS.md`](docs/REVIEWER_EXPORTS.md) |

---

## Why this project exists

Most portfolio robotics projects optimize for "the robot moved." Project Boundary optimizes for a harder question:

> *When the robot moves, how do you prove the autonomy stack could not have moved it unsafely — and how do you reconstruct exactly what happened if something goes wrong?*

That question is the daily reality of industrial, aerospace, defence, and warehouse robotics teams. The architectural patterns required to answer it — bounded autonomy, deterministic execution, separated authority, replayable state, traceable requirements — are the focus of this repository.

See [`docs/WHY_THIS_PROJECT_EXISTS.md`](docs/WHY_THIS_PROJECT_EXISTS.md) for the full motivation and the engineering disciplines this project takes seriously.

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

For the rendered version see [`docs/diagrams/safety-authority.md`](docs/diagrams/safety-authority.md).

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
| `backend/app/runtime_validation/` | Live runtime validation pipeline; static-only fall-back when no Jazzy host |
| `backend/app/incident_analysis/` | Incident reconstruction + index |
| `backend/app/replay_review/`, `replay_analytics/` | Replay review + cross-incident analytics |
| `backend/app/reliability_impact/` | Source-change → replay-quality correlation (correlation only, never causation) |
| `backend/app/programme_review/` | Longitudinal governance (trends, drift, freshness, subsystem risk, gate history) |
| `backend/app/reviewer_exports/` | Reviewer-friendly CSV / JSONL / JSON-Schema bundle |
| `backend/app/simulation/` | Deterministic scenario engine (no external dependencies) |
| `rover_ws/` | Parallel ROS 2 Jazzy / Gazebo Harmonic implementation honouring the same contracts |
| `tools/`, `rover_ws/tools/` | Audits, validators, evidence generators, scenario runners, programme-review and reviewer-export CLIs |
| `docs/` | Architecture, contracts, strategies, traceability, reports, the reviewer playbook, and `docs/diagrams/` |
| `evidence/`, `incidents/`, `programme-review/`, `reliability-impact/`, `reviewer-export/` | Generated evidence artefacts |

Two parallel implementations — a **dependency-free Python core** and a **ROS 2 / Gazebo workspace** — share the same event, motion-authority, fault-injection, and replay contracts. The Python side runs anywhere; the ROS 2 side passes static validation everywhere and is designed for end-to-end execution on a Jazzy host.

---

## Verification evidence

The repository ships with a working verification + governance pipeline, not just documentation about one.

- **Stable requirement IDs** across safety, fault, replay, mission, world, diagnostics, operator, runtime, incident, qualification, replay-review, analytics, impact, programme, and export categories. Each has architecture references, implementation pointers, scenarios, tests, and (where applicable) evidence artefacts.
- **14 verified scenarios** including stale-lidar restricted mode, odometry divergence, command timeout, bridge disconnect, wheel slip, e-stop latched manual reset, keepout-zone violation, safe-stop during active mission, and mission abort after fault escalation.
- **Per-scenario evidence artefacts** under `evidence/scenarios/` — `evidence.json`, `events-summary.md`, `replay-integrity.json`, `command-audit.json`, `safety-transition-audit.json`.
- **Longitudinal governance** under `programme-review/` — trends, drift, freshness, subsystem risk, coverage evolution, gate history.
- **Reviewer export** under `reviewer-export/` — 8 CSV tables, 8 JSONL mirrors, 8 JSON Schemas (draft 2020-12) with `causality_claimed` pinned `const: false`, a `manifest.json`, a notebook scaffold, and a Markdown summary.
- **5 ADRs** under `docs/adr/` covering ROS 2 / Gazebo selection, simulation-first strategy, the safety supervisor authority model, and the companion-computer / MCU split.
- **Honest report status codes**: `passed`, `failed`, `partial`, `skipped`, `not_executed` — no green-washing.

The current `docs/SCENARIO_VERIFICATION_REPORT.md` shows 14/14 scenarios passing in the deterministic engine. Live ROS 2 / Gazebo runtime verification is reported separately and falls back to `static-only` when a Jazzy host isn't available; the report says so explicitly rather than skipping the gap.

---

## Engineering principles this project takes seriously

These are explicit constraints in the repository, not aspirations:

1. **Safety authority is non-negotiable.** No mission, navigation, or perception path can authorise motion. Ever.
2. **Determinism over novelty.** Critical paths produce explainable, bounded, replayable outputs. Probabilistic behaviour stays out of safety-critical code.
3. **Faults alter inputs, not state.** Fault injection mutates sensor readings and watchdog pets — the supervisor reacts through normal mechanisms. Faults never reach into the safety state machine.
4. **Replay reconstructs causality.** Every scenario emits ordered, schema-validated events sufficient to reconstruct safety and mission transitions.
5. **Traceability is mechanical, not aspirational.** Requirements link to architecture sections, modules, scenarios, tests, and evidence artefacts via a generated matrix.
6. **No fake green.** Reports distinguish passed, failed, partial, skipped, and not_executed. If something can't run in the current environment, it says so.
7. **No causal claims** in any aggregation layer. Programme review, replay analytics, reliability impact, and reviewer export use correlation language; the reviewer-export schema pins `causality_claimed: false`.
8. **No safety-certification claims.** Anywhere. The disclaimer is in the docs, the reports, and this README.

---

## Quick start

The Python backend has zero runtime dependencies and runs the full verification suite locally.

```bash
# From the repo root
cd backend
pip install -e ".[dev]"
pytest                                          # run the test suite

# Generate evidence and reports
cd ..
python tools/run_scenario_suite.py              # execute the scenario verifier
python tools/generate_evidence.py               # write per-scenario evidence/
python tools/generate_traceability.py --with-verification  # regenerate docs/TRACEABILITY_MATRIX.md
python tools/generate_verification_report.py    # regenerate docs/SCENARIO_VERIFICATION_REPORT.md

# Programme review + reviewer export (Phases 10–11)
python rover_ws/tools/generate_programme_review.py --reference-time 2026-05-12T00:00:00Z
python rover_ws/tools/generate_reviewer_export.py --export-id reviewer-export-canonical \
                                                  --generated-at 2026-05-12T00:00:00Z
python rover_ws/tools/validate_reviewer_export.py --bundle reviewer-export/
```

The ROS 2 workspace under `rover_ws/` requires a ROS 2 Jazzy + Gazebo Harmonic host; static-validation tests run without it. See [`rover_ws/README.md`](rover_ws/README.md) and [`rover_ws/tests/manual.md`](rover_ws/tests/manual.md).

For a hands-on walkthrough see [`docs/SCENARIO_DEMO_GUIDE.md`](docs/SCENARIO_DEMO_GUIDE.md).

---

## Where to read next

If you have **two minutes** — read this README and skim [`docs/SCENARIO_VERIFICATION_REPORT.md`](docs/SCENARIO_VERIFICATION_REPORT.md).

If you have **ten minutes**:
1. [`docs/EXECUTIVE_SUMMARY.md`](docs/EXECUTIVE_SUMMARY.md) — one-page overview
2. [`ARCHITECTURE.md`](ARCHITECTURE.md) — system overview, principles, authority model
3. [`docs/SAFETY_MODEL.md`](docs/SAFETY_MODEL.md) — state machine, transition rules, reason codes

If you have **an hour**:
- [`docs/REVIEWER_PLAYBOOK.md`](docs/REVIEWER_PLAYBOOK.md) for the per-audience routing
- [`docs/ARCHITECTURE_WALKTHROUGH.md`](docs/ARCHITECTURE_WALKTHROUGH.md) for the module tour
- [`docs/EVENT_MODEL.md`](docs/EVENT_MODEL.md), [`docs/FAULT_INJECTION.md`](docs/FAULT_INJECTION.md), [`docs/REPLAY_SYSTEM.md`](docs/REPLAY_SYSTEM.md) for the contracts
- [`docs/VERIFICATION_STRATEGY.md`](docs/VERIFICATION_STRATEGY.md), [`docs/TESTING_STRATEGY.md`](docs/TESTING_STRATEGY.md), [`docs/PROGRAMME_REVIEW.md`](docs/PROGRAMME_REVIEW.md) for how the evidence is generated and rolled up
- [`docs/adr/`](docs/adr/) for the major architectural decisions

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
| 5 — ROS host qualification & continuous runtime validation | Implemented |
| 6 — Incident reconstruction & telemetry correlation | Implemented |
| 7 — Live Foxglove replay integration | Implemented |
| 8 — Replay coverage analytics | Implemented |
| 9 — Source-to-replay regression correlation | Implemented |
| 10 — Reliability programme review & longitudinal governance | Implemented |
| 11 — Reviewer export package & notebook scaffolding | Implemented |
| 12 — Reviewer operations playbook & portfolio presentation | Implemented |
| 13 — Live runtime maturity (Jazzy CI, real bags, real source-change series) | Pending — see [`docs/ROADMAP.md`](docs/ROADMAP.md) |

For the full breakdown see [`docs/ROADMAP.md`](docs/ROADMAP.md).

---

## A note on intent

I built Project Boundary to develop and demonstrate the engineering disciplines I think matter most for trustworthy autonomous systems: separated authority, bounded behaviour, deterministic execution, and honest verification. The patterns here are deliberately drawn from industries where "the robot moved" is the easy part and "prove it couldn't have moved unsafely" is the job.

The code, docs, and evidence artefacts are meant to be read together. Each is incomplete without the others.

— Michael
