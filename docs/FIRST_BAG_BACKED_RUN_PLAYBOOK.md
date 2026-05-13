# First Bag-Backed Run Playbook (Phase 19)

The platform is **not safety-certified.** This playbook is the
exact operator workflow for producing the FIRST real bag-backed
spatial-replay artifact + reviewer scene snapshot.

The platform is intentionally honest about what it ships today:
**no real bag-backed run exists yet.** Every committed
`spatial-replay/runs/<id>/spatial-replay.json` has
`derivation_source = "fixture"`. The Phase 19 layer makes the
on-ramp for the first real run obvious.

## 1. Prerequisites

- A qualified self-hosted Jazzy + Gazebo runner (Phase 13).
- A committed runner profile under `live-runtime/`.
- A scenario plan entry that references the run.
- The Phase 18 artifact-registry / hydration CLI installed.

## 2. Record the bag

On the self-hosted runner:

```bash
ros2 bag record \
    -o bags \
    -s mcap \
    /odom /tf /tf_static \
    /mission/events /safety/events /system/health
```

Phase 13 produces `evidence/runtime/<run_id>/bag-manifest.json`
alongside the bag bytes. **Bag bytes are not committed to the
repo.**

## 3. Post-process to `pose-samples.jsonl`

The operator post-processes the bag with their own tooling (e.g.
`mcap` Python library or `rosbag2_py`) into a JSONL stream of pose
samples — see `docs/SPATIAL_REPLAY_ARTIFACT_FORMAT.md`.

Commit the resulting file to
`evidence/runtime/<run_id>/pose-samples.jsonl`.

## 4. Generate the spatial-replay artifact

```bash
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

The CLI emits the five files under
`spatial-replay/runs/<run_id>/`. The artifact's
`derivation_source` will be `bag_backed` if the bag manifest
validates and pose samples are present.

## 5. Register the run

Append a new record to
`spatial-replay/registry/canonical-artifacts.json` (helper:
`backend/app/artifact_registry/registry.py::discover_run_files`
computes the file list + sha256 hashes for you):

```python
from pathlib import Path
from app.artifact_registry import (
    ArtifactFile, ArtifactRecord, hash_file,
    load_registry, write_registry, default_registry_path,
)

repo = Path(".")
run_dir = repo / "spatial-replay" / "runs" / "<run_id>"
files = []
for p in sorted(run_dir.rglob("*")):
    if p.is_file() and not p.name.startswith("."):
        files.append(ArtifactFile(
            relative_path=str(p.relative_to(repo)),
            expected_hash=hash_file(p),
            size_bytes=p.stat().st_size,
            description="",
        ))
# ... build ArtifactRecord, append to registry, write_registry().
```

## 6. Verify hydration

```bash
python tools/hydrate_replay_artifacts.py --check-only
```

This must report `overall_integrity = passed` and produce no
working-tree drift.

## 7. Generate the reviewer snapshot metadata

```bash
python tools/generate_reviewer_scene_snapshot.py --run-id <run_id>
```

When the artifact is honestly bag-backed, the CLI prints
`status=bag_backed` and `reviewer_export_ready=True`, and writes
`spatial-replay/snapshots/<run_id>.scene-snapshot.{json,md}`.

## 8. Commit + open a PR

The frontend will auto-detect the new run, render the bag-backed
trajectory in the immersive scene, mark the lifecycle ladder as
`canonical`, and turn the reviewer scene-snapshot panel green.

## 9. Honesty rules

- The CLI never invents pose samples — the operator produces the
  JSONL.
- The registry update is a manual operator step; nothing in CI
  auto-promotes a run to `canonical`.
- The reviewer scene-snapshot panel never claims a snapshot
  exists unless the artifact registry + spatial-replay +
  bag-status all align.
- This playbook is a *plan* — the platform does NOT yet contain
  a real bag-backed run.

## 10. Related docs

- `docs/BAG_TO_TRAJECTORY_PIPELINE.md`
- `docs/SPATIAL_REPLAY_ARTIFACT_FORMAT.md`
- `docs/REVIEWER_SCENE_SNAPSHOT_GUIDE.md`
- `docs/DETERMINISTIC_REPLAY_HYDRATION.md`
