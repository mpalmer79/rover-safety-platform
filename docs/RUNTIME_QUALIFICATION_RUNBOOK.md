# Runtime Qualification Runbook

This runbook is the operational guide for the Phase 5 ROS host
qualification + qualified-runtime-run flow. It documents how to take
the platform from "the workspace builds" to "a qualified runtime run
with evidence." The platform is **not** safety-certified; this
runbook describes engineering qualification discipline and nothing
more.

The qualified path is:

```
host_qualification
    -> live_runtime_validator (Phase 4 probes)
    -> qualification scenarios
    -> regression detection
    -> baseline comparison (optional)
    -> qualification report
    -> evidence index update
```

## 1. Host prerequisites

Live qualification requires:

| Component | Required version | Notes |
| --- | --- | --- |
| Ubuntu | 24.04 LTS (Noble) | host OS |
| ROS 2 Jazzy | full desktop install | rclpy + ros2 CLI + tf2 + ros_gz_bridge |
| Gazebo Harmonic | matching Jazzy | `gz` CLI on PATH |
| Python | 3.12 | matches the workspace's pinned interpreter |
| colcon | 2.x | builds `rover_ws/` |
| Required ROS packages | rclpy, ros_gz_bridge, robot_state_publisher, tf2_ros | resolved via `ros2 pkg list` |

The static-only path needs only Python 3.10+; that is what GitHub-hosted CI runs.

Run the host qualifier first:

```bash
python3 rover_ws/tools/qualify_ros_host.py \
  --evidence-root evidence/host \
  --run-id "host-$(date -u +%Y%m%dT%H%M%SZ)"
```

The qualifier writes `host-qualification.json` and
`host-qualification.md` to the run directory. Each check returns one
of `passed`, `failed`, `partial`, `skipped`, `not_executed`. CI runs
without ROS and reports the ROS / Gazebo checks as `not_executed`
with a reason.

## 2. Workspace setup

```bash
source /opt/ros/jazzy/setup.bash
cd rover_ws
colcon build --symlink-install
source install/setup.bash
cd ..
```

If `colcon build` fails, fix it before proceeding; the qualifier
flags an unbuilt workspace as `partial` (not `passed`).

## 3. Run a qualified runtime

The orchestrator is `rover_ws/tools/qualified_runtime_run.py`. It
takes care of:

* host qualification,
* the Phase-4 probe orchestrator,
* qualification scenario evaluation,
* regression detection,
* (optional) baseline comparison,
* per-run report rendering,
* the evidence index.

### 3.1 Static-only (CI / non-Jazzy host)

```bash
python3 rover_ws/tools/qualified_runtime_run.py \
  --static-only \
  --evidence-root evidence/runtime \
  --run-id "qualified-$(date -u +%Y%m%dT%H%M%SZ)" \
  --canonical-report
```

Live-runtime checks surface as `not_executed` with the reason
"`rclpy not importable: No module named 'rclpy'`" (or similar). They
are never reported as `passed`. The orchestrator returns non-zero
when any check is `failed`; `not_executed` does not fail CI.

### 3.2 Live (Jazzy host)

```bash
python3 rover_ws/tools/qualified_runtime_run.py \
  --ros-launch \
  --evidence-root evidence/runtime \
  --run-id "qualified-$(date -u +%Y%m%dT%H%M%SZ)" \
  --canonical-report
```

The orchestrator launches `rover_bringup full_system.launch.py`
(headless), sleeps for the configured settle period, runs every
Phase-4 probe live, evaluates each qualification scenario, and
shuts down cleanly.

### 3.3 Specific scenarios only

```bash
python3 rover_ws/tools/qualified_runtime_run.py \
  --static-only \
  --scenario nominal_runtime_launch \
  --scenario authorized_motion_path
```

## 4. Qualification scenarios

Scenarios live under `qualification/scenarios/*.yaml`. Each pins:

* required topics + nodes + safety state;
* required + forbidden events;
* required replay artifacts;
* qualification rules (e.g. `command_path_invariants`,
  `zero_motion_in_safe_stop`, `replay_integrity`);
* expected outcome (`passed`, `failed`, `partial`).

Adding a scenario:

1. Drop a YAML under `qualification/scenarios/`.
2. The qualification orchestrator validates the schema during load;
   malformed YAML appears as a `failed` check in the report.
3. Re-run the orchestrator; the scenario contributes a new
   `qualification-scenario-<id>.json` artifact and a row in the
   summary.

## 5. Baselines and regression detection

### 5.1 Capture a baseline

```bash
python3 rover_ws/tools/compare_runtime_baseline.py capture \
  evidence/runtime/<known-good-run-id>/ \
  --baseline-out qualification/baselines/<name>.json
```

Commit the resulting baseline JSON. It becomes the ground truth for
later runs.

### 5.2 Compare a run

```bash
python3 rover_ws/tools/compare_runtime_baseline.py compare \
  evidence/runtime/<run-id>/ \
  --baseline qualification/baselines/<name>.json \
  --required-topics /scan,/imu,/cmd_vel_authorized
```

The comparator classifies each delta as
`expected_difference`, `warning`, `regression`, or `critical_regression`.
The orchestrator runs the comparison automatically when
`--baseline` is supplied.

### 5.3 Regression detection without a baseline

`regression-report.json` is produced on every run. It catches
missing topics / nodes / frames, stale topics, command-path
violations, and missing replay artifacts. In static-only mode the
orchestrator suppresses live-only requirements so CI does not flag
them.

## 6. Evidence layout

Per qualified run (`evidence/runtime/<run_id>/`):

| File | Purpose |
| --- | --- |
| `host-qualification.json` / `.md` | Host qualifier output |
| `runtime-validation.json` / `.md` | Phase-4 orchestrator output |
| `topic-snapshot.json` | Topic probe |
| `node-snapshot.json` | Launch smoke / node graph |
| `tf-snapshot.json` / `tf-tree.txt` | TF probe |
| `command-path-audit.json` | Command-path probe |
| `qualification-scenario-<id>.json` | Per-scenario evaluation |
| `qualification-summary.json` / `.md` | Aggregate qualification report |
| `live-runtime-status.md` | Static vs live origin labelling |
| `regression-report.json` / `.md` | Regression detector output |
| `baseline-comparison.json` / `.md` | Baseline diff (when supplied) |
| `known-limitations.md` | Standalone known-limitations callout |

Per-run navigation: `docs/EVIDENCE_INDEX.md` lists every retained run
in chronological order.

## 7. Interpreting a report

`qualification-summary.md` reports:

* **host qualification** — Ubuntu / ROS / Gazebo / colcon / packages /
  workspace structure;
* **runtime validation** — Phase-4 probe aggregate;
* **qualification checks** — origin-labelled (`static-source`,
  `static-workspace`, `live-runtime`);
* **scenarios** — per-scenario expected vs observed;
* **regression detection** — finding-level severity;
* **baseline comparison** — when a baseline was supplied;
* **known limitations** — verbatim, every run.

`live-runtime-status.md` is a short-form view that **labels every
check by origin**. Reviewers should never confuse a
`static-workspace` pass for a `live-runtime` pass; the orchestrator
makes the difference visible by construction.

## 8. CI discipline

Four GitHub workflows ship under `.github/workflows/`:

| Workflow | Trigger | What it runs |
| --- | --- | --- |
| `backend-tests.yml` | push, PR | `pytest backend/tests` + `pytest rover_ws/tests` |
| `runtime-static-validation.yml` | push, PR | `live_runtime_validator.py` + `qualified_runtime_run.py`, both `--static-only` |
| `docs-traceability.yml` | push, PR | regenerate the matrix and verification report; fail if drift |
| `evidence-validation.yml` | push, PR | regenerate per-scenario evidence and validate the manifest |
| `ros-jazzy-runtime.yml` | manual / self-hosted | live qualification on a Jazzy + Gazebo runner |

The `ros-jazzy-runtime.yml` workflow is intentionally manual. github-hosted
runners cannot drive Gazebo Harmonic reliably; live qualification
requires a self-hosted runner labelled `ros-jazzy`. Do not enable it
on github-hosted runners; the result would be misleading.

## 9. Common failures

| Symptom | Likely cause | Resolution |
| --- | --- | --- |
| `host_qualification` reports `partial` | rover_ws/install missing | run `colcon build --symlink-install` |
| `ros2_distro` `not_executed` | `/opt/ros/jazzy/setup.bash` not sourced | source ROS, re-run |
| `gazebo_harmonic` `not_executed` | Gazebo not on PATH | install Gazebo Harmonic for Jazzy |
| `topic_probe` stale freshness | launch hasn't reached steady state | bump `--settle-seconds` on the underlying probe |
| `command_path_probe` flags foreign publisher | non-supervisor source publishes `/cmd_vel_authorized` | architectural violation; fix the offending node |
| Baseline comparator reports `critical_regression` | required topic / node missing | inspect `topic-snapshot.json` and `node-snapshot.json` |
| `regression-report` has `replay_integrity_missing` | live probe wasn't run | use `--ros-launch` on a Jazzy host |

## 10. Gazebo troubleshooting

| Symptom | Likely cause | Resolution |
| --- | --- | --- |
| `gz sim` exits 1 immediately | missing display / GPU | run with `headless:=true` or set `GZ_GUI=0` |
| Simulation runs but ros_gz_bridge can't see topics | bridge YAML drift | inspect `rover_ws/src/rover_sim_gazebo/config/ros_gz_bridge.yaml` |
| `/clock` not advertised | bridge not started or simulation not running | check `gz topic -l` and bring up sim before bridge |

## 11. Replay troubleshooting

| Symptom | Likely cause | Resolution |
| --- | --- | --- |
| `replay-integrity.json` reports `failed` | event ordering broken | inspect `runs/<run_id>/events.jsonl` for non-monotonic sim_time_ns |
| `commands.jsonl` empty | recorder not subscribed | confirm `rover_event_recorder` is running |
| Replay markers missing | observability launch not included | confirm `full_system.launch.py` includes `rover_observability` |

## 12. Bridge troubleshooting

| Symptom | Likely cause | Resolution |
| --- | --- | --- |
| `/cmd_vel_authorized` not bridged ROS → Gazebo | bridge YAML missing entry | re-add ros_gz_bridge entry |
| `/cmd_vel` appears in topic list | architectural violation | fix the offending node; never bridge `/cmd_vel` directly |
| Bridge process crashes | typed message mismatch | inspect bridge YAML types vs ROS / Gazebo definitions |

## 13. Related documents

* [docs/RUNTIME_VALIDATION_RUNBOOK.md](RUNTIME_VALIDATION_RUNBOOK.md) — Phase-4 probe-level runbook.
* [docs/EVIDENCE_INDEX.md](EVIDENCE_INDEX.md) — generated index of retained runs.
* [docs/RUNTIME_QUALIFICATION_REPORT.md](RUNTIME_QUALIFICATION_REPORT.md) — the most recent canonical qualification report.
* [docs/LIVE_RUNTIME_STATUS.md](LIVE_RUNTIME_STATUS.md) — static-vs-live status page.
* [docs/VERIFICATION_STRATEGY.md](VERIFICATION_STRATEGY.md) — how the qualification layer fits into Phase 3 / Phase 4.

This runbook does not claim safety certification. It documents the
operations that produce honest, repeatable engineering qualification
evidence for a ROS 2 Jazzy + Gazebo Harmonic stack.
