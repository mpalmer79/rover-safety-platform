# Reviewer Playbook

The platform is **not safety-certified**. This playbook is the
front door for a reviewer. It tells you *what to read first* based
on **how much time you have** and **why you are reviewing**.

If in doubt, start with the [5-minute path](#5-minute-path-everyone)
and then pick the audience-specific path that fits.

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
