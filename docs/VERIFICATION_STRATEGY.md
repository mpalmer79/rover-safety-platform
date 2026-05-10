# Verification Strategy

> **The platform is not safety-certified.** This document describes
> the engineering verification discipline used by the project — a
> safety-case-style preparation appropriate for portfolio and learning
> purposes. It does not claim conformance to ISO 13849, ISO 26262,
> IEC 61508, or any other functional-safety standard. It draws on the
> *vocabulary* and *evidence discipline* of those frameworks while
> being explicit about its own limits.

## 1. What this strategy verifies

The verification layer (Phase 3) operationalises a small set of
platform-level guarantees as `REQ-*` requirement IDs and binds each
to:

* an architecture-doc reference,
* one or more implementation modules,
* one or more tests that assert the requirement directly,
* zero or more scenarios that exercise it end-to-end through the
  deterministic engine,
* an evidence artefact produced when verification runs.

The full registry lives in
[`backend/app/verification/requirements.py`](../backend/app/verification/requirements.py)
and the binding matrix is in
[`docs/TRACEABILITY_MATRIX.md`](TRACEABILITY_MATRIX.md).

## 2. Status vocabulary

Every verifier returns one of five statuses. They are chosen to make
honest reporting easy and to avoid silent passes:

| Status | Meaning |
|---|---|
| `passed` | Every check in scope held. |
| `failed` | At least one check explicitly failed. |
| `partial` | Some checks held; some are not yet evaluable from the available artefacts. The verifier produces a partial result rather than a fake pass. |
| `skipped` | The check / scenario was deliberately bypassed (operator request, environment lacking a dependency). |
| `not_executed` | The check / scenario could not run in the current environment (e.g., requires Gazebo on a Jazzy host). The reporter must include a reason. |

A scenario's overall status is the highest-severity status across its
checks (failure dominates, then partial, then not_executed, then
skipped, then passed). Empty inputs map to `not_executed` so "no
checks ran" is never misread as "all checks passed".

## 3. Verifier inventory

The verification layer is composed of several narrow pieces. Each
runs without ROS / Gazebo and operates on the recorded run directory
artefacts produced by either the deterministic engine or the ROS 2
launch.

| Verifier | Purpose | CLI |
|---|---|---|
| [`requirements`](../backend/app/verification/requirements.py) | Stable `REQ-*` registry with metadata. | (no CLI; queried by other tools) |
| [`scenario_verifier`](../backend/app/verification/scenario_verifier.py) | Runs a scenario through the deterministic engine and asserts per-scenario expectations. | `tools/generate_evidence.py` |
| [`command_audit`](../backend/app/verification/command_audit.py) | Asserts only the supervisor's arbiter constructs `AuthorizedMotionCommand`; SAFE_STOP / E_STOP / forced-zero states never carry non-zero motion; ACTIVE_* states never exceed documented limits. | `tools/audit_command_path.py` |
| [`safety_audit`](../backend/app/verification/safety_audit.py) | Asserts every observed safety state transition is permitted by `app.safety.transitions`; E_STOP_LATCHED only exits to RECOVERY; SAFE_STOP only exits to RECOVERY / E_STOP_LATCHED; every transition carries a non-empty reason code. | `tools/audit_safety_transitions.py` |
| [`replay_integrity`](../backend/app/verification/replay_integrity.py) | Composes `validate_run_directory`, `validate_mission_run`, and `validate_events_file` into a single Phase-3 status. | `tools/verify_replay_integrity.py` |
| [`evidence`](../backend/app/verification/evidence.py) | Writes per-scenario evidence directories under `evidence/scenarios/<scenario_id>/`. | `tools/generate_evidence.py` |
| [`traceability`](../backend/app/verification/traceability.py) | Generates `verification/traceability.json` and `docs/TRACEABILITY_MATRIX.md`. | `tools/generate_traceability.py` |
| [`report_generator`](../backend/app/verification/report_generator.py) | Generates `docs/SCENARIO_VERIFICATION_REPORT.md` and `verification/verification_report.json`. | `tools/generate_verification_report.py` |
| [`runtime_validation`](../backend/app/runtime_validation/) | Phase 4. Declares the expected ROS topic / node / TF graph and runs a static workspace validator plus the live probes orchestrated by `live_runtime_validator.py`. Honest about `not_executed` when ROS / Gazebo are unavailable. | `rover_ws/tools/live_runtime_validator.py` |
| [`host_qualification`](../backend/app/runtime_validation/host_qualification.py) | Phase 5. Qualifies the ROS 2 Jazzy host: Ubuntu, ROS distro, Gazebo Harmonic, colcon, required packages, backend importability, workspace structure, launch files, bridge config. | `rover_ws/tools/qualify_ros_host.py` |
| [`qualification_scenarios`](../backend/app/runtime_validation/qualification_scenarios.py) | Phase 5. YAML pack format + loader for qualification scenarios (one YAML per scenario; required topics / nodes / events / replay artefacts; expected outcome). | (consumed by the orchestrator) |
| [`baselines`](../backend/app/runtime_validation/baselines.py) | Phase 5. Per-category baseline + comparator (topics, nodes, TF, transitions, commands, events, replay artefacts, diagnostic health). Classifies deltas as `expected_difference`, `warning`, `regression`, or `critical_regression`. | `rover_ws/tools/compare_runtime_baseline.py` |
| [`regression`](../backend/app/runtime_validation/regression.py) | Phase 5. Per-run regression detector run on the captured evidence; emits findings with severity and evidence references. | (consumed by the orchestrator) |
| [`evidence_index`](../backend/app/runtime_validation/evidence_index.py) | Phase 5. Builds `docs/EVIDENCE_INDEX.md` and `evidence/runtime/index.json` from retained runs. | (consumed by the orchestrator) |
| [`qualification_report`](../backend/app/runtime_validation/qualification_report.py) | Phase 5. Aggregate report renderer; labels every check as `static-source`, `static-workspace`, or `live-runtime`. | `rover_ws/tools/qualified_runtime_run.py` |
| [`incident_analysis`](../backend/app/incident_analysis/) | Phase 6. Read-only incident reconstruction: loader, normaliser, timeline, causality (with confidence levels), classifier, reporter, Foxglove hints, index, comparison. Honest about inferred causality, missing links, and contradictory evidence. | `rover_ws/tools/reconstruct_incident.py`, `rover_ws/tools/index_incidents.py`, `rover_ws/tools/compare_incidents.py` |
| [`replay_review`](../backend/app/replay_review/) | Phase 7. Read-only replay-review layer: bag indexer, manifest generator, marker generator (with alignment labels), Foxglove session metadata generator, validator, reporter. Honest about missing bags and partial marker alignment; Foxglove session JSON labelled internal (`rover-replay-review/1`). | `rover_ws/tools/build_replay_review_bundle.py`, `rover_ws/tools/validate_replay_review.py`, `rover_ws/tools/list_replay_reviews.py` |
| [`replay_analytics`](../backend/app/replay_analytics/) | Phase 8. Read-only analytics over Phase-6 + Phase-7 artefacts: coverage metrics, deterministic 0..100 quality score with band caps (static-only ≤ 39, missing-bag ≤ 59, contradictions ≤ 39), gap detection + recommendations, operator review audit (explicit acknowledgement only), trends + cross-incident comparison + filterable index. | `rover_ws/tools/analyze_replay_coverage.py`, `rover_ws/tools/compare_replay_reviews.py`, `rover_ws/tools/generate_replay_analytics.py`, `rover_ws/tools/audit_replay_reviews.py` |
| [`reliability_impact`](../backend/app/reliability_impact/) | Phase 9. Read-only source-to-evidence traceability + analytics-delta gate. Classifies changed files by subsystem, maps subsystems to REQ-* ids + recommended tools/artefacts, compares replay analytics against a pinned baseline, assesses risk, and emits a deterministic CI gate decision. Missing live runtime evidence on github-hosted runners is **never** a failure. | `rover_ws/tools/analyze_source_impact.py`, `rover_ws/tools/reliability_impact_gate.py` |
| [`programme_review`](../backend/app/programme_review/) | Phase 10. Read-only longitudinal governance layer over Phase 3..9 artefacts. Deterministic trends, drift detection, six-discipline governance health rollup, subsystem-risk aggregation, coverage evolution, gate history, evidence freshness. Missing history is reported as `insufficient_history` / `unknown`, never as regression. | `rover_ws/tools/generate_programme_review.py`, `analyze_reliability_trends.py`, `detect_reliability_drift.py`, `review_governance_health.py`, `review_evidence_freshness.py` |
| [`reviewer_exports`](../backend/app/reviewer_exports/) | Phase 11. Read-only packaging layer that emits CSV + JSONL + JSON Schemas + a manifest + a reviewer notebook + a Markdown summary. `causality_claimed=false` enforced at the schema level; static-only / missing-bag flags preserved on every replay-quality row. | `rover_ws/tools/generate_reviewer_export.py`, `rover_ws/tools/validate_reviewer_export.py` |

## 4. Per-scenario expectations

Each Phase 1C / Phase 2 scenario has a stable
`ScenarioExpectation` declaring its requirement IDs, expected final
safety state, expected mission state (Phase 2 only), required event
types, forbidden event types, expected fired faults, recovery
expectations, and whether the SAFE_STOP zero-motion check applies.
The list lives in
[`backend/app/verification/scenario_verifier.py`](../backend/app/verification/scenario_verifier.py).

For each scenario, the verifier runs the deterministic engine and
applies up to eleven checks: `execution`, `safety_state`,
`mission_state`, `required_events`, `forbidden_events`, `fired_faults`,
`recovery_engagements`, `command_path_audit`, `safety_transition_audit`,
`replay_integrity`, and (when the scenario reaches a forced-zero
state) `safe_stop_zero_motion`.

## 5. Evidence layout

Per-scenario evidence is materialised under
`evidence/scenarios/<scenario_id>/`:

```
evidence/scenarios/<scenario_id>/
  evidence.json                  # full structured record
  evidence.md                    # human-readable summary
  events-summary.md              # safety + mission + fault timelines
  replay-integrity.json          # composed validator output
  command-audit.json             # command path audit output
  safety-transition-audit.json   # safety transition audit output
```

The directory is deterministic; re-running verification overwrites
its contents. The recorded run directory is referenced via
`evidence.json -> observed.run_dir` and is not copied into evidence/
to avoid duplication.

## 6. Reproducing a verification run

```bash
# Run every scenario and produce evidence + report + matrix.
python tools/generate_verification_report.py \
    --runs-root runs/verify \
    --evidence-root evidence \
    --md-out docs/SCENARIO_VERIFICATION_REPORT.md \
    --json-out verification/verification_report.json
python tools/generate_traceability.py \
    --json-out verification/traceability.json \
    --md-out docs/TRACEABILITY_MATRIX.md \
    --with-verification \
    --runs-root runs/verify \
    --evidence-root evidence
```

Output should always end with `overall=passed` on a healthy main
branch. A `partial`, `failed`, or `not_executed` overall status
indicates a real regression and must be triaged before merge.

## 7. What this strategy does NOT do

* **No certification claim.** This is engineering evidence, not
  regulatory evidence.
* **No live ROS / Gazebo coverage in CI.** Phase 3 verification runs
  exclusively against the deterministic Python engine. End-to-end
  Gazebo verification on a Jazzy host is documented in
  [`rover_ws/tests/manual.md`](../rover_ws/tests/manual.md); the
  results of those runs are not captured automatically by the
  verification report.
* **No automated state-estimator-driven slip detection.** The
  wheel-slip-only path does not by itself reach `MISSION_DEGRADED` —
  the corresponding scenario combines slip with a co-occurring IMU
  bias to demonstrate the degraded mode honestly. State-estimator
  integration is future work.
* **No closed-loop verification of the Nav2 boundary.** The
  velocity-clamp boundary is asserted at the source level only.
  Live verification of the clamp's effect on the actuator stream
  requires the Jazzy-host manual procedure.

## 8. Adding a new requirement

1. Pick the next free `REQ-*` ID in its category.
2. Add a `Requirement` entry in
   [`backend/app/verification/requirements.py`](../backend/app/verification/requirements.py)
   with at least one `architecture_refs` entry.
3. Add at least one `test_refs` entry that asserts it.
4. If a scenario exercises it, add a `scenario_refs` entry and either
   reuse an existing `ScenarioExpectation` or add a new one.
5. Run `pytest backend/tests/test_requirements_registry.py` to
   confirm registry hygiene.
6. Re-run `tools/generate_verification_report.py` and
   `tools/generate_traceability.py` so the report and matrix reflect
   the new binding.

## 9. Adding a new scenario

1. Drop the scenario JSON under `backend/scenarios/`.
2. Add a `ScenarioExpectation` in `scenario_verifier.py` citing the
   relevant `REQ-*` IDs.
3. Add a row in
   [`docs/TRACEABILITY_MATRIX.md`](TRACEABILITY_MATRIX.md) by
   regenerating it.
4. Verify the scenario passes the expectations:
   `pytest backend/tests/test_scenario_verifier.py -k "<scenario_id>"`.

## 10. Failure handling policy

When verification fails:

* Do not mark the scenario as `passed` or remove it from the
  expectations list. Triage the failure.
* If the failure is the verifier's bug, fix the verifier; the
  evidence directory will be regenerated next run.
* If the failure is a real platform regression, fix the platform.
* If the failure is environmental (e.g., disk space), capture the
  cause in `not_executed` reasons and re-run.
* Never silence a failure by widening the expectation tolerance
  unless an architecture-doc change accompanies the widening.
