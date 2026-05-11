# Reviewer Playbook

The platform is **not safety-certified**. This playbook is the
front door for a reviewer. It tells you *what to read first* based
on **how much time you have** and **why you are reviewing**.

If in doubt, start with the [5-minute path](#5-minute-path-everyone)
and then pick the audience-specific path that fits.

**Phase 17C addition.** For reviewers focused on the
bag-backed spatial replay layer:

* `docs/BAG_BACKED_SPATIAL_REPLAY.md` — evidence hierarchy + what
  a real bag-backed run produces.
* `docs/SPATIAL_REPLAY_HONESTY_RULES.md` — the rules that
  gatekeep the `bag_backed` label across backend, frontend, and
  CI.
* `docs/SPATIAL_REPLAY_ARTIFACT_FORMAT.md` — the on-disk schema
  of `spatial-replay/runs/<id>/spatial-replay.json`.
* `docs/BAG_TO_TRAJECTORY_PIPELINE.md` — how a self-hosted runner
  becomes a `bag_backed` artefact.
* `backend/app/spatial_replay/` — the package; the manifest loader
  and validator are the single source of truth for honesty rules.
* `spatial-replay/runs/canonical-fixture/spatial-replay.json` —
  the committed canonical fixture artefact (labelled `fixture`,
  never `bag_backed`).

**Phase 19 addition.** For reviewers focused on the design system,
local LLM intelligence layer, and bag-backed readiness:

* `docs/MISSION_CONTROL_DESIGN_SYSTEM.md` — token + theme rules.
* `docs/THEME_AND_RESPONSIVE_UI.md` — light/dark + responsive layout.
* `docs/LOCAL_LLM_INTELLIGENCE_UPGRADE.md` — ranking, repair,
  critique, readiness.
* `docs/LLM_CANDIDATE_RANKING_MODEL.md` — the deterministic
  scoring rules.
* `docs/LLM_REPAIR_SUGGESTIONS.md` — repair surface (suggestion
  only).
* `docs/FIRST_BAG_BACKED_RUN_PLAYBOOK.md` — exact operator
  workflow for the first real bag-backed run.
* `docs/REVIEWER_SCENE_SNAPSHOT_GUIDE.md` — snapshot metadata
  contract.

**Phase 18 addition.** For reviewers focused on the artefact
governance layer + immersive UX:

* `docs/ARTIFACT_GOVERNANCE_MODEL.md` — the registry's lifecycle
  ladder, integrity model, and why-it-exists.
* `docs/DETERMINISTIC_REPLAY_HYDRATION.md` — the hydration CLI +
  the CI gates that make it deterministic.
* `docs/REPLAY_EVIDENCE_LINEAGE.md` — how a reviewer reads the
  source-to-render chain from one panel.
* `docs/IMMERSIVE_MISSION_CONTROL.md` — what's in the 3D scene
  and how the WebGL fallback works.
* `docs/3D_VISUALIZATION_BOUNDARY.md` — the hard boundary the
  immersive scene must respect.
* `docs/CINEMATIC_REPLAY_ARCHITECTURE.md` — camera rig + playback
  modes.
* `docs/AUTONOMY_UI_DESIGN_SYSTEM.md` — palette, typography,
  panels, motion.
* `spatial-replay/registry/canonical-artifacts.json` — the
  canonical registry; the only authoritative index of replay
  artefacts.

## How to use this playbook

1. Pick a column from the [audience matrix](#audience-matrix).
2. Read the entries for the time you have (5 / 15 / 45 minutes).
3. Use the [reading-order shortcuts](#reading-order-shortcuts) to
   open files in the right order.
4. If you want to *verify* claims rather than read them, jump to
   [`TECHNICAL_REVIEW_CHECKLIST.md`](TECHNICAL_REVIEW_CHECKLIST.md).

---

## 5-minute path (everyone)

If you only have 5 minutes:

1. [`docs/EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md) — what the
   project is, what it proves, what is live vs static, the
   disclaimer.
2. The status table in the top-level
   [`README.md`](../README.md#status) — phase-by-phase implementation
   state.
3. The summary table in
   [`docs/SCENARIO_VERIFICATION_REPORT.md`](SCENARIO_VERIFICATION_REPORT.md)
   — current pass / fail / partial / skipped / not_executed counts.

That is enough to understand the scope, the honesty bar, and the
current state of the engineering evidence.

---

## 15-minute path (everyone)

Add to the 5-minute path:

4. [`docs/WHY_THIS_PROJECT_EXISTS.md`](WHY_THIS_PROJECT_EXISTS.md) —
   the engineering motivation and the gap the project closes.
5. [`docs/diagrams/system-flow.md`](diagrams/system-flow.md) and
   [`docs/diagrams/safety-authority.md`](diagrams/safety-authority.md)
   — two diagrams that show how everything fits together.
6. [`ARCHITECTURE.md`](../ARCHITECTURE.md) (sections 1, 2, and 3) —
   principles, authority model, layering.

---

## 45-minute path (everyone)

Add to the 15-minute path:

7. [`docs/ARCHITECTURE_WALKTHROUGH.md`](ARCHITECTURE_WALKTHROUGH.md)
   — module-by-module narrative tour.
8. [`docs/SAFETY_MODEL.md`](SAFETY_MODEL.md) — state machine,
   transitions, reason codes.
9. [`docs/EVENT_MODEL.md`](EVENT_MODEL.md) and
   [`docs/REPLAY_SYSTEM.md`](REPLAY_SYSTEM.md) — event contract +
   replay contract.
10. One `evidence/scenarios/<id>/evidence.md` of your choice —
    e.g. `stale_lidar_restricted_mode` or
    `estop_latched_manual_reset_required`.
11. [`reviewer-export/reviewer-export-summary.md`](../reviewer-export/reviewer-export-summary.md)
    and any one of the eight CSV tables under `reviewer-export/csv/`.

---

## Audience matrix

| Audience | Best 5-min entry | Best 15-min addition | Best 45-min deep dive |
| --- | --- | --- | --- |
| Recruiter / non-technical | [`EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md) | [`WHY_THIS_PROJECT_EXISTS.md`](WHY_THIS_PROJECT_EXISTS.md), README status table | [`PORTFOLIO_CASE_STUDY.md`](PORTFOLIO_CASE_STUDY.md) |
| Senior software engineer | [`EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md) | [`ARCHITECTURE.md`](../ARCHITECTURE.md), [`SAFETY_MODEL.md`](SAFETY_MODEL.md) | [`ARCHITECTURE_WALKTHROUGH.md`](ARCHITECTURE_WALKTHROUGH.md), [`TECHNICAL_REVIEW_CHECKLIST.md`](TECHNICAL_REVIEW_CHECKLIST.md), one `evidence/scenarios/<id>/` |
| Robotics / ROS 2 reviewer | [`EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md) | [`LIVE_RUNTIME_STATUS.md`](LIVE_RUNTIME_STATUS.md), [`RUNTIME_VALIDATION_RUNBOOK.md`](RUNTIME_VALIDATION_RUNBOOK.md) | `rover_ws/README.md`, `rover_ws/tests/manual.md`, [`RUNTIME_QUALIFICATION_RUNBOOK.md`](RUNTIME_QUALIFICATION_RUNBOOK.md), [`FOXGLOVE_REPLAY_WORKFLOW.md`](FOXGLOVE_REPLAY_WORKFLOW.md) |
| Verification / reliability reviewer | [`EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md) | [`SCENARIO_VERIFICATION_REPORT.md`](SCENARIO_VERIFICATION_REPORT.md), [`TRACEABILITY_MATRIX.md`](TRACEABILITY_MATRIX.md) | [`VERIFICATION_STRATEGY.md`](VERIFICATION_STRATEGY.md), [`PROGRAMME_REVIEW.md`](PROGRAMME_REVIEW.md), [`GOVERNANCE_HEALTH_MODEL.md`](GOVERNANCE_HEALTH_MODEL.md), [`REVIEWER_EXPORTS.md`](REVIEWER_EXPORTS.md) |

---

## Per-audience details

### Recruiter / non-technical reviewer

**Goal**: confirm the project is real, the scope is honest, and the
engineering disciplines on display are credible.

What to read:

- [`EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md) — one-page version
  with phase status table.
- [`WHY_THIS_PROJECT_EXISTS.md`](WHY_THIS_PROJECT_EXISTS.md) — the
  motivating gap and the audiences it serves.
- [`PORTFOLIO_CASE_STUDY.md`](PORTFOLIO_CASE_STUDY.md) — the
  narrative arc by phase, what the artefacts say about the
  engineer.

What to look for:

- Every report carries the verbatim **not safety-certified**
  disclaimer.
- The status table separates `passed`, `failed`, `partial`,
  `skipped`, `not_executed`.
- The phase status table goes 0 → 12 with each phase tied to
  concrete artefacts.

### Senior software engineer

**Goal**: form a quick opinion of architectural quality, invariant
discipline, and test coverage.

What to read:

- [`ARCHITECTURE.md`](../ARCHITECTURE.md) — principles, authority
  model, layering.
- [`docs/SAFETY_MODEL.md`](SAFETY_MODEL.md) — state machine,
  transitions, reason codes.
- [`docs/ARCHITECTURE_WALKTHROUGH.md`](ARCHITECTURE_WALKTHROUGH.md)
  — module tour.
- [`docs/TECHNICAL_REVIEW_CHECKLIST.md`](TECHNICAL_REVIEW_CHECKLIST.md)
  — concrete things to poke at.
- One `evidence/scenarios/<id>/evidence.md` plus its three audit
  JSONs (`safety-transition-audit.json`, `command-audit.json`,
  `replay-integrity.json`).
- [`docs/TESTING_STRATEGY.md`](TESTING_STRATEGY.md).

What to look for:

- The supervisor is the *only* path to actuator authorisation.
- Every state transition is allowed-list checked and reason-coded.
- Faults mutate inputs, not state.
- Tests cover authority, latching, freshness, recovery, and
  scenario outcomes.
- Audits are runnable on any run directory, not coupled to the
  generator that produced it.

### Robotics / ROS 2 reviewer

**Goal**: confirm the ROS 2 layer is consistent with the
deterministic core, and understand what is live vs static today.

What to read:

- [`docs/LIVE_RUNTIME_STATUS.md`](LIVE_RUNTIME_STATUS.md) — what is
  live vs static-only right now.
- [`rover_ws/README.md`](../rover_ws/README.md) and
  [`rover_ws/tests/manual.md`](../rover_ws/tests/manual.md).
- [`docs/RUNTIME_VALIDATION_RUNBOOK.md`](RUNTIME_VALIDATION_RUNBOOK.md)
  and [`docs/RUNTIME_QUALIFICATION_RUNBOOK.md`](RUNTIME_QUALIFICATION_RUNBOOK.md).
- [`docs/FOXGLOVE_REPLAY_WORKFLOW.md`](FOXGLOVE_REPLAY_WORKFLOW.md)
  and [`docs/REPLAY_REVIEW_RUNBOOK.md`](REPLAY_REVIEW_RUNBOOK.md).
- ADR-001 and ADR-002 under [`docs/adr/`](adr/).

What to look for:

- The ROS 2 / Gazebo path honours the same event, motion-authority,
  fault-injection, and replay contracts as the Python core.
- When no Jazzy host is available, the runtime layers fall back to
  `static-only` and label the result honestly.
- `evidence/runtime/<id>/runtime-validation.json` carries an
  explicit `mode` field.
- The Foxglove replay path does not auto-mix bag-backed and static
  evidence.

### Verification / reliability reviewer

**Goal**: confirm requirements, scenarios, tests, and evidence are
mechanically linked, and that aggregations refuse to claim
causality or fabricate history.

What to read:

- [`docs/VERIFICATION_STRATEGY.md`](VERIFICATION_STRATEGY.md) —
  scope, vocab, verifier inventory, evidence layout.
- [`docs/TRACEABILITY_MATRIX.md`](TRACEABILITY_MATRIX.md) and
  `verification/traceability.json`.
- [`docs/SCENARIO_VERIFICATION_REPORT.md`](SCENARIO_VERIFICATION_REPORT.md).
- [`docs/PROGRAMME_REVIEW.md`](PROGRAMME_REVIEW.md),
  [`docs/GOVERNANCE_HEALTH_MODEL.md`](GOVERNANCE_HEALTH_MODEL.md),
  [`docs/RELIABILITY_TREND_ANALYSIS.md`](RELIABILITY_TREND_ANALYSIS.md),
  [`docs/EVIDENCE_FRESHNESS_POLICY.md`](EVIDENCE_FRESHNESS_POLICY.md),
  [`docs/SUBSYSTEM_RISK_AGGREGATION.md`](SUBSYSTEM_RISK_AGGREGATION.md),
  [`docs/CI_RELIABILITY_GATE.md`](CI_RELIABILITY_GATE.md).
- [`docs/REVIEWER_EXPORTS.md`](REVIEWER_EXPORTS.md),
  [`docs/EXPORT_SCHEMA_REFERENCE.md`](EXPORT_SCHEMA_REFERENCE.md),
  [`docs/REVIEWER_NOTEBOOK_GUIDE.md`](REVIEWER_NOTEBOOK_GUIDE.md).

What to look for:

- Every REQ-* is mapped to architecture refs, modules, scenarios,
  tests, and (where applicable) evidence artefacts.
- Reports use only the documented status vocabulary.
- Trend categories include `insufficient_history`; programme review
  never forecasts.
- `subsystem_risk` always reports `causality_claimed=false`.
- Reliability impact reports use correlation language, never
  causation.
- Reviewer-export schemas pin `causality_claimed: {"const": false}`.

---

## Reading-order shortcuts

If you want to read sequentially, here is the order that minimises
backtracking:

1. [`README.md`](../README.md)
2. [`docs/EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md)
3. [`docs/WHY_THIS_PROJECT_EXISTS.md`](WHY_THIS_PROJECT_EXISTS.md)
4. [`ARCHITECTURE.md`](../ARCHITECTURE.md)
5. [`docs/SAFETY_MODEL.md`](SAFETY_MODEL.md)
6. [`docs/EVENT_MODEL.md`](EVENT_MODEL.md)
7. [`docs/REPLAY_SYSTEM.md`](REPLAY_SYSTEM.md)
8. [`docs/FAULT_INJECTION.md`](FAULT_INJECTION.md)
9. [`docs/ARCHITECTURE_WALKTHROUGH.md`](ARCHITECTURE_WALKTHROUGH.md)
10. [`docs/SCENARIO_DEMO_GUIDE.md`](SCENARIO_DEMO_GUIDE.md)
11. [`docs/TECHNICAL_REVIEW_CHECKLIST.md`](TECHNICAL_REVIEW_CHECKLIST.md)
12. [`docs/VERIFICATION_STRATEGY.md`](VERIFICATION_STRATEGY.md)
13. [`docs/TRACEABILITY_MATRIX.md`](TRACEABILITY_MATRIX.md)
14. [`docs/SCENARIO_VERIFICATION_REPORT.md`](SCENARIO_VERIFICATION_REPORT.md)
15. [`docs/PROGRAMME_REVIEW.md`](PROGRAMME_REVIEW.md)
16. [`docs/REVIEWER_EXPORTS.md`](REVIEWER_EXPORTS.md)
17. [`docs/PORTFOLIO_CASE_STUDY.md`](PORTFOLIO_CASE_STUDY.md)

---

## Diagrams

| Diagram | Purpose |
| --- | --- |
| [`docs/diagrams/system-flow.md`](diagrams/system-flow.md) | High-level system flow |
| [`docs/diagrams/safety-authority.md`](diagrams/safety-authority.md) | Single-authority motion-command path |
| [`docs/diagrams/evidence-flow.md`](diagrams/evidence-flow.md) | How evidence flows from scenario → reviewer export |
| [`docs/diagrams/replay-flow.md`](diagrams/replay-flow.md) | Event recording → replay → reconstruction |

All diagrams are inline Mermaid in markdown; GitHub renders them
natively.

---

## Common reviewer questions

| Question | Where the answer lives |
| --- | --- |
| What problem does this solve? | [`WHY_THIS_PROJECT_EXISTS.md`](WHY_THIS_PROJECT_EXISTS.md) |
| Why is this different from a rover demo? | [`PORTFOLIO_CASE_STUDY.md`](PORTFOLIO_CASE_STUDY.md) §1–§2 |
| What does the architecture prove? | [`ARCHITECTURE.md`](../ARCHITECTURE.md), [`docs/SAFETY_MODEL.md`](SAFETY_MODEL.md) |
| Where should I look first? | This playbook + [`EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md) |
| What evidence supports the claims? | `evidence/`, `incidents/`, `programme-review/`, `reviewer-export/` |
| What is live, simulated, static, partial, or missing? | [`LIVE_RUNTIME_STATUS.md`](LIVE_RUNTIME_STATUS.md), [`EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md) §"What is live…" |
| What would Phase 13 need to prove? | [`PORTFOLIO_CASE_STUDY.md`](PORTFOLIO_CASE_STUDY.md) §6, [`WHY_THIS_PROJECT_EXISTS.md`](WHY_THIS_PROJECT_EXISTS.md) §6 |

---

## Phase 14B (LLM mission proposal layer) entry points

If you are reviewing the Phase 14B work specifically:

1. Start with [`LLM_MISSION_PROPOSAL_LAYER.md`](LLM_MISSION_PROPOSAL_LAYER.md)
   — the architectural contract and where the seam plugs in.
2. Read [`LLM_SAFETY_BOUNDARY.md`](LLM_SAFETY_BOUNDARY.md) for what
   the proposal layer is forbidden from doing.
3. Skim [`MISSION_PROPOSAL_AUDIT.md`](MISSION_PROPOSAL_AUDIT.md) and
   one fixture bundle under `mission-proposals/audits/`.
4. Read [`FUTURE_LLM_INTEGRATION_PLAN.md`](FUTURE_LLM_INTEGRATION_PLAN.md)
   if you care about the path forward.

No real LLM API is called. External provider modes return a
deterministic ``not_configured`` response. The deterministic Phase
14A mission compiler remains authoritative for what is interpretable;
the runtime safety supervisor remains authoritative for what moves.

---

## Phase 15A (robotics skill authoring workbench) entry points

If you are reviewing the Phase 15A work specifically:

1. Start with [`ROBOTICS_SKILL_AUTHORING_WORKBENCH.md`](ROBOTICS_SKILL_AUTHORING_WORKBENCH.md)
   — architectural contract.
2. Read [`SKILL_SAFETY_BOUNDARY.md`](SKILL_SAFETY_BOUNDARY.md) for
   what the workbench is forbidden from doing.
3. Skim [`SKILL_TEMPLATE_CATALOG.md`](SKILL_TEMPLATE_CATALOG.md) for
   the supported skill list + safety constraints, and one accepted
   audit bundle (e.g. `skill-library/audits/move_forward_6_feet/`).
4. Read [`CODE_CARD_METADATA.md`](CODE_CARD_METADATA.md) if you care
   about the code-card payload a future UI would render.
5. Read [`FUTURE_LOCAL_LLM_SKILL_PROVIDER.md`](FUTURE_LOCAL_LLM_SKILL_PROVIDER.md)
   if you care about the path forward (intentionally not
   implemented in Phase 15A).

No real LLM, no code execution, no robot motion. The deterministic
template catalog and validator are authoritative for what the
workbench can emit; the runtime safety supervisor remains
authoritative for what actually moves.

---

## Phase 15B (local LLM skill candidate provider) entry points

If you are reviewing the Phase 15B work specifically:

1. Start with [`LOCAL_LLM_SKILL_PROVIDER.md`](LOCAL_LLM_SKILL_PROVIDER.md)
   — architectural contract for the disabled-by-default provider.
2. Read [`LOCAL_LLM_PROVIDER_SAFETY_BOUNDARY.md`](LOCAL_LLM_PROVIDER_SAFETY_BOUNDARY.md)
   for what the provider is forbidden from doing.
3. Skim [`SKILL_LLM_CANDIDATE_AUDITS.md`](SKILL_LLM_CANDIDATE_AUDITS.md)
   and one accepted bundle under
   `skill-llm-candidates/audits/fixture_valid_move_forward_6_feet/`.
4. Read [`LOCAL_LLM_SKILL_PROMPT_CONTRACT.md`](LOCAL_LLM_SKILL_PROMPT_CONTRACT.md)
   for the JSON-only contract a future local model must satisfy.
5. Read [`FUTURE_LOCAL_MODEL_OPERATIONS.md`](FUTURE_LOCAL_MODEL_OPERATIONS.md)
   if you care about the path forward (intentionally not
   implemented in Phase 15B).

No cloud API is called. No network socket is opened. No generated
code is executed. The deterministic Phase 15A skill validator and
the runtime safety supervisor remain authoritative.

---

## Phase 16 (governed mission-to-rehearsal pipeline) entry points

If you are reviewing the Phase 16 work specifically:

1. Start with [`GOVERNED_MISSION_REHEARSAL.md`](GOVERNED_MISSION_REHEARSAL.md)
   — architectural contract for the pipeline.
2. Read [`REHEARSAL_SAFETY_BOUNDARY.md`](REHEARSAL_SAFETY_BOUNDARY.md)
   for what the pipeline is forbidden from doing.
3. Skim [`MISSION_REHEARSAL_STATE_MACHINE.md`](MISSION_REHEARSAL_STATE_MACHINE.md)
   and [`SIMULATION_REHEARSAL_PIPELINE.md`](SIMULATION_REHEARSAL_PIPELINE.md)
   for the state transitions + JSON schema.
4. Open one accepted bundle under
   `mission-rehearsals/audits/warehouse_pickup_route_alpha/`
   (request, plan, events, timeline, replay, analytics, audit).
5. Read [`REHEARSAL_REPLAY_INTEGRATION.md`](REHEARSAL_REPLAY_INTEGRATION.md)
   for the bag-backed honesty rule and the analytics shape.
6. Read [`FUTURE_DIGITAL_TWIN_DIRECTION.md`](FUTURE_DIGITAL_TWIN_DIRECTION.md)
   if you care about the path forward (intentionally not
   implemented in Phase 16).

The pipeline is simulation-only and deterministic. The runtime
safety supervisor and motion arbitration remain authoritative; no
artefact in this directory authorises live robot motion.

---

## Phase 17A (mission control UI) entry points

If you are reviewing the Phase 17A work specifically:

1. Start with [`MISSION_CONTROL_UI.md`](MISSION_CONTROL_UI.md) for
   the architectural overview and screen list.
2. Read [`AUTONOMY_VISUALIZATION_GUIDE.md`](AUTONOMY_VISUALIZATION_GUIDE.md)
   for the per-component design rationale.
3. Read [`OPERATOR_WORKSTATION_ARCHITECTURE.md`](OPERATOR_WORKSTATION_ARCHITECTURE.md)
   for the adapter layer and data flow.
4. Read [`REPLAY_VIEWER_GUIDE.md`](REPLAY_VIEWER_GUIDE.md) and
   [`SAFETY_AUTHORITY_VISUALIZATION.md`](SAFETY_AUTHORITY_VISUALIZATION.md)
   for the two screens that anchor the safety story.
5. Run the workspace locally:
   ```
   cd apps/mission-control
   npm install
   npm run test
   npm run build
   npm run dev
   ```

The UI never opens a network socket, never imports a cloud SDK,
never executes generated code, and never marks simulated rehearsal
evidence as bag-backed. The runtime safety supervisor and motion
arbitration remain authoritative.

---

## Phase 17B (Railway + spatial visualisation) entry points

If you are reviewing the Phase 17B work specifically:

1. Start with [`MISSION_SPATIAL_VISUALIZATION.md`](MISSION_SPATIAL_VISUALIZATION.md)
   for the deterministic 2D map architecture.
2. Read [`MISSION_REPLAY_MAPS.md`](MISSION_REPLAY_MAPS.md) for the
   per-mission detail composition.
3. Read [`SPATIAL_REPLAY_ARCHITECTURE.md`](SPATIAL_REPLAY_ARCHITECTURE.md)
   for the data-flow diagram and the dock-close-of-route
   convention.
4. Read [`RAILWAY_DEPLOYMENT_GUIDE.md`](RAILWAY_DEPLOYMENT_GUIDE.md)
   for the Railway lane and the CI gate.
5. Read [`OPERATOR_EXPERIENCE_GUIDELINES.md`](OPERATOR_EXPERIENCE_GUIDELINES.md)
   for the UX rules every new panel follows.
6. Skim `apps/mission-control/tests/spatial.test.ts`,
   `apps/mission-control/tests/deployment.test.ts`, and the
   prerendered HTML grep step in
   `.github/workflows/mission-control-ci.yml` — those are the
   honesty contract.

The spatial layer derives coordinates deterministically from the
audit's bounded inputs. No real-world telemetry is implied; every
map labels its derivation source.

---

## What this playbook does not do

- It does not run anything for you. To run scenarios and inspect
  evidence, see
  [`SCENARIO_DEMO_GUIDE.md`](SCENARIO_DEMO_GUIDE.md).
- It does not catalogue every doc in `docs/` —
  [`EVIDENCE_INDEX.md`](EVIDENCE_INDEX.md) and
  [`REPLAY_REVIEW_INDEX.md`](REPLAY_REVIEW_INDEX.md) cover the
  generated indexes; this playbook routes you to the *first*
  things to read.
- It does not make safety-certification claims.
