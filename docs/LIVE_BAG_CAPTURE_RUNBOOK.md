# Live Bag Capture Runbook

The platform is **not safety-certified**. This runbook walks an
operator through executing a Phase 13 live bag capture on a
self-hosted Jazzy + Gazebo runner.

## 1. Prerequisites

* A self-hosted GitHub Actions runner labelled
  `[self-hosted, ros-jazzy, gazebo]`.
* ROS 2 Jazzy installed (`source /opt/ros/jazzy/setup.bash`).
* Gazebo Harmonic installed.
* `colcon`, `rosbag2`, and the project workspace built under
  `rover_ws/install/`.
* A populated `live-runtime/runner-profile.json`. The shipped file
  is a *template* — `qualification_status: unknown` and
  `supports_gazebo: false / supports_rosbag2: false`. A real
  runner overwrites this file with its own values.

## 2. Quick check before launching

```bash
python rover_ws/tools/qualify_ros_host.py --json
echo "ROS_DISTRO=${ROS_DISTRO:-unset}"
ros2 doctor --report || true
ros2 bag --help > /dev/null && echo "rosbag2 OK"
```

If any of those fail, do not run the capture — the capture script
will write a `not_executed` bundle and exit cleanly, but the
operator should fix the host first.

## 3. Run a live capture

```bash
python rover_ws/tools/live_bag_capture.py \
    --plan live-runtime/scenario-plans/core-live-qualification.yaml \
    --evidence-root evidence/runtime \
    --run-id live-$(date -u +%Y%m%dT%H%M%SZ) \
    --runner-profile live-runtime/runner-profile.json
```

Optional flags:

* `--scenario nominal_runtime_launch` (repeatable) to run a subset.
* `--dry-run` to force a `not_executed` bundle (useful in CI).
* `--reason "<text>"` to record an extra blocker reason.
* `--json` to emit a machine-readable summary.

## 4. What gets written

```
evidence/runtime/<run_id>/
  metadata.json
  runner-profile.json
  live-run-summary.json
  bag-manifest.json
  bags/
  logs/
  events.jsonl
  qualification-summary.md
  known-limitations.md
```

If the host could not execute live, every file is still written;
`live-run-summary.json` carries `status=not_executed` and
`bag-manifest.json` carries `bag_status=not_executed` with a
`not_executed_reason`.

## 5. Validate the evidence

```bash
python rover_ws/tools/validate_live_runtime_evidence.py \
    --bundle evidence/runtime/<run_id> --json
```

The validator fails if:

* any required file is missing,
* the bag manifest lies about being `bag_backed`,
* a `not_executed` manifest has no reason,
* the bag inventory is missing required topics for the scenario.

## 6. Feed the bundle into downstream pipelines

```bash
python rover_ws/tools/process_live_runtime_evidence.py \
    --bundle evidence/runtime/<run_id> \
    --json
```

By default this is a **dry-run** that lists which downstream
integrations the bundle qualifies for, with the reason. Use
`--apply` to actually invoke the underlying generators
(`reconstruct_incident.py`, `build_replay_review_bundle.py`,
`generate_replay_analytics.py`, `generate_programme_review.py`,
`generate_reviewer_export.py`). The orchestrator preserves
`bag_status` verbatim — it never upgrades.

## 7. Refresh the maturity report

```bash
python rover_ws/tools/generate_live_runtime_maturity_report.py \
    --reference-time $(date -u +%Y-%m-%dT%H:%M:%SZ)
```

Outputs:

* `live-runtime/live-runtime-maturity.json`
* `docs/LIVE_RUNTIME_MATURITY_REPORT.md`

## 8. Honest fall-backs

This runbook never asks the operator to fabricate evidence.
The acceptable outcomes are:

* `status=passed` with `bag_status=bag_backed` (real live run),
* `status=partial` with `bag_status=partial` (some required topics
  absent),
* `status=failed` (the run executed but a check failed),
* `status=skipped` (the operator skipped on purpose),
* `status=not_executed` (live execution did not happen at all).

There is no path to `bag_backed` that does not produce real bag
files on disk.

## 9. Related documents

- [`LIVE_RUNTIME_EVIDENCE_PIPELINE.md`](LIVE_RUNTIME_EVIDENCE_PIPELINE.md)
- [`LIVE_RUNNER_PROFILE.md`](LIVE_RUNNER_PROFILE.md)
- [`LIVE_RUNTIME_MATURITY_REPORT.md`](LIVE_RUNTIME_MATURITY_REPORT.md)
- [`RUNTIME_QUALIFICATION_RUNBOOK.md`](RUNTIME_QUALIFICATION_RUNBOOK.md)
- [`REPLAY_REVIEW_RUNBOOK.md`](REPLAY_REVIEW_RUNBOOK.md)
