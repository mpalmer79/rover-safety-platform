# Live Bag Capture Runbook

This runbook is the operational guide for capturing a real rosbag2
bag on a self-hosted ROS 2 Jazzy + Gazebo Harmonic runner. Pairs
with `docs/LIVE_RUNTIME_EVIDENCE_PIPELINE.md` and
`docs/SELF_HOSTED_JAZZY_RUNNER_SETUP.md`.

The platform is **not safety-certified.** This runbook describes
engineering qualification discipline and nothing more.

## 1. Prerequisites

* the runner is set up per
  `docs/SELF_HOSTED_JAZZY_RUNNER_SETUP.md`;
* `live-runtime/runner-profile.local.json` exists on the runner with
  `runner_status` ≥ `provisional`;
* `rover_ws` builds cleanly: `cd rover_ws && colcon build --symlink-install`;
* the scenario plan you intend to capture is valid.

## 2. Choose a scenario plan

| Plan ID                  | Duration | Purpose                                           |
|--------------------------|---------:|---------------------------------------------------|
| `smoke-live-runtime`     | 30 s     | first real bring-up; required-topic smoke test    |
| `core-live-qualification`| 300 s    | exercises supervisor + diagnostics; longer bag    |

Pick `smoke-live-runtime` for the first run. Move to
`core-live-qualification` only after the smoke run has produced a
`bag_backed` evidence record.

## 3. Bring up the stack

In one terminal:

```
source /opt/ros/jazzy/setup.bash
source rover_ws/install/setup.bash
ros2 launch rover_bringup full_system.launch.py
```

Wait for `safety/state` to publish `ACTIVE_NORMAL`. If it never
does, the bag will still capture but the evidence will downgrade to
`partial` because the expected safety state was not observed.

## 4. Capture the bag

In a second terminal on the same runner:

```
source /opt/ros/jazzy/setup.bash
source rover_ws/install/setup.bash
python3 rover_ws/tools/live_bag_capture.py \
  --scenario-plan live-runtime/scenario-plans/smoke-live-runtime.yaml \
  --output evidence/runtime/<run_id>/bag \
  --run-id <run_id> \
  --bag-format mcap \
  --json
```

The tool:

1. validates the scenario plan;
2. spawns `ros2 bag record` for every topic listed under
   `bag_topics`;
3. waits `duration_seconds` from the scenario plan;
4. sends `SIGINT` and waits for `ros2 bag record` to flush the
   metadata file;
5. classifies the resulting directory and writes
   `evidence/runtime/<run_id>/bag-manifest.json`.

If `ros2` is not on PATH, the tool exits 0 and writes a
`status: not_executed` manifest. It does NOT fabricate a bag.

## 5. Stop the stack

`Ctrl+C` the launch terminal once the recorder has exited cleanly.
The launch file is responsible for shutting down Gazebo.

## 6. Process the evidence

```
python3 rover_ws/tools/process_live_runtime_evidence.py \
  --runner-profile live-runtime/runner-profile.local.json \
  --scenario-plan live-runtime/scenario-plans/smoke-live-runtime.yaml \
  --bag-dir evidence/runtime/<run_id>/bag \
  --output evidence/runtime/<run_id> \
  --run-id <run_id>
```

Inspect the resulting `evidence.md`. The expected first-run output
is `mode: bag_backed`, `status: passed`. Anything weaker is a real
gap — fix the gap, do not reword the report.

## 7. Validate

```
python3 rover_ws/tools/validate_live_runtime_evidence.py \
  --evidence-dir evidence/runtime/<run_id> \
  --maturity-baseline live-runtime/baselines/maturity-baseline.json
```

The validator re-classifies the on-disk bag and compares it against
the recorded manifest. A mismatch fails the validator with exit
code 1.

## 8. Promote the maturity baseline (optional)

Only after a clean `bag_backed` run that you are willing to commit
to the project's maturity record:

```
python3 rover_ws/tools/run_live_runtime_pipeline.py \
  --runner-profile live-runtime/runner-profile.local.json \
  --output evidence/runtime/<run_id> \
  --run-id <run_id> \
  --promote-baseline
```

The committed `live-runtime/baselines/maturity-baseline.template.json`
remains `not_established`. The promoted
`live-runtime/baselines/maturity-baseline.json` lives next to it but
is gitignored — promote it on the runner, copy it back to a review
PR explicitly when you want to publish maturity.

## 9. Common failure modes

| Symptom                                              | Likely cause                                          | Action                                                       |
|------------------------------------------------------|-------------------------------------------------------|--------------------------------------------------------------|
| `bag-manifest.json` shows `missing_bag`              | `ros2` not on PATH; recorder never started            | Re-source `/opt/ros/jazzy/setup.bash`; rerun                 |
| `bag-manifest.json` shows `partial: metadata only`   | recorder was killed before any chunk flushed          | Increase `duration_seconds`; ensure topics are publishing    |
| `evidence.md` shows `live_runtime_no_bag`/`partial`  | required topics missing from inventory                | Verify launch file publishes them; widen `bag_topics` if so  |
| `validate.log` shows `bag_backed_requires_…` failure | someone hand-edited `evidence.json`                   | Regenerate with `process_live_runtime_evidence.py`           |
| `not_executed` from a "real" run                     | runner profile is `unqualified`                       | Promote runner profile only after a clean dry run            |
