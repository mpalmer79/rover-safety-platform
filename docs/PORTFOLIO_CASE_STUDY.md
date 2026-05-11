# Portfolio Case Study

The platform is **not safety-certified**. This document is the
narrative arc of the project for a portfolio reviewer — a hiring
manager, principal engineer, or robotics reliability lead who wants
the story before they read the code.

## 1. The problem

In aerospace, defence-adjacent unmanned systems, industrial
robotics, and warehouse logistics, the hard part of autonomy is not
"can it move." The hard part is:

> Prove the autonomy stack could not have moved the vehicle
> unsafely — and reconstruct exactly what happened if something
> went wrong.

Most public-facing rover projects don't try to answer that. They
optimise for "the robot moved" and leave the engineering disciplines
that make autonomy *trustworthy under uncertainty* unaddressed:
single-authority safety, deterministic execution, replayable state,
mechanical traceability, honest reporting.

Project Boundary is built around that gap.

## 2. The thesis

A simulated rover is enough surface area to *prove* the disciplines
that matter:

- **architectural authority** — only one component can authorise
  motion, and the authority is enforceable in code,
- **deterministic behaviour** — every safety transition is allowed-
  list checked and reason-coded,
- **replayable state** — every scenario emits structured events
  sufficient to reconstruct safety and mission transitions,
- **mechanical traceability** — REQ-* IDs link to architecture,
  modules, scenarios, tests, and evidence,
- **honest reporting** — `passed` / `failed` / `partial` /
  `skipped` / `not_executed`, with `static-only` and `missing-bag`
  flags propagated end-to-end,
- **no causal claims** in aggregation layers,
- **no fake green** anywhere.

The thesis is that *if you build for those disciplines first*, the
autonomy you put on top inherits a credible safety story. The
opposite — bolting evidence on top of opportunistic autonomy —
produces nothing a reliability engineer can defend.

## 3. The arc, phase by phase

| Phase | Theme | Pivotal artefact |
| --- | --- | --- |
| 0 | Architecture authority layer | `ARCHITECTURE.md`, `docs/SAFETY_MODEL.md`, ADR-001..005 |
| 1A | Deterministic Python autonomy core | `backend/app/safety/`, `backend/app/mission/`, `backend/app/replay/` |
| 1B | ROS 2 / Gazebo bringup | `rover_ws/` packages with shared contracts |
| 1C | Runtime hardening + integration verification | `backend/app/validation/scenario_suite.py`, `tools/run_scenario_suite.py` |
| 2 | Mission runtime + deterministic navigation | `backend/app/mission/orchestrator.py`, world model + keepouts |
| 3 | Verification, scenario certification, evidence | `backend/app/verification/`, `evidence/scenarios/`, traceability + verification report |
| 4 | Live ROS 2 / Gazebo runtime verification | `backend/app/runtime_validation/`, `rover_ws/tools/runtime_capture.py` |
| 5 | ROS host qualification + continuous runtime validation | `rover_ws/tools/qualify_ros_host.py`, `qualified_runtime_run.py` |
| 6 | Incident reconstruction + telemetry correlation | `backend/app/incident_analysis/`, `incidents/` |
| 7 | Live Foxglove replay integration | `backend/app/replay_review/`, `rover_ws/tools/build_replay_review_bundle.py` |
| 8 | Replay coverage analytics | `backend/app/replay_analytics/`, `incidents/analytics/` |
| 9 | Source-to-replay regression correlation | `backend/app/reliability_impact/`, `reliability-impact/` |
| 10 | Reliability programme review + longitudinal governance | `backend/app/programme_review/`, `programme-review/` |
| 11 | Reviewer export package + notebook scaffolding | `backend/app/reviewer_exports/`, `reviewer-export/` |
| 12 | Reviewer operations playbook + portfolio presentation | This document, `REVIEWER_PLAYBOOK.md`, diagrams |
| 13 | Live runtime maturity + bag-backed evidence pipeline | `backend/app/live_runtime/`, `.github/workflows/live-runtime-evidence.yml` |
| 14A | Deterministic natural-language mission compiler | `backend/app/natural_language_mission/`, `mission-library/` |
| 14B | Pluggable LLM mission proposal layer (offline / mock-only) | `backend/app/mission_proposal/`, `mission-proposals/` |
| 15A | Deterministic robotics skill authoring workbench (offline / template-only) | `backend/app/skill_authoring/`, `skill-library/` |

Each phase had hard-out-of-scope rules: no SLAM, no perception ML,
no RL, no cloud robotics, no hardware drivers, no UI polish, no
weakening of the safety authority model, no fake green. The phase
gates are visible as commits and PR titles in `git log`.

## 4. What this project says about the engineer

Reviewing the repository, you should be able to conclude the
following from the artefacts alone:

1. **The engineer designs for verifiability first.** The safety
   authority model, event contract, fault contract, and replay
   contract were written before the autonomy that runs on top.
2. **The engineer reports honestly.** Every scenario has an
   observed-vs-expected entry. Static-only fall-backs are labelled.
   Missing history is reported, not synthesised. Aggregation layers
   refuse to claim causality.
3. **The engineer scales discipline longitudinally.** The
   programme-review and reviewer-export layers turn the per-scenario
   discipline into a long-term governance surface — trends,
   freshness, drift, gates, coverage evolution.
4. **The engineer treats reviewers as users.** Phase 11 exports
   reviewer-friendly CSV/JSONL, with a notebook that runs on the
   standard library. Phase 12 (this layer) restructures the docs
   for a 5 / 15 / 45 minute review.
5. **The engineer respects scope.** Each phase is small, focused,
   and ends at a phase gate. No phase quietly expands into
   neighbouring territory.

## 5. What this project does not claim

- It does not claim safety certification.
- It does not claim live runtime maturity beyond what
  [`docs/LIVE_RUNTIME_STATUS.md`](LIVE_RUNTIME_STATUS.md) says.
- It does not claim its incident corpus or reliability impact
  reports are derived from real production bags — they are
  canonical fixtures unless a Jazzy host runs the live capture
  pipelines.
- It does not claim its aggregations are causal.
- It does not claim novelty in autonomy algorithms — the autonomy
  is intentionally minimal so the architecture is what stands out.

## 6. What a Phase 13 would have to prove

If a reviewer asks "what would close the live-runtime gap?", the
honest answer is:

- A persistent Jazzy CI runner that executes the runtime layers and
  emits live `evidence/runtime/<id>/` bundles.
- A bag corpus generated from real Gazebo runs (not canonical
  fixtures) and propagated through the replay-review and replay-
  analytics pipelines.
- A real source-change series exercising
  `analyze_source_impact.py` with non-fixture commit data.
- A Foxglove session replay produced from a live bag and validated
  by `validate_replay_review.py`.
- A programme-review run against the resulting longitudinal corpus
  with at least one trend that is not `insufficient_history`.

Phase 12 explicitly does **not** ship those — it only labels the
gap so a reviewer knows where to look.

## 7. How to evaluate the project quickly

- **5 minutes**: read [`EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md).
- **15 minutes**: add `ARCHITECTURE.md` skim and the
  `docs/SCENARIO_VERIFICATION_REPORT.md` table.
- **45 minutes**: walk
  [`ARCHITECTURE_WALKTHROUGH.md`](ARCHITECTURE_WALKTHROUGH.md),
  open one scenario's evidence under
  `evidence/scenarios/<id>/`, then open `reviewer-export/` and
  the `programme-review/` bundle.

For a per-audience reading path, see
[`REVIEWER_PLAYBOOK.md`](REVIEWER_PLAYBOOK.md).

## 8. Related documents

- [`WHY_THIS_PROJECT_EXISTS.md`](WHY_THIS_PROJECT_EXISTS.md)
- [`EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md)
- [`ARCHITECTURE_WALKTHROUGH.md`](ARCHITECTURE_WALKTHROUGH.md)
- [`SCENARIO_DEMO_GUIDE.md`](SCENARIO_DEMO_GUIDE.md)
- [`TECHNICAL_REVIEW_CHECKLIST.md`](TECHNICAL_REVIEW_CHECKLIST.md)
- [`REVIEWER_PLAYBOOK.md`](REVIEWER_PLAYBOOK.md)
- [`LIVE_RUNTIME_STATUS.md`](LIVE_RUNTIME_STATUS.md)
- [`ROADMAP.md`](ROADMAP.md)
