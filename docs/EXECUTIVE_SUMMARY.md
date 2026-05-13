# Executive Summary

The platform is **not safety-certified**. This page is the
five-minute version of the project for any reader.

## What it is

**Project Boundary** is a deterministic autonomy validation and
safety-orchestration platform for a simulated unmanned ground vehicle
(UGV). It demonstrates how to architect, exercise, and *prove* a
rover whose autonomy stack is **architecturally incapable** of
authorising unsafe motion — and how to generate the engineering
evidence that supports that claim.

## What it proves

| Claim | How it is proven |
| --- | --- |
| Mission code cannot authorise motion | Single-authority safety supervisor; command-path audit (`tools/audit_command_path.py`) |
| Safety state transitions are explicit and bounded | Allowed-list state machine; safety-transition audit (`tools/audit_safety_transitions.py`) |
| Faults change inputs, not state | Fault-injection contract (`docs/FAULT_INJECTION.md`); state-machine integrity tests |
| Every scenario is replayable from events | Replay system (`docs/REPLAY_SYSTEM.md`); replay-integrity verifier (`tools/verify_replay_integrity.py`) |
| Requirements link to tests and evidence | Mechanical traceability matrix (`docs/TRACEABILITY_MATRIX.md`) |
| Reports never green-wash | Status vocab `passed` / `failed` / `partial` / `skipped` / `not_executed` is enforced across all generators |
| Aggregations never claim causality | Programme-review and reviewer-export layers pin `causality_claimed=false` at schema level |

## What is in the repo

| Layer | Location | Role |
| --- | --- | --- |
| Deterministic Python autonomy core | `backend/app/` | Safety supervisor, mission runtime, world model, fault injection, replay, verification, programme review, reviewer export |
| ROS 2 / Gazebo workspace | `rover_ws/` | Parallel implementation honouring the same contracts; static-only fall-back when no Jazzy host |
| Engineering tools | `tools/`, `rover_ws/tools/` | Audits, validators, evidence generators, scenario runners, programme-review CLIs, reviewer-export CLI |
| Evidence | `evidence/`, `incidents/`, `programme-review/`, `reliability-impact/`, `reviewer-export/` | Per-scenario artifacts, incident reconstructions, longitudinal governance, reviewer-friendly bundle |
| Docs | `docs/`, `ARCHITECTURE.md`, ADRs | Architecture, contracts, strategy, traceability, reports, playbook |

## Phase status (high level)

| Phase | Theme | Status |
| --- | --- | --- |
| 0 | Architecture authority layer | Implemented |
| 1A / 1B / 1C | Python core / ROS bringup / runtime hardening | Implemented (ROS-side end-to-end requires Jazzy host) |
| 2 | Mission runtime, deterministic navigation | Implemented |
| 3 | Verification, scenario certification, evidence generation | Implemented |
| 4 | Live ROS 2 / Gazebo runtime verification | Implemented (static-only fall-back where applicable) |
| 5 | ROS host qualification & continuous runtime validation | Implemented |
| 6 | Incident reconstruction & telemetry correlation | Implemented |
| 7 | Live Foxglove replay integration | Implemented |
| 8 | Replay coverage analytics | Implemented |
| 9 | Source-to-replay regression correlation | Implemented |
| 10 | Reliability programme review & longitudinal governance | Implemented |
| 11 | Reviewer export package & notebook scaffolding | Implemented |
| 12 | Reviewer operations playbook & portfolio presentation | Implemented (this layer) |
| 13 | Live runtime maturity (Jazzy CI, real bags, real source-change series) | Pending |

See [`ROADMAP.md`](ROADMAP.md) for the full breakdown.

## What is live, simulated, static, partial, or missing

| Surface | Today's reality |
| --- | --- |
| Deterministic Python core scenarios | **Live** — 14/14 passing in CI |
| Per-scenario evidence artifacts | **Live** — regenerated every run |
| Traceability matrix | **Live** — generated from registry + verification |
| ROS 2 / Gazebo runtime | **Static-only** by default; live execution requires a Jazzy host and is honestly labelled |
| Incident reconstructions | **Canonical fixtures**; same generator runs against real bags when available |
| Foxglove replay reviews | **Canonical fixtures**; bag-backed mode requires live bags |
| Replay analytics | **Live** — over the canonical incident corpus |
| Reliability impact reports | **Canonical fixture**; same generator runs over a real source-change series |
| Programme review | **Live** — over the on-disk evidence and history |
| Reviewer export bundle | **Live** — regenerated and validated in CI |

The repository never hides the gap; see
[`docs/LIVE_RUNTIME_STATUS.md`](LIVE_RUNTIME_STATUS.md).

## How to start as a reviewer

1. Read [`REVIEWER_PLAYBOOK.md`](REVIEWER_PLAYBOOK.md) to pick the
   path that matches your role and how much time you have.
2. Skim [`SCENARIO_VERIFICATION_REPORT.md`](SCENARIO_VERIFICATION_REPORT.md)
   to see the latest passing/failing matrix.
3. Open `reviewer-export/` to see the eight CSV/JSONL tables that
   summarise the engineering evidence.

## Disclaimers

- The project is **not safety-certified**.
- Live runtime claims are limited and explicitly labelled. Anything
  not labelled "live" should be assumed to be canonical-fixture-driven
  or static-only.
- No causality is claimed by any aggregation or analytics layer.
