# Artifact Stabilization Pass

> Phase 20B committed canonical replay fixture bytes, made
> hydration `--check-only` a true no-op, and stopped pytest from
> dirtying the working tree.

## Why

Three pre-existing weaknesses blocked clean CI:

1. The canonical fixture artifacts (`spatial-replay/runs/canonical-fixture/*`)
   were gitignored under the global `runs/` rule. A fresh clone did
   not carry the bytes, so `test_canonical_registry_paths_match_disk`
   failed unless hydration was run locally first.
2. `tools/hydrate_replay_artifacts.py --check-only` rewrote the
   registry's `generated_at_utc` and the hydration report files.
   Running it locally always produced a dirty working tree.
3. `rover_ws/tests/test_runtime_qualification.py::test_qualified_runtime_run_writes_full_evidence_dir`
   ran `qualified_runtime_run` against the real repo, which wrote
   `docs/EVIDENCE_INDEX.md` with tempdir paths and dirtied the
   working tree.

## What changed

### Canonical fixture commitment

* `.gitignore` now includes an exception:
  `!spatial-replay/runs/canonical-fixture/**`
* The five canonical-fixture run files are committed:
  - `spatial-replay.json`
  - `trajectory.jsonl`
  - `event-alignment.json`
  - `spatial-validation.json`
  - `spatial-replay-report.md`
* `backend/tests/test_artifact_fixture_commitment.py` asserts:
  - every registered file exists on disk;
  - every file's sha256 matches the registry hash;
  - the gitignore exception is in place.

### Hydration check-only is a true no-op

* `backend/app/artifact_registry/hydration.py::hydrate_registry`
  accepts a new `check_only: bool` parameter.
  In `check_only=True` mode the function:
  - does NOT rebuild artifacts;
  - does NOT write spatial-replay outputs;
  - does NOT rewrite the registry's `generated_at_utc`;
  - reads committed bytes and compares against expected hashes.
* `tools/hydrate_replay_artifacts.py` exposes `--check-only` as the
  read-only path and adds a separate `--write-reports` opt-in for
  the rare case where the report files must be regenerated.
* `backend/tests/test_hydration_noop.py` asserts the registry
  files + canonical-fixture bytes are unchanged after a
  `--check-only` invocation.

### Test side-effect cleanup

* `rover_ws/tools/qualified_runtime_run.py` now accepts
  `--evidence-index-md <path>` so callers can redirect the
  Markdown output.
* `rover_ws/tests/test_runtime_qualification.py` passes a `tmp_path`
  for the evidence-index Markdown so pytest never touches
  `docs/EVIDENCE_INDEX.md`.

## Result

After the pass:

* a fresh clone passes `python -m pytest backend/tests/`
  without running hydration first;
* `python tools/hydrate_replay_artifacts.py --check-only` leaves
  the working tree clean;
* the full backend + rover_ws + frontend test suites no longer
  modify committed files.
