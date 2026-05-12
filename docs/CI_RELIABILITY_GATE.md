# CI Reliability Gate

This document describes the deterministic CI gate produced by
`backend/app/reliability_impact/ci_gate.py` and surfaced through
`rover_ws/tools/reliability_impact_gate.py`. The platform is **not
safety-certified**; the gate is engineering reliability material.

## 1. Decision surface

The gate emits one of:

| Status | Exit code | Meaning |
| --- | --- | --- |
| `passed` | 0 | no failure conditions; warnings (if any) recorded for review |
| `warning` | 0 | no failure conditions but one or more warnings recorded |
| `failed` | 1 | at least one documented failure condition is true |
| `not_executed` | 0 | the analysis layer could not run (e.g. impact report missing) |

The gate is **independent of the risk assessment**. A `high` risk
run can still pass the gate when none of the failure conditions
fire. The risk assessment is the operator-facing summary; the gate
is the hard signal CI consumes.

## 2. Failure conditions (exhaustive)

A gate fails **only** when one of the following is true:

1. **Critical analytics regression.** The replay-analytics delta
   reports at least one `critical_regression` entry (score crossed
   below 40, new contradictions, replay honesty violation, or
   bag-backed reverted to missing-bag).
2. **Replay honesty violation.** Any delta entry with
   `category == "honesty"` and severity `regression` or
   `critical_regression` (e.g. an incident is now labelled
   `bag-backed` while its `bag_status` is `missing_bag` / `static_only`).
3. **Safety / motion change with no evidence recipe.** A
   safety-critical subsystem (safety, mission, motion, replay,
   runtime_validation, observability) changed but the evidence
   mapper emitted no `recommended_tools`. This means the reviewer
   has no automated way to regenerate the relevant evidence — a
   high-risk situation regardless of analytics deltas.
4. **Static-validation workflow removed.** The file
   `.github/workflows/runtime-static-validation.yml` was deleted or
   renamed. The CI safety net for live-mode probes would disappear.
5. **Traceability matrix failed.** The caller passes
   `traceability_passed=False` (e.g. the docs-traceability workflow
   regenerated the matrix and saw drift).
6. **Tests failed.** The caller passes `tests_passed=False`.

## 3. Warning conditions

Warnings never fail the gate but are surfaced in the report:

* analytics delta severity is `regression` or `warning`;
* the baseline is unavailable or partially present;
* unknown files were touched (paths outside the documented prefix
  table);
* any subsystem was classified as `unknown`.

## 4. Honesty rules

- **Missing live runtime evidence on a github-hosted runner is not
  a failure.** The gate detects the github-hosted environment (via
  `RUNNER_ENVIRONMENT=github-hosted`, or assumes github-hosted
  when unset) and adds a note explaining the exception.
- **First-run / missing-baseline state is not a failure.** Treated
  as a warning so the first CI run on a fresh clone is not broken.
- **Static-only incidents remain static-only.** The gate never
  treats a static-only baseline + static-only current as a
  regression.
- **The gate does not infer source-level causality.** Even when a
  safety file changed and an analytics regression appeared, the
  report records both observations but never claims the source
  change caused the regression — the reviewer establishes that.

## 5. Configuring the gate from CI

The default CI workflow
(`.github/workflows/reliability-impact.yml`) runs the analyzer
with `--ci-github-hosted` so the gate's runner detection is
explicit. The gate then exits non-zero only when one of the
documented failure conditions is true.

To run the gate locally:

```bash
python3 rover_ws/tools/analyze_source_impact.py \
  --base-ref origin/main --head-ref HEAD \
  --output reliability-impact/

python3 rover_ws/tools/reliability_impact_gate.py
```

The gate reads `reliability-impact/impact-report.json` by default.

## 6. Baseline lifecycle

Baselines are pinned files under `reliability-baselines/`:

* `replay-quality-index.baseline.json`
* `replay-analytics-report.baseline.json`

Update them intentionally:

```bash
python3 rover_ws/tools/analyze_source_impact.py \
  --changed-files . \
  --write-baseline \
  --output reliability-impact/
```

The `--write-baseline` flag is the **only** path that mutates the
baseline. CI never refreshes baselines automatically. When a
regen is required, commit the new baseline alongside the analytics
change that caused the drift.

## 7. Related documents

- [docs/RELIABILITY_IMPACT_ANALYSIS.md](RELIABILITY_IMPACT_ANALYSIS.md)
- [docs/SOURCE_TO_EVIDENCE_TRACEABILITY.md](SOURCE_TO_EVIDENCE_TRACEABILITY.md)
- [docs/REPLAY_ANALYTICS.md](REPLAY_ANALYTICS.md)
- [docs/ARTIFACT_STABILIZATION_PASS.md](ARTIFACT_STABILIZATION_PASS.md)
- [docs/TESTING_STRATEGY.md §16](TESTING_STRATEGY.md)

## 8. Phase 20B — CI job ordering + read-only check

The reliability gate now expects CI jobs to run in this order:

1. checkout
2. backend pytest with random order + coverage gate
3. rover_ws static pytest suite
4. frontend typecheck
5. frontend tests
6. frontend build
7. honesty greps (no websocket, no EventSource, no `bag_backed: true`)
8. traceability verification

The hydration `--check-only` invocation is now read-only — it must
not be a CI step that introduces a dirty working tree. The
canonical-fixture artefacts are committed to disk and verified by
`backend/tests/test_artifact_registry.py::test_canonical_registry_paths_match_disk`
plus the Phase 20B
`backend/tests/test_artifact_fixture_commitment.py`.
