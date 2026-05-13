# Architecture Walkthrough

The platform is **not safety-certified**. This document is a guided
tour of the architecture for an engineer who has 30–45 minutes and
wants to understand *how the pieces fit together* before opening
the code.

For diagrams, see [`docs/diagrams/`](diagrams/).

## 1. Reading order

If you only read three files in this repo, read them in this order:

1. [`ARCHITECTURE.md`](../ARCHITECTURE.md) — principles, authority model, layering
2. [`docs/SAFETY_MODEL.md`](SAFETY_MODEL.md) — state machine, transitions, reason codes
3. [`docs/EVENT_MODEL.md`](EVENT_MODEL.md) — what gets recorded and why

Then come back here.

## 2. The two implementations

```
┌───────────────────────────────┐    ┌───────────────────────────────┐
│ Deterministic Python core     │    │ ROS 2 Jazzy / Gazebo Harmonic │
│  backend/app/                 │    │  rover_ws/                    │
│  - safety supervisor          │    │  - lifecycle nodes            │
│  - mission runtime            │    │  - safety bridge              │
│  - world model                │    │  - mission orchestrator node  │
│  - fault injection            │    │  - launch graphs              │
│  - replay                     │    │  - bag capture                │
│  - verification               │    │  - replay review nodes        │
│  - programme review           │    │  - runtime capture            │
│  - reviewer export            │    │                               │
└───────────────────────────────┘    └───────────────────────────────┘
                  │                                 │
                  └──── shared contracts ───────────┘
                         events / motion authority
                         fault injection / replay
```

The two sides share the same **contracts** but not the same code.
The Python core is dependency-free and runs anywhere; the ROS 2
workspace passes static validation everywhere and end-to-end on a
Jazzy host.

## 3. Layered view of the Python core

`backend/app/` is layered. Lower layers do not depend on higher
layers.

```
runtime / verification / programme review / reviewer export   ←  evidence + governance
                       ▲
mission / replay / fault injection / world model              ←  application surface
                       ▲
safety supervisor / motion arbitration / freshness / watchdogs ←  authority + invariants
                       ▲
domain types / events / enums                                  ←  shared vocabulary
```

| Module | Role | Key files |
| --- | --- | --- |
| `domain/` | Plain types, enums, geometry | — |
| `safety/` | Single-authority supervisor, arbitration, freshness, watchdogs, confidence, transition rules | `supervisor.py`, `arbitration.py`, `transitions.py` |
| `mission/` | Orchestrator, waypoint executor, recovery framework, constraints, transitions | `orchestrator.py`, `controller.py`, `recovery.py`, `transitions.py` |
| `world_model/` | Keepout / restricted zones, occupancy, snapshots | — |
| `faults/` | Fault library; mutates *inputs*, never safety state | — |
| `replay/` | Recorder, loader, run manifests | `recorder.py`, `manifest.py` |
| `simulation/` | Deterministic scenario engine (no external dependencies) | — |
| `telemetry/`, `diagnostics/` | Observability surface | — |
| `verification/` | Requirements registry, scenario verifier, evidence generator, audits, traceability | — |
| `runtime_validation/` | Live runtime validation pipeline (ROS-aware; static-only fall-back) | — |
| `incident_analysis/` | Incident reconstruction + index | — |
| `replay_review/`, `replay_analytics/` | Replay review reports + cross-incident analytics | — |
| `reliability_impact/` | Source-change → replay-quality correlation | — |
| `programme_review/` | Longitudinal governance rollup | — |
| `reviewer_exports/` | Reviewer-friendly CSV/JSONL/JSON-Schema bundle | — |

## 4. The safety authority model

**The single most important invariant in the project**: only the
safety supervisor can authorise motion. Every actuator command flows
through one auditable pipeline:

```
Mission Runtime  ─requests─▶  Safety Supervisor  ─authorises─▶  Motion Arbitration  ─actuates─▶  Hardware Gateway
                                     ▲
              freshness gates ───────┤
              watchdogs       ───────┤
              confidence      ───────┤
              operator inputs ───────┘
```

- Mission, navigation, perception code may **request** motion.
- Only the supervisor, given valid inputs and a permitted state, may
  **authorise** motion.
- The boundary is enforced *in code*, *exercised by scenarios*, and
  *audited mechanically*.

Audit tools that prove the invariant holds:

- `tools/audit_command_path.py` — for every recorded command, was it
  requested before authorised, and never authorised in excess of the
  active safety constraints?
- `tools/audit_safety_transitions.py` — was every safety state
  transition allowed by the state machine, with a reason code?

See [`docs/SAFETY_MODEL.md`](SAFETY_MODEL.md) for the state machine
and [`docs/diagrams/safety-authority.md`](diagrams/safety-authority.md)
for the authority diagram.

## 5. The safety state machine

States: `ACTIVE_NORMAL`, `ACTIVE_DEGRADED`, `RESTRICTED`,
`SAFE_STOP`, `E_STOP_LATCHED`, `RECOVERY`.

Properties:

- Allowed-list checked on every transition.
- Each transition carries a reason code.
- E-stop is *latched*; it requires an explicit, operator-acknowledged
  reset to leave.
- Recovery validates required input streams before re-entering
  `ACTIVE_*`.

Tested by:

- unit tests in `backend/tests/test_safety_*`,
- scenario `estop_latched_manual_reset_required` (latching
  invariant),
- scenarios `*_safe_stop` and `*_degraded_mode` (transition causes),
- scenario `safe_stop_during_active_mission` (mission cannot
  override safe-stop).

## 6. The event model and replay

Every meaningful runtime fact is emitted as an **event** — a typed,
schema-validated record with a monotonic timestamp, a reason, and
the originating subsystem. Events are appended to per-run
`events.jsonl` and accompanied by a `manifest.json`.

Properties enforced:

- ordered emission,
- consistent `run_id` and `scenario_id`,
- replayable safety + mission transitions,
- markers where required (e.g. recovery completion),
- `replay-integrity.json` audit per scenario.

See [`docs/EVENT_MODEL.md`](EVENT_MODEL.md),
[`docs/REPLAY_SYSTEM.md`](REPLAY_SYSTEM.md), and
[`docs/diagrams/replay-flow.md`](diagrams/replay-flow.md).

## 7. The fault-injection contract

Faults mutate **inputs**:

- sensor readings (lidar staleness, IMU bias, wheel slip),
- command timeouts,
- bridge disconnects,
- watchdog pet failures.

Faults never reach into the safety state machine directly. The
supervisor reacts through its normal mechanisms (freshness gates,
watchdogs, confidence). This is the property that makes safety
behaviour *predictable under fault* rather than *encoded in the
fault library*.

See [`docs/FAULT_INJECTION.md`](FAULT_INJECTION.md).

## 8. The verification layer (Phase 3)

`backend/app/verification/` is the engineering-evidence layer:

- `requirements.py` — typed registry of REQ-* IDs (safety, fault,
  replay, mission, world, diagnostics, operator, runtime, incident,
  qualification, replay-review, analytics, impact, programme,
  export).
- `scenario_verifier.py` — runs a scenario through the deterministic
  engine and grades its observed outcome against expected.
- `evidence.py` — emits per-scenario `evidence.json`,
  `events-summary.md`, `replay-integrity.json`,
  `command-audit.json`, `safety-transition-audit.json`.
- `traceability.py` — links REQ-* → tests → scenarios → artifacts.
- `report_generator.py` — emits `docs/SCENARIO_VERIFICATION_REPORT.md`
  with an honest status code per scenario.

Reports use `passed` / `failed` / `partial` / `skipped` /
`not_executed`.

## 9. The runtime + qualification layers (Phases 4–5)

`backend/app/runtime_validation/` and `rover_ws/tools/` add:

- live runtime validation (`live_runtime_validator.py`,
  `runtime_capture.py`),
- ROS host qualification (`qualify_ros_host.py`,
  `qualified_runtime_run.py`),
- a `static-only` fall-back when no Jazzy host is present —
  honestly labelled, never silently skipped.

See [`docs/RUNTIME_VALIDATION_RUNBOOK.md`](RUNTIME_VALIDATION_RUNBOOK.md)
and [`docs/RUNTIME_QUALIFICATION_RUNBOOK.md`](RUNTIME_QUALIFICATION_RUNBOOK.md).

## 10. Incident reconstruction + replay review (Phases 6–7)

`backend/app/incident_analysis/` and `backend/app/replay_review/`:

- reconstruct incidents from runtime evidence,
- score replay reviews against bag-backed or static-only inputs,
- preserve `static_only` and `missing_bag` flags verbatim,
- produce `incident-report.json` and `replay-review-report.json`.

See [`docs/INCIDENT_ANALYSIS_STRATEGY.md`](INCIDENT_ANALYSIS_STRATEGY.md),
[`docs/INCIDENT_RECONSTRUCTION.md`](INCIDENT_RECONSTRUCTION.md),
[`docs/FOXGLOVE_REPLAY_WORKFLOW.md`](FOXGLOVE_REPLAY_WORKFLOW.md),
[`docs/REPLAY_REVIEW_RUNBOOK.md`](REPLAY_REVIEW_RUNBOOK.md).

## 11. Replay analytics + reliability impact (Phases 8–9)

`backend/app/replay_analytics/` aggregates across the incident
corpus to produce coverage, gap, and quality scores.
`backend/app/reliability_impact/` correlates source-change series
with replay-quality movements — *correlations, not causations*.

See [`docs/REPLAY_ANALYTICS.md`](REPLAY_ANALYTICS.md),
[`docs/REPLAY_QUALITY_SCORING.md`](REPLAY_QUALITY_SCORING.md),
[`docs/REPLAY_GAP_ANALYSIS.md`](REPLAY_GAP_ANALYSIS.md),
[`docs/RELIABILITY_IMPACT_ANALYSIS.md`](RELIABILITY_IMPACT_ANALYSIS.md),
[`docs/SOURCE_TO_EVIDENCE_TRACEABILITY.md`](SOURCE_TO_EVIDENCE_TRACEABILITY.md).

## 12. Programme review (Phase 10)

`backend/app/programme_review/` is the longitudinal governance layer:

- trend analysis (rolling-3 / rolling-5 windows, deterministic
  classifier),
- drift detection (informational / warning / regression / critical),
- governance health (six-discipline rollup),
- evidence freshness (reference-time-driven, never `datetime.now()`),
- subsystem risk (frequency + severity, `causality_claimed=false`),
- coverage evolution + gate history.

See [`docs/PROGRAMME_REVIEW.md`](PROGRAMME_REVIEW.md),
[`docs/GOVERNANCE_HEALTH_MODEL.md`](GOVERNANCE_HEALTH_MODEL.md),
[`docs/RELIABILITY_TREND_ANALYSIS.md`](RELIABILITY_TREND_ANALYSIS.md),
[`docs/EVIDENCE_FRESHNESS_POLICY.md`](EVIDENCE_FRESHNESS_POLICY.md),
[`docs/SUBSYSTEM_RISK_AGGREGATION.md`](SUBSYSTEM_RISK_AGGREGATION.md),
[`docs/CI_RELIABILITY_GATE.md`](CI_RELIABILITY_GATE.md).

## 13. Reviewer export (Phase 11)

`backend/app/reviewer_exports/` packages every prior layer's outputs
into reviewer-friendly artifacts:

- 8 CSV tables, 8 JSONL mirrors, 8 JSON Schemas (draft 2020-12),
- a `manifest.json` with row counts and disclaimer,
- a notebook scaffold (`reviewer_walkthrough.ipynb`) that does not
  import ROS, Gazebo, or Foxglove,
- a `reviewer-export-summary.md` with a verbatim disclaimer.

`causality_claimed` is pinned `const: false` at schema level.

See [`docs/REVIEWER_EXPORTS.md`](REVIEWER_EXPORTS.md),
[`docs/EXPORT_SCHEMA_REFERENCE.md`](EXPORT_SCHEMA_REFERENCE.md),
[`docs/REVIEWER_NOTEBOOK_GUIDE.md`](REVIEWER_NOTEBOOK_GUIDE.md).

## 14. The presentation layer (Phase 12)

This is the layer you are reading. It adds:

- [`REVIEWER_PLAYBOOK.md`](REVIEWER_PLAYBOOK.md) — per-audience reading paths,
- [`EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md) — five-minute version,
- this walkthrough,
- [`SCENARIO_DEMO_GUIDE.md`](SCENARIO_DEMO_GUIDE.md) — running and observing scenarios,
- [`TECHNICAL_REVIEW_CHECKLIST.md`](TECHNICAL_REVIEW_CHECKLIST.md) — what to poke at,
- [`PORTFOLIO_CASE_STUDY.md`](PORTFOLIO_CASE_STUDY.md) — narrative arc,
- [`WHY_THIS_PROJECT_EXISTS.md`](WHY_THIS_PROJECT_EXISTS.md) — motivation,
- diagrams for system flow, evidence flow, replay flow, and safety
  authority under [`docs/diagrams/`](diagrams/).

No new runtime behaviour. Pure packaging.

## 15. Cross-references

- [`ARCHITECTURE.md`](../ARCHITECTURE.md)
- [`docs/SYSTEM_CONTEXT.md`](SYSTEM_CONTEXT.md)
- [`docs/SAFETY_MODEL.md`](SAFETY_MODEL.md)
- [`docs/EVENT_MODEL.md`](EVENT_MODEL.md)
- [`docs/REPLAY_SYSTEM.md`](REPLAY_SYSTEM.md)
- [`docs/FAULT_INJECTION.md`](FAULT_INJECTION.md)
- [`docs/VERIFICATION_STRATEGY.md`](VERIFICATION_STRATEGY.md)
- [`docs/TESTING_STRATEGY.md`](TESTING_STRATEGY.md)
- [`docs/TRACEABILITY_MATRIX.md`](TRACEABILITY_MATRIX.md)
- [`docs/SCENARIO_VERIFICATION_REPORT.md`](SCENARIO_VERIFICATION_REPORT.md)
- [`docs/adr/`](adr/)
