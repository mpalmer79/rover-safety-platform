# Scenario Demo Guide

The platform is **not safety-certified**. This guide shows a reviewer
how to run, observe, and inspect the deterministic scenarios that
back the safety-architecture claims.

You can do everything below in the **Python core** with zero
external dependencies. The ROS 2 / Gazebo path is described
separately at the end and requires a Jazzy host.

## 1. The 14 verified scenarios

| Scenario | What it exercises | Expected final safety state |
| --- | --- | --- |
| `nominal_run` | Healthy baseline, no faults | `ACTIVE_NORMAL` |
| `nominal_waypoint_patrol` | Mission completes, motion stays authorised | `ACTIVE_NORMAL` (mission `MISSION_COMPLETE`) |
| `degraded_sensor_navigation` | Reduced confidence inputs, navigation continues with constraints | `ACTIVE_DEGRADED` |
| `restricted_mode_navigation` | Restricted operational envelope is honoured | `RESTRICTED` |
| `stale_lidar_restricted_mode` | Lidar staleness triggers restricted → safe-stop fall-back | `SAFE_STOP` |
| `odometry_divergence_safe_stop` | Wheel/IMU disagreement degrades or stops | `ACTIVE_DEGRADED` (or `SAFE_STOP` per scenario data) |
| `command_timeout_safe_stop` | Command channel timeout forces safe-stop | `SAFE_STOP` |
| `bridge_disconnect_safe_stop` | Bridge disconnect forces safe-stop | `SAFE_STOP` |
| `wheel_slip_degraded_mode` | IMU bias + slip drop confidence into degraded | `ACTIVE_DEGRADED` |
| `keepout_zone_violation` | Keepout boundary breach is constrained, not silenced | varies; events recorded |
| `safe_stop_during_active_mission` | Mission cannot override safe-stop | `SAFE_STOP` |
| `mission_abort_after_fault_escalation` | Fault escalation aborts the mission cleanly | `SAFE_STOP` (mission aborted) |
| `estop_latched_manual_reset_required` | E-stop latches, requires explicit reset | `E_STOP_LATCHED` |
| `waypoint_timeout_recovery` | Recovery framework runs and validates streams | varies; recovery emits events |

Latest pass/fail matrix: [`docs/SCENARIO_VERIFICATION_REPORT.md`](SCENARIO_VERIFICATION_REPORT.md).

## 2. Run the deterministic engine

From the repo root:

```bash
cd backend
pip install -e ".[dev]"
pytest                                          # full unit + integration suite
cd ..

# Run the scenario suite (Phase 1C surface)
python tools/run_scenario_suite.py

# Re-generate per-scenario evidence (Phase 3 surface)
python tools/generate_evidence.py

# Re-generate the traceability matrix + verification report
python tools/generate_traceability.py --with-verification
python tools/generate_verification_report.py
```

Each command is deterministic and emits structured output. The
verification tools also accept `--json` for machine-readable form.

## 3. What gets written

```
runs/verify/<scenario_id>/
  manifest.json
  events.jsonl
  ...
evidence/scenarios/<scenario_id>/
  evidence.json                  ← scenario metadata + observed vs expected
  evidence.md                    ← the same, human readable
  events-summary.md              ← curated event summary
  replay-integrity.json          ← replay verifier output
  command-audit.json             ← command-path audit output
  safety-transition-audit.json   ← transition audit output
docs/
  SCENARIO_VERIFICATION_REPORT.md
  TRACEABILITY_MATRIX.md
verification/
  traceability.json
```

Open `evidence/scenarios/<id>/evidence.md` for the per-scenario story.
Every artifact is regeneratable; nothing here is hand-written.

## 4. Inspect a single scenario

After `generate_evidence.py`, the easiest "see what happened"
sequence is:

```bash
# Pick any scenario id
SID=stale_lidar_restricted_mode

cat evidence/scenarios/$SID/evidence.md
cat evidence/scenarios/$SID/events-summary.md
python -m json.tool evidence/scenarios/$SID/safety-transition-audit.json
python -m json.tool evidence/scenarios/$SID/command-audit.json
python -m json.tool evidence/scenarios/$SID/replay-integrity.json
```

What to look for:

- `evidence.md` — expected vs observed safety state, mission state,
  fired faults, recovery count.
- `safety-transition-audit.json` — every state transition, whether
  it was allowed, and the reason code.
- `command-audit.json` — paired requested/authorised commands and
  whether the supervisor ever exceeded the active constraints.
- `replay-integrity.json` — ordered events, consistent ids, required
  markers present.

## 5. Run a single scenario only

```bash
python tools/generate_evidence.py --scenario stale_lidar_restricted_mode
```

`--scenario` accepts repeated values.

## 6. Run the audits standalone

```bash
python tools/audit_command_path.py        --runs-root runs/verify
python tools/audit_safety_transitions.py  --runs-root runs/verify
python tools/verify_replay_integrity.py   --runs-root runs/verify
```

These are the same audits the evidence generator runs, exposed as
standalone tools so a reviewer can point them at any run directory.

## 7. Inspect the longitudinal layer

If you want to see the Phase 8–11 outputs:

```bash
# Replay analytics across the canonical incident corpus
python rover_ws/tools/generate_replay_analytics.py
ls incidents/analytics/

# Reliability impact (canonical fixture)
python rover_ws/tools/analyze_source_impact.py --reference-time 2026-05-12T00:00:00Z
ls reliability-impact/

# Programme review (Phase 10) — full bundle
python rover_ws/tools/generate_programme_review.py --reference-time 2026-05-12T00:00:00Z
ls programme-review/

# Reviewer export (Phase 11)
python rover_ws/tools/generate_reviewer_export.py --export-id reviewer-export-canonical \
                                                  --generated-at 2026-05-12T00:00:00Z
ls reviewer-export/
python rover_ws/tools/validate_reviewer_export.py --bundle reviewer-export/
```

Every CLI accepts `--reference-time` (or `--generated-at`) so output
is deterministic and CI-stable.

## 8. The reviewer-export bundle

`reviewer-export/` is the most reviewer-friendly entry point:

| File | Purpose |
| --- | --- |
| `reviewer-export-summary.md` | Human-readable summary with disclaimer |
| `manifest.json` | Row counts, schemas, csv/jsonl paths, disclaimer |
| `csv/*.csv` | 8 reviewer tables (programme health, trend series, drift, subsystem risk, gate history, replay quality, incident index, requirement coverage) |
| `jsonl/*.jsonl` | Same data, line-delimited JSON |
| `schemas/*.schema.json` | JSON Schema (draft 2020-12) per table; `causality_claimed` pinned `const: false` |
| `notebooks/reviewer_walkthrough.ipynb` | Standard-library notebook tour; pandas/matplotlib imported behind guards; no ROS, no Foxglove |

See [`docs/REVIEWER_EXPORTS.md`](REVIEWER_EXPORTS.md) and
[`docs/REVIEWER_NOTEBOOK_GUIDE.md`](REVIEWER_NOTEBOOK_GUIDE.md).

## 9. ROS 2 / Gazebo path

The ROS 2 workspace is parallel to the Python core and honours the
same contracts. To run end-to-end you need a Jazzy + Harmonic host.

```bash
cd rover_ws
# Build (Jazzy host)
colcon build
. install/setup.bash

# Static validation (works anywhere)
colcon test --packages-select <pkg>

# Live runtime (requires Jazzy)
python tools/qualified_runtime_run.py --reference-time 2026-05-12T00:00:00Z
ls evidence/runtime/
```

Without a Jazzy host the suite reports `static-only` / `not_executed`
and writes the same evidence schema with the limitation labelled —
nothing is silently skipped.

See [`rover_ws/README.md`](../rover_ws/README.md),
[`rover_ws/tests/manual.md`](../rover_ws/tests/manual.md),
and [`docs/LIVE_RUNTIME_STATUS.md`](LIVE_RUNTIME_STATUS.md).

## 10. What you should be able to verify in 15 minutes

- The Python suite passes locally (`pytest`).
- Every scenario in `evidence/scenarios/` has an honest
  observed-vs-expected entry.
- `docs/SCENARIO_VERIFICATION_REPORT.md` reports `overall=passed`
  with an explicit count per status.
- `docs/TRACEABILITY_MATRIX.md` has zero unmapped requirements (or,
  if there are gaps, the gap rows are visible — never hidden).
- `reviewer-export/manifest.json` lists row counts and the verbatim
  certification disclaimer.
- The ROS 2 side either runs end-to-end (Jazzy host) or honestly
  reports `static-only`.

## 11. Related documents

- [`REVIEWER_PLAYBOOK.md`](REVIEWER_PLAYBOOK.md)
- [`SCENARIO_VERIFICATION_REPORT.md`](SCENARIO_VERIFICATION_REPORT.md)
- [`TRACEABILITY_MATRIX.md`](TRACEABILITY_MATRIX.md)
- [`VERIFICATION_STRATEGY.md`](VERIFICATION_STRATEGY.md)
- [`TESTING_STRATEGY.md`](TESTING_STRATEGY.md)
- [`REVIEWER_EXPORTS.md`](REVIEWER_EXPORTS.md)
- [`LIVE_RUNTIME_STATUS.md`](LIVE_RUNTIME_STATUS.md)
