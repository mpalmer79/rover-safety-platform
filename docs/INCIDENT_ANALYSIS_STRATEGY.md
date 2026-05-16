# Incident Analysis Strategy

This document captures the principles the Phase 6 analysis layer
follows. The platform is **not safety-certified**; this strategy is
engineering reliability discipline calibrated for a portfolio robotics
platform.

## 1. Read-only evidence handling

The analysis layer never mutates source artifacts. It loads, copies,
projects, and renders. If an analysis run wants to add value it must
do so by emitting a new file under `incidents/<incident_id>/` — never
by editing the underlying scenario or runtime evidence.

## 2. No fabricated causality

A report may not assert a causal link the evidence does not support.
The causality engine recognises four failure modes and labels them
explicitly:

| Failure mode | Treatment |
| --- | --- |
| Link present and observed | `direct` confidence |
| Link present but inferred from a different signal | `inferred=yes`, confidence ≤ `moderate` |
| Link missing | recorded in the chain's `missing_links` list, confidence downgraded |
| Link contradicts another piece of evidence | recorded in `contradictions`, chain is `inconclusive`, evidence_status becomes `inconsistent` |

The reporter renders all four cases in dedicated sections.

## 3. Conservative classification

The classifier is conservative on three axes:

- **Severity** is never higher than the worst signal supports;
  contradictions force severity to `high`.
- **Outcome** is `inconclusive` whenever a chain reports a
  contradiction.
- **Evidence status** is `partial` when documented files are missing,
  `static_only` when the run captured no live event stream, and
  `inconsistent` when contradictions exist.

A clean-looking outcome is never reported when the evidence does not
support it.

## 4. Honest disclaimers

Every report carries the verbatim certification disclaimer:

> This report is an engineering analysis artifact generated from
> available simulation and runtime evidence. It does not represent
> safety certification or regulatory approval.

A reviewer must be able to read any single artifact (the JSON, the
Markdown, the timeline diagram) and not mistake it for a regulatory
attestation.

## 5. Evidence origin labelling

Every timeline entry carries `evidence_origin` ∈
`{static-source, static-workspace, live-runtime, scenario-evidence,
runtime-evidence, unknown}`. The reporter and Foxglove hint
generator preserve the origin so reviewers see whether a transition
was observed in `events.jsonl` (live-recorded) or rolled up from a
scenario summary file.

The canonical scenario evidence directories ship a versioned
`events.jsonl` snapshot so the analysis layer can run end-to-end
without the gitignored `runs/` directory. Such events still carry
`evidence_origin = scenario-evidence` because their source is a
committed scenario fixture, not a live ROS recording.

## 6. Determinism

Timeline ordering is deterministic for a given evidence set. The
sort key is `(sim_time_ns, timestamp, original_position)`. When
multiple records share a `sim_time_ns`, the original position breaks
the tie, so a re-run of the analysis on the same input produces
byte-identical output (apart from the `generated_at_utc` stamp,
which the reporter places in a single, easy-to-mask line).

## 7. Test discipline

Tests run without ROS or Gazebo. Every code path that depends on
the absence of an artifact has a synthetic test fixture (an empty
events.jsonl, a malformed JSON file, a missing run dir) so the
loader's structured warnings are exercised.

## 8. Boundaries

The analysis layer **does not**:

- replace any safety logic,
- bypass the supervisor's authority model,
- generate or modify replay artifacts,
- claim certification,
- perform live ROS / Gazebo work,
- substitute for the Phase-3 scenario verifier or the Phase-4 runtime
  validator (it consumes their output).

## 9. Related documents

- [docs/INCIDENT_RECONSTRUCTION.md](INCIDENT_RECONSTRUCTION.md)
- [docs/REPLAY_SYSTEM.md](REPLAY_SYSTEM.md)
- [docs/VERIFICATION_STRATEGY.md](VERIFICATION_STRATEGY.md)
- [docs/RUNTIME_VALIDATION_RUNBOOK.md](RUNTIME_VALIDATION_RUNBOOK.md)
- [docs/RUNTIME_QUALIFICATION_RUNBOOK.md](RUNTIME_QUALIFICATION_RUNBOOK.md)
