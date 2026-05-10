# Incident Reconstruction

This document describes the Phase 6 incident reconstruction layer.
The platform is **not safety-certified**; the reconstruction layer
produces engineering analysis artefacts from available simulation
and runtime evidence.

## 1. Purpose

Captured evidence (`evidence/scenarios/<scenario_id>/`,
`evidence/runtime/<run_id>/`) tells you *what was recorded*. The
reconstruction layer turns that into *what happened, why, and what
the safety response did about it* — without rewriting the underlying
artefacts and without inventing causality the evidence does not
support.

## 2. Architectural principle

The package is **read-only with respect to runtime evidence**. It
loads, normalises, classifies, and reports. It does **not**:

- mutate any source file,
- alter replay artefacts,
- rewrite scenario or runtime status,
- change safety or mission state in any system,
- claim safety certification.

Every report carries the certification disclaimer verbatim.

## 3. Pipeline

```
loader -> normaliser -> timeline -> causality -> classifier -> reporter
                                                                 |
                                                                 v
                          evidence-manifest.json + foxglove-replay-hints.json
```

| Module | Responsibility |
| --- | --- |
| `loader.py` | Reads scenario + runtime artefact directories. Missing files / malformed JSON / empty event streams become `LoaderWarning` entries. |
| `normalizer.py` | Converts heterogeneous records (events.jsonl, command-audit, replay-integrity, runtime-validation, regression, host-qualification) into canonical `TimelineEntry`s. Preserves the `evidence_origin`. |
| `timeline.py` | Sorts by `(sim_time_ns, timestamp, original_index)` deterministically; computes relative times; flags out-of-order entries; identifies first-fault, first-safety-transition, first-command-intervention, terminal entry. |
| `causality.py` | Rule-based chain reconstruction with confidence levels. Missing links downgrade the chain; contradictions are surfaced explicitly. |
| `classifier.py` | Derives `severity`, `outcome`, `evidence_status` plus the best-evidence cause. Conservative: missing files always degrade to `partial` or worse. |
| `reporter.py` | Renders Markdown + JSON, including the disclaimer, missing-evidence section, and contradictions section. |
| `foxglove.py` | Emits `foxglove-replay-hints.json` and the canonical layout under `foxglove/layouts/`. Tests do not require Foxglove to be installed. |
| `index.py` | Per-incident manifest with severity / outcome / evidence-status filters. |
| `compare.py` | Cross-incident comparison with safety-response latency, command-audit deltas, replay status. |

## 4. Status vocabulary

The reporter uses three controlled enums:

| Severity | Outcome | Evidence status |
| --- | --- | --- |
| `informational` | `controlled_degradation` | `complete` |
| `low` | `safe_stop_success` | `partial` |
| `moderate` | `estop_latched` | `static_only` |
| `high` | `mission_aborted` | `live_runtime` |
| `critical` | `recovery_success` | `not_executed` |
|  | `recovery_failed` | `missing` |
|  | `inconclusive` | `inconsistent` |

Severity is never upgraded above what the evidence supports. A
report with a missing event stream will not claim severity = `low`
just because the safety transitions look clean.

## 5. Causality confidence levels

| Confidence | Meaning |
| --- | --- |
| `direct` | Every link in the chain is observed in the evidence. |
| `strong` | Every link observed; the rule is heuristic but supported. |
| `moderate` | At least one link is inferred (no direct event evidence). |
| `weak` | The chain is inferred from a single observation (e.g. a fault entry without supporting transitions). |
| `inconclusive` | The chain contains contradictions or no evidence. |

Reports label inferred links with `inferred=yes` so reviewers see
the difference between observed and inferred causality.

## 6. Reconstructing an incident

```bash
python3 rover_ws/tools/reconstruct_incident.py \
  --scenario evidence/scenarios/stale_lidar_restricted_mode \
  --runs-root runs/verify \
  --incident-id stale-lidar-canonical \
  --output incidents/stale-lidar-canonical
```

The bundle (`incidents/<incident_id>/`) contains:

| File | Purpose |
| --- | --- |
| `incident-report.md` / `.json` | Operator-readable + machine-readable report. |
| `timeline.md` / `.json` | Ordered event timeline. |
| `timeline-sequence.mmd` | Mermaid sequence diagram of the supervisory chain. |
| `timeline-state.mmd` | Mermaid state diagram of the safety walk. |
| `causality.md` | Chain-by-chain explanation with Mermaid flowcharts. |
| `recommendations.md` | Deterministic, evidence-driven recommendations. |
| `evidence-manifest.json` | Per-file presence, origin, and notes. |
| `foxglove-replay-hints.json` | Topics, layout pointer, timeline markers. |

## 7. Indexing and comparison

```bash
# Build the incident index.
python3 rover_ws/tools/index_incidents.py
# Compare two bundles.
python3 rover_ws/tools/compare_incidents.py incidents/a incidents/b \
  --comparison-id stale-vs-estop
```

The index supports filters (`severity`, `outcome`, `scenario_id`,
`evidence_status`, `terminal_safety_state`) directly in
`app.incident_analysis.IncidentIndex.filter`.

## 8. Honesty rules

- A run with `mode=static-only` and no events.jsonl is reported as
  `static_only`, not `complete`.
- An `incident-report.json` that disagrees with `events.jsonl` is
  reported as `inconsistent` with the contradiction listed verbatim.
- The reporter never invents missing transitions; missing links are
  named in the chain's `missing_links` list.
- Every report carries the certification disclaimer.

## 9. Related documents

- [docs/INCIDENT_ANALYSIS_STRATEGY.md](INCIDENT_ANALYSIS_STRATEGY.md) — strategic principles.
- [docs/INCIDENT_INDEX.md](INCIDENT_INDEX.md) — generated index.
- [docs/FOXGLOVE_REPLAY_WORKFLOW.md](FOXGLOVE_REPLAY_WORKFLOW.md) — operator workflow for the Foxglove layout.
- [docs/REPLAY_SYSTEM.md](REPLAY_SYSTEM.md) — underlying replay contract.
- [docs/VERIFICATION_STRATEGY.md](VERIFICATION_STRATEGY.md) — Phase-3 verification context.
