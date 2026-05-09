# Runtime Validation Runbook

This runbook is the developer-facing companion to the Phase 4 live
runtime validation suite. It tells you how to bring the rover stack
up, how to invoke each probe, what evidence each probe writes, and how
to interpret a `runtime-validation.md` report. The platform is **not
safety-certified**; this runbook describes engineering verification
discipline, nothing more.

## 1. Prerequisites

The full live path requires:

| Component | Required version | Purpose |
| --- | --- | --- |
| Ubuntu | 24.04 LTS (Noble) | host OS for ROS 2 Jazzy |
| ROS 2 Jazzy | full desktop install | rclpy, ros2 CLI, tf2 |
| Gazebo Harmonic | matching ROS 2 Jazzy | physics + sensor simulation |
| Python | 3.12 | matches the workspace's pinned interpreter |
| `colcon` | 2.x | builds `rover_ws/` |
| `ros_gz_bridge` | from Jazzy | bridges Gazebo topics to ROS |

The static-only path needs only Python 3.10+; that is what CI runs.

Source the workspace before running the live probes:

```bash
source /opt/ros/jazzy/setup.bash
source rover_ws/install/setup.bash
```

If `source rover_ws/install/setup.bash` fails because the workspace is
not built, run:

```bash
cd rover_ws
colcon build --symlink-install
source install/setup.bash
cd ..
```

## 2. Bring up the stack

The canonical full launch is `rover_bringup full_system.launch.py`. It
composes simulation, sensor adapters, the safety supervisor, the
observability recorder, and the runtime diagnostics:

```bash
ros2 launch rover_bringup full_system.launch.py \
  headless:=true \
  enable_diagnostics:=true \
  record_bag:=true \
  scenario_id:=runtime_validation \
  run_id:=$(date -u +runtime-%Y%m%dT%H%M%SZ)
```

Wait ~10 seconds for steady state. The launch log is verbose; the
runtime validator captures the entire log into
`evidence/runtime/<run_id>/launch-log.txt` for the live path.

If you want the diagnostics nodes only (e.g. against a pre-existing
sim), use `runtime_validation.launch.py` instead.

## 3. Run the probes

The Phase 4 probes live under `rover_ws/tools/`. Each is a CLI you can
run directly; the orchestrator `live_runtime_validator.py` runs all of
them and writes the aggregate report.

### 3.1 Orchestrator (recommended)

```bash
python3 rover_ws/tools/live_runtime_validator.py \
  --evidence-root evidence/runtime \
  --canonical-report \
  --ros-launch                # opt-in: actually invoke ros2 launch
```

Outputs:

* `evidence/runtime/<run_id>/runtime-validation.json` — machine-readable
  status manifest (one entry per check).
* `evidence/runtime/<run_id>/runtime-validation.md` — human-readable
  Markdown report.
* `evidence/runtime/<run_id>/known-limitations.md` — stand-alone
  known-limitations callout.
* `evidence/runtime/<run_id>/<per-probe>.json` — per-probe artefacts
  (see below).
* `docs/RUNTIME_VALIDATION_REPORT.md` — only when
  `--canonical-report` is supplied; mirrors the run's Markdown report.

Pass `--static-only` to force the offline path. Useful in CI or on a
workstation that lacks Jazzy / Gazebo.

### 3.2 Individual probes

Each probe accepts the same common flags
(`--static-only`, `--evidence-root`, `--run-id`, `--workspace-root`,
`--json`).

| Probe | Live evidence | Static evidence | Status vocabulary |
| --- | --- | --- | --- |
| `launch_smoke_test.py` | `node-snapshot.json`, `launch-log.txt` | same files; live cells `not_executed` | `passed` / `failed` / `not_executed` |
| `topic_probe.py` | `topic-snapshot.json` | same file; live cells `not_executed` | `passed` / `failed` / `not_executed` |
| `tf_probe.py` | `tf-snapshot.json`, `tf-tree.txt` | same files; live cells `not_executed` | `passed` / `failed` / `not_executed` |
| `command_path_probe.py` | `command-path-audit.json` | same file (statically verifiable) | `passed` / `failed` |
| `runtime_capture.py` | `runtime-capture-<scenario>.json` | same file (deterministic engine) | `passed` / `failed` / `not_executed` |

`launch_smoke_test.py` requires `--ros-launch` to actually invoke
`ros2 launch`. Without it the probe runs in static-only mode even on
a Jazzy host. This avoids surprising side-effects when the orchestrator
runs from CI.

### 3.3 Scenario-driven runtime capture

```bash
python3 rover_ws/tools/runtime_capture.py \
  --scenario stale_lidar_restricted_mode \
  --evidence-root evidence/runtime
```

The scenario list mirrors `app.verification.scenario_verifier`. In
static-only mode the probe runs the deterministic engine; live mode
(opt-in via `--ros-launch`) is reserved for a Jazzy host with the
`rover_fault_injection` node available.

## 4. Reading a report

`runtime-validation.md` reports five status values, defined in
`app/verification/acceptance.py`:

| Status | Meaning |
| --- | --- |
| `passed` | The check held; evidence is captured. |
| `failed` | The check explicitly failed. The orchestrator returns a non-zero exit code. |
| `partial` | Some sub-checks passed, some did not yet run. The reporter does **not** call this a pass. |
| `skipped` | The check was deliberately bypassed (e.g. an optional frame). |
| `not_executed` | The check requires a Jazzy host and could not run in this environment. The report carries an explicit reason. |

Treat `not_executed` as “evidence not collected.” Never read it as a
pass.

## 5. CI fallback

CI executes only the static-only path:

```bash
python3 rover_ws/tools/live_runtime_validator.py \
  --static-only \
  --evidence-root evidence/runtime \
  --canonical-report
```

The orchestrator returns a non-zero exit code if any *static* check
fails. `not_executed` checks do not fail the build because CI cannot
run them, but they are surfaced in the report so reviewers see what
was skipped.

## 6. Updating expected topics / nodes / frames

When the workspace gains a new topic, node, or TF frame that should be
part of the runtime contract:

1. Add an entry to the relevant module under
   `backend/app/runtime_validation/`:
   * `expected_topics.py` for new topics,
   * `expected_nodes.py` for new ROS nodes,
   * `expected_tf_frames.py` for new TF frames.
2. Mark `required=False` if the entry is best-effort.
3. Re-run `python3 rover_ws/tools/live_runtime_validator.py` and
   confirm the static checks still pass.
4. The runtime validation tests under
   `rover_ws/tests/test_runtime_validation_tooling.py` pin the
   structural contract; update them when the contract changes.

## 7. Troubleshooting

| Symptom | Likely cause | Resolution |
| --- | --- | --- |
| `rclpy not importable` in the report | `/opt/ros/jazzy/setup.bash` not sourced | source ROS, re-run; or pass `--static-only` to acknowledge the gap |
| `ros2 CLI not on PATH` | same as above | source ROS |
| `gz CLI not on PATH` | Gazebo Harmonic missing | install Gazebo Harmonic for Jazzy |
| Required topic shows `failed` (live) | publisher is not advertising | check `ros2 topic list`; the launch may still be coming up |
| Required frame shows `failed` (live) | TF transform missing | inspect `tf-tree.txt`; check `robot_state_publisher` and `ros_gz_bridge` |
| `command_path_probe` flags a foreign publisher | a node outside `rover_safety_bridge` is publishing `/cmd_vel_authorized` | architectural violation — fix the offending node |
| `runtime-validation.json` missing | orchestrator crashed before writing | re-run with `--json`; capture stderr |

## 8. Related documents

* `docs/RUNTIME_VALIDATION_REPORT.md` — most recent canonical report.
* `docs/VERIFICATION_STRATEGY.md` — how this layer fits into the
  Phase-3 verification approach.
* `docs/TRACEABILITY_MATRIX.md` — REQ-RUNTIME-001..005 map onto the
  probes documented here.
* `docs/SCENARIO_VERIFICATION_REPORT.md` — scenario-driven evidence
  generated in Phase 3.

This runbook does not claim safety certification. It documents the
operations that produce honest, repeatable engineering evidence for
the live ROS 2 / Gazebo runtime path.
