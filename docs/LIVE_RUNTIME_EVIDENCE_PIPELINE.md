# Live Runtime Evidence Pipeline

This document describes the Phase 14 end-to-end live runtime
evidence pipeline. The pipeline takes a self-hosted ROS 2 Jazzy +
Gazebo Harmonic host from "workspace builds" to
"`evidence/runtime/<run_id>/` populated with honest artefacts" in a
single command.

The platform is **not safety-certified.** This document describes
engineering qualification discipline.

## 1. One-command entry point

```
python3 rover_ws/tools/run_live_runtime_pipeline.py \
  --scenario-plan live-runtime/scenario-plans/smoke-live-runtime.yaml \
  --runner-profile live-runtime/runner-profile.local.json \
  --output evidence/runtime/<run_id> \
  [--dry-run | --static-check-only] \
  [--capture-bag] \
  [--promote-baseline] \
  [--json]
```

The pipeline drives:

1. scenario plan validation
2. runner profile validation
3. (optional) inline `live_bag_capture.py` — `--capture-bag`
4. construction of the canonical `LiveRuntimeEvidence` record
5. `evidence.json`, `evidence.md`, and `bag-manifest.json` writes
6. (optional) maturity baseline promotion — `--promote-baseline`

`--dry-run` and `--static-check-only` short-circuit the live steps
and produce a `not_executed` evidence record. The pipeline never
fabricates a bag in those modes.

## 2. Output layout

```
evidence/runtime/<run_id>/
  evidence.json              canonical machine-readable record
  evidence.md                human-readable summary
  bag-manifest.json          bag classification (status + chunks + topics)
  bag/                       rosbag2 directory (only when bag was captured)
    metadata.yaml
    *.mcap or *.db3
  logs/
    pipeline.log
    bag-capture.log
    validate.log
    host-qualification.log
    colcon-build.log
```

## 3. Bag-backed evidence contract

A run is `mode: bag_backed` only when **all** of these hold:

1. the runner profile is at least `runner_status: provisional`;
2. the bag directory exists on disk;
3. `metadata.yaml` exists inside the bag directory;
4. at least one `.mcap` or `.db3` chunk exists and is non-empty;
5. all required topics from the scenario plan are present in the
   bag's topic inventory (when the inventory is readable).

Any weaker shape produces:

| Disk shape                                  | Bag manifest status | Evidence mode             | Evidence status   |
|---------------------------------------------|---------------------|---------------------------|-------------------|
| no bag dir / dir absent                     | `missing_bag`       | `live_runtime_no_bag`     | `partial`         |
| metadata only                               | `partial`           | `live_runtime_no_bag`     | `partial`         |
| chunk(s) only, no metadata                  | `partial`           | `live_runtime_no_bag`     | `partial`         |
| metadata + zero-byte chunks                 | `partial`           | `live_runtime_no_bag`     | `partial`         |
| metadata + non-empty chunks, missing topics | `bag_backed`*       | `live_runtime_no_bag`     | `partial`         |
| metadata + non-empty chunks, all topics     | `bag_backed`        | `bag_backed`              | `passed`          |
| `--dry-run`                                 | `not_executed`      | `dry_run`                 | `not_executed`    |
| `--static-check-only`                       | `not_executed`      | `static_only`             | `not_executed`    |
| no runner profile                           | _per disk_          | `not_executed`            | `not_executed`    |
| runner profile `unqualified`                | _per disk_          | `not_executed`            | `not_executed`    |

\* The bag manifest is `bag_backed` based on disk shape, but the
evidence record is downgraded to `live_runtime_no_bag` /
`partial` until the topic inventory matches the scenario plan.

The classifier and processor live in `backend/app/live_runtime/` and
are unit-tested. The `validate_live_runtime_evidence.py` tool runs
the same logic and re-classifies the on-disk bag against the
recorded manifest, so a tampered evidence file is detected.

## 4. CI vs self-hosted lanes

| Lane                       | Runner               | Modes used                               | Outcome                     |
|----------------------------|----------------------|------------------------------------------|-----------------------------|
| `runtime-static-validation`| GitHub-hosted        | `--static-check-only`                    | `not_executed`              |
| `live-runtime-evidence`    | self-hosted Jazzy    | live, optional `--capture-bag`           | `passed` / `partial`        |
| operator local on runner   | self-hosted Jazzy    | live, optional `--dry-run` for rehearsal | `passed` / `partial`        |

CI only runs the GitHub-hosted lane today. The Phase 14 honesty
guardrails ensure CI cannot accidentally claim live evidence.

## 5. Maturity baseline

`live-runtime/baselines/maturity-baseline.template.json` is the
honest committed baseline. The pipeline only updates the
`maturity-baseline.json` (gitignored, optional) when:

* `--promote-baseline` is supplied, **and**
* the resulting `LiveRuntimeEvidence` is `mode: bag_backed`.

Any weaker outcome leaves the baseline unchanged. Reviewers should
treat `status: not_established` as the authoritative answer to "has
this project ever produced bag-backed live evidence?" until a real
self-hosted run flips it.

## 6. Replay and analytics integration

The bag artefacts produced by this pipeline are the input to
`docs/REPLAY_REVIEW_RUNBOOK.md` and `docs/REPLAY_ANALYTICS.md`.
Those flows already accept bag directories and require no further
changes for Phase 14. The pipeline does not yet auto-invoke them; do
so manually with the bag path emitted in `evidence.json` after
verifying the run is `mode: bag_backed`.

## 7. Known limitations

* The pipeline does not simulate a bag — `--capture-bag` requires
  `ros2` on PATH or it short-circuits to `not_executed`.
* The classifier reads `metadata.yaml` for the topic inventory but
  does not run `ros2 bag info` to validate message schemas. A bag
  with a corrupt MCAP chunk would still classify as `bag_backed`
  on disk; replay-review would catch it.
* No live execution has occurred against this branch at the time
  this document was written. The committed baseline therefore
  remains `not_established`.
