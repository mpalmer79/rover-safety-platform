# Deterministic Replay Hydration (Phase 18)

The platform is **not safety-certified.** This document describes
the hydration pipeline that rebuilds canonical replay fixtures
from their source inputs and verifies the resulting bytes match
the committed deterministic hashes.

## 1. The CLI

```
python tools/hydrate_replay_artifacts.py             # rebuild + write
python tools/hydrate_replay_artifacts.py --check-only # verify only
```

Inputs (read-only):

- `spatial-replay/registry/canonical-artifacts.json`
- `spatial-replay/fixtures/<run_id>/pose-samples.jsonl`
- `mission-rehearsals/audits/<mission_id>/rehearsal-events.json`

Outputs:

- `spatial-replay/runs/<run_id>/spatial-replay.json` (and the four
  sibling files)
- `spatial-replay/registry/hydration-report.json`
- `spatial-replay/registry/hydration-report.md`
- `spatial-replay/registry/canonical-artifacts.md`

The CLI is deterministic: two consecutive runs against the same
inputs produce byte-identical outputs (the canonical fixtures pin
`generated_at_utc` so timestamps don't drift).

## 2. The hydration loop

```
load registry
for each record in registry.records:
    extract pose samples
    build spatial-replay artifact
    validate the artifact
    write the artifact bytes
    verify the bytes match the registry's expected_hash
emit hydration report
if overall integrity passed:
    refresh registry.generated_at_utc
else:
    leave the registry untouched (honest failure)
```

The "leave the registry untouched on failure" rule is the
honesty backstop: an operator investigating a drift can trust
that the registry on disk reflects the last successful run.

## 3. The CI gates

Two workflows enforce hydration:

1. `.github/workflows/replay-hydration.yml` — dedicated job that
   runs the CLI in check-only mode against every relevant path.
2. `.github/workflows/mission-control-ci.yml` — runs hydration as
   the first stage before installing npm dependencies; the build
   fails immediately if hydration drifts.

Both jobs run:

```bash
python tools/hydrate_replay_artifacts.py --check-only
git diff --quiet -- spatial-replay/runs
```

Any working-tree drift after hydration fails the build with a
GitHub Actions error annotation pointing at the diff.

## 4. Producing a new bag-backed run

For a real bag-backed run (eventual Phase 17D / 19):

1. Record the bag on a qualified self-hosted Jazzy + Gazebo runner.
2. Post-process the bag into
   `evidence/runtime/<run_id>/pose-samples.jsonl`.
3. Run `python tools/generate_spatial_replay.py …` to emit the
   `spatial-replay/runs/<run_id>/` directory.
4. Append a new record to
   `spatial-replay/registry/canonical-artifacts.json` (the helpers
   in `backend/app/artifact_registry/registry.py::discover_run_files`
   compute the file list + sha256 hashes for you).
5. Run `python tools/hydrate_replay_artifacts.py --check-only` to
   verify the new record validates.
6. Commit the registry + runs/ + report.

The frontend will surface the new run automatically.

## 5. Honesty invariants enforced here

- A failing hydration NEVER rewrites the registry.
- A drift between expected and computed hashes is reported as a
  per-file `hash mismatch` and downgrades integrity to `failed`.
- A missing committed file downgrades integrity to `missing`.
- The hydration CLI never invents pose samples or fabricates bag
  manifests.

## 6. Related docs

- `docs/ARTIFACT_GOVERNANCE_MODEL.md`
- `docs/SPATIAL_REPLAY_HONESTY_RULES.md`
- `docs/BAG_TO_TRAJECTORY_PIPELINE.md`
- `docs/ARTIFACT_STABILIZATION_PASS.md`

## 7. Phase 20B — `--check-only` is a true no-op

The CLI flag `--check-only` was previously implemented as
"skip the registry timestamp rewrite". It still wrote
spatial-replay output bytes and rewrote report files, leaving a
dirty working tree.

Phase 20B changes the contract:

* `tools/hydrate_replay_artifacts.py --check-only` is read-only.
  It computes hashes for the committed bytes, compares them to the
  registry, and exits non-zero on drift. Nothing is written.
* `--write-reports` is a separate opt-in flag that re-enables
  report generation alongside `--check-only` (rare).
* The default (no `--check-only`) rebuilds artifacts AND writes
  the registry + reports, as before.

`backend/tests/test_hydration_noop.py` enforces the no-op rule by
hashing the registry + canonical-fixture files before and after a
`--check-only` invocation.
