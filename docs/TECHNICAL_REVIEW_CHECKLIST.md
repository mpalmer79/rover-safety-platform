# Technical Review Checklist

The platform is **not safety-certified**. This checklist gives a
technical reviewer concrete things to poke at to satisfy themselves
the architecture, invariants, and reporting are honest.

Every check below is *something a reviewer can verify themselves
in this repo*, not something they have to take on trust.

## 1. Authority invariants (10 minutes)

- [ ] Open `backend/app/safety/supervisor.py` and confirm motion
      authorisation goes through one function with explicit guard
      clauses. There is no second authoriser anywhere.
- [ ] Open `backend/app/mission/orchestrator.py` and confirm mission
      code only ever *requests* motion (no direct actuator path).
- [ ] Run `python tools/audit_command_path.py --runs-root runs/verify`
      and confirm every authorised command has a matching prior
      request, and authorisation never exceeds the active safety
      constraints.
- [ ] Run `python tools/audit_safety_transitions.py --runs-root runs/verify`
      and confirm every transition is in the allowed list and carries
      a reason code.
- [ ] Confirm there is **no** code path under
      `backend/app/faults/` that mutates `SafetyState` or any
      member of `backend/app/safety/`. Faults change inputs only.

## 2. State-machine integrity (5 minutes)

- [ ] Open `backend/app/safety/transitions.py` and confirm the
      transition rules are an explicit allowed list (data, not
      branching logic).
- [ ] Open `backend/tests/test_safety_*` and verify that:
      - E-stop is latched (cannot transition to `ACTIVE_*` without
        an explicit reset),
      - `RECOVERY` validates required input streams before re-entry,
      - degraded / restricted transitions carry reason codes.
- [ ] Run the scenario `estop_latched_manual_reset_required` and
      confirm the latching is exercised end-to-end.

## 3. Replay reconstructability (10 minutes)

- [ ] Open any `runs/verify/<scenario>/events.jsonl` and confirm
      events are ordered, schema-validated, and carry consistent
      `run_id` / `scenario_id`.
- [ ] Run `python tools/verify_replay_integrity.py --runs-root runs/verify`
      and confirm every required marker is present.
- [ ] Open `evidence/scenarios/<id>/replay-integrity.json` for any
      scenario and confirm it reports `passed`.
- [ ] Confirm `static_only` and `missing_bag` flags propagate
      verbatim into `incidents/<id>/replay-review-report.json` and
      from there into `reviewer-export/csv/replay_quality.csv`.

## 4. Traceability + verification reporting (10 minutes)

- [ ] Open `verification/traceability.json` and confirm every REQ-*
      ID lists architecture references, implementation pointers,
      scenarios, tests, and (where applicable) evidence artefacts.
- [ ] Open `docs/TRACEABILITY_MATRIX.md` and confirm there are no
      silently unmapped requirements (gap rows are visible if any
      exist).
- [ ] Open `docs/SCENARIO_VERIFICATION_REPORT.md` and confirm:
      - the status table uses `passed` / `failed` / `partial` /
        `skipped` / `not_executed` (and only those values),
      - per-scenario rows record fired faults and recovery counts,
      - `overall=passed` is supported by per-row evidence.
- [ ] Re-run `python tools/generate_traceability.py --with-verification`
      and confirm the matrix regenerates byte-stably.

## 5. Honest fall-backs (5 minutes)

- [ ] Open `docs/LIVE_RUNTIME_STATUS.md` and confirm it lists what
      is live vs static-only today.
- [ ] Open any `evidence/runtime/<id>/runtime-validation.json` and
      confirm the `mode` field reports `static-only` or live, with
      the limitation explicit when applicable.
- [ ] Confirm CI workflows under `.github/workflows/` that target
      live ROS behaviour either run on a Jazzy host or downgrade to
      static-only with a labelled outcome.

## 6. No-causality discipline (5 minutes)

- [ ] Open `backend/app/programme_review/subsystem_risk.py` and
      confirm the rollup is frequency + severity, never causal.
- [ ] Open `backend/app/reliability_impact/` and confirm reports
      use *correlation* language only.
- [ ] Open `reviewer-export/schemas/subsystem_risk.schema.json` and
      confirm `causality_claimed` is `{"const": false}`.
- [ ] Open any `reliability-impact/*/impact-report.json` and confirm
      narrative fields use "may", "observed alongside", "correlated"
      — never "caused by".

## 7. Programme-review honesty (10 minutes)

- [ ] Open `programme-review/programme-review.md` and confirm:
      - trends use the documented vocabulary (`improving`, `stable`,
        `degrading`, `volatile`, `insufficient_history`),
      - drift uses `informational` / `warning` / `regression` /
        `critical_regression`,
      - governance health uses `strong` / `acceptable` / `weak` /
        `concerning` / `critical`,
      - missing history shows up as `insufficient_history` and is
        never forecast.
- [ ] Run `python rover_ws/tools/review_evidence_freshness.py
      --reference-time 2026-05-12T00:00:00Z` and confirm the
      reference time, not `datetime.now()`, drives freshness.
- [ ] Run `python rover_ws/tools/review_governance_health.py
      --reference-time 2026-05-12T00:00:00Z` twice and confirm
      byte-identical output.

## 8. Reviewer export validity (5 minutes)

- [ ] Run `python rover_ws/tools/validate_reviewer_export.py
      --bundle reviewer-export/` and confirm all 11 checks pass.
- [ ] Open `reviewer-export/manifest.json` and confirm the verbatim
      certification disclaimer is present.
- [ ] Open `reviewer-export/notebooks/reviewer_walkthrough.ipynb`
      and confirm there is no `import rclpy`, no `rosbag2`, and no
      `import foxglove*` in any code cell.

## 9. Test strategy (5 minutes)

- [ ] Open `docs/TESTING_STRATEGY.md` and confirm tests are
      categorised (unit / integration / scenario / CLI / static /
      runtime).
- [ ] Run `pytest -q` from `backend/` and confirm a non-zero count
      passes deterministically.
- [ ] Confirm tests do not depend on a real Gazebo unless explicitly
      marked / skipped when unavailable.

## 10. Scope discipline (5 minutes)

- [ ] Confirm no SLAM, perception ML, RL, cloud robotics, or
      hardware-driver code has been added under any phase. (Every
      phase brief calls these out as out-of-scope.)
- [ ] Confirm the runtime layers (Phases 4–5) honestly fall back to
      static-only when no Jazzy host is available.
- [ ] Confirm Phase 12 (this presentation layer) adds no runtime
      behaviour — it is pure documentation, diagrams, and README
      restructuring.

## 11. Disclaimer presence

- [ ] Top-level README contains the "not safety-certified" line.
- [ ] Every generated report contains the disclaimer (search:
      `git grep "not safety-certified"`).
- [ ] Reviewer-export `manifest.json` and `reviewer-export-summary.md`
      carry the disclaimer verbatim.

## 12. Tools used in this checklist

| Tool | Location |
| --- | --- |
| `audit_command_path.py` | `tools/` |
| `audit_safety_transitions.py` | `tools/` |
| `verify_replay_integrity.py` | `tools/` |
| `generate_traceability.py` | `tools/` |
| `generate_verification_report.py` | `tools/` |
| `generate_evidence.py` | `tools/` |
| `run_scenario_suite.py` | `tools/` |
| `generate_replay_analytics.py` | `rover_ws/tools/` |
| `analyze_source_impact.py` | `rover_ws/tools/` |
| `generate_programme_review.py` | `rover_ws/tools/` |
| `review_governance_health.py` | `rover_ws/tools/` |
| `review_evidence_freshness.py` | `rover_ws/tools/` |
| `generate_reviewer_export.py` | `rover_ws/tools/` |
| `validate_reviewer_export.py` | `rover_ws/tools/` |

## 13. Related documents

- [`REVIEWER_PLAYBOOK.md`](REVIEWER_PLAYBOOK.md)
- [`SCENARIO_DEMO_GUIDE.md`](SCENARIO_DEMO_GUIDE.md)
- [`ARCHITECTURE_WALKTHROUGH.md`](ARCHITECTURE_WALKTHROUGH.md)
- [`VERIFICATION_STRATEGY.md`](VERIFICATION_STRATEGY.md)
- [`TESTING_STRATEGY.md`](TESTING_STRATEGY.md)
- [`LIVE_RUNTIME_STATUS.md`](LIVE_RUNTIME_STATUS.md)
