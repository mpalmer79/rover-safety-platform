# Bag → trajectory pipeline (Phase 17C)

The platform is **not safety-certified.** This document describes
how a real bag-backed run on a qualified self-hosted Jazzy + Gazebo
runner becomes a `derivation_source = bag_backed` artifact that the
Mission Control UI can render.

## 1. Pipeline overview

```
┌──────────────────────────────────────────────┐
│  Self-hosted runner (Jazzy + Gazebo)         │
│  ┌────────────────────────────────────────┐  │
│  │ ros2 launch ...                         │  │
│  │ ros2 bag record /odom /tf /tf_static ...│  │
│  └────────────────┬───────────────────────┘  │
└───────────────────┼──────────────────────────┘
                    │ produces
                    ▼
         evidence/runtime/<run_id>/
            ├── bag-manifest.json
            ├── bags/run.mcap (or .db3)
            ├── bags/metadata.yaml
            └── pose-samples.jsonl   ← operator post-process
                    │
                    ▼
┌──────────────────────────────────────────────┐
│  tools/generate_spatial_replay.py            │
│  ├── load_run_manifest                       │
│  ├── extract_pose_samples (runtime + fixture) │
│  ├── evaluate_bag_eligibility                │
│  ├── build_segments                          │
│  ├── classify_trajectory                     │
│  ├── align_events                            │
│  ├── validate_spatial_replay                 │
│  └── write_spatial_replay_artifacts          │
└────────────────┬─────────────────────────────┘
                 │ writes
                 ▼
         spatial-replay/runs/<run_id>/
            ├── spatial-replay.json
            ├── trajectory.jsonl
            ├── event-alignment.json
            ├── spatial-validation.json
            └── spatial-replay-report.md
                 │
                 ▼
┌──────────────────────────────────────────────┐
│  apps/mission-control/                       │
│  ├── loader.ts::loadSpatialReplay            │
│  └── spatial.ts::selectMissionRoute          │
└──────────────────────────────────────────────┘
```

## 2. Step-by-step

### Step 1 — Record the bag

On a qualified self-hosted runner (Phase 13):

```bash
ros2 bag record \
    -o bags \
    -s mcap \
    /odom /tf /tf_static \
    /mission/events /safety/events /system/health
```

The runner is responsible for producing the `bag-manifest.json`
(Phase 13 already does this). The bag itself is **not** committed
to the repo — only the manifest and the derived
`pose-samples.jsonl` are.

### Step 2 — Post-process to `pose-samples.jsonl`

The operator post-processes the bag (with `mcap`, `rosbag2_py`, or
their own tooling) into the JSONL format defined in
`docs/SPATIAL_REPLAY_ARTIFACT_FORMAT.md`. The platform never does
this step itself; the dependency cost is real and the operator has
the trust boundary.

The output is committed to
`evidence/runtime/<run_id>/pose-samples.jsonl`.

### Step 3 — Run the CLI

```
python tools/generate_spatial_replay.py \
    --run-id <run_id> \
    --scenario-id <scenario_id> \
    --mission-id <mission_id> \
    --rehearsal mission-rehearsals/audits/<mission_id> \
    --evidence-root evidence \
    --fixtures-root spatial-replay/fixtures \
    --output-root spatial-replay/runs \
    --expected-topic /odom \
    --expected-topic /tf
```

The CLI:

1. Loads the rehearsal events.
2. Loads the bag manifest (if any).
3. Extracts pose samples (runtime path first, fixture fallback).
4. Evaluates bag-backed eligibility.
5. Builds segments + classifies the trajectory.
6. Aligns events to the nearest pose sample.
7. Validates the artifact.
8. Writes the five output files.

### Step 4 — Commit + open a PR

The frontend picks up the artifact automatically (no rebuild
required at this step, except the static export must re-prerender).

## 3. Determinism guarantees

* The trajectory builder sorts samples by `(time_ns, sample_id)`
  before computing segments; identical inputs produce identical
  output bytes.
* The event aligner is a simple nearest-neighbour over the sorted
  sample list; ties are broken by the first sample seen, which is
  deterministic given the sort.
* The JSON writer uses `sort_keys=True`; the JSONL writer sorts
  samples by time.

## 4. Honesty backstops

Every step above can fail. Phase 17C's honesty rules ensure that a
failure mode never produces a fake bag-backed artifact:

* Missing `bag-manifest.json` → `derivation_source = fixture` (if
  fixture exists) or `unavailable`.
* Missing bag file on disk → `derivation_source ≠ bag_backed`.
* Missing `pose-samples.jsonl` → `derivation_source = fixture` (if
  fixture exists) or `unavailable`.
* Invalid `validation_status` on the manifest →
  `derivation_source ≠ bag_backed`.

See `docs/SPATIAL_REPLAY_HONESTY_RULES.md` for the complete rule
set.

## 5. What this pipeline does NOT do

* It does not parse `.mcap` / `.db3` files; the operator does that.
* It does not stream telemetry; spatial-replay is a snapshot.
* It does not publish to ROS topics.
* It does not call cloud APIs or download anything.
* It does not bypass the safety supervisor or motion arbitration.
