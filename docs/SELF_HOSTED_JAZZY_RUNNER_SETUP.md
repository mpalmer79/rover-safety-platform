# Self-Hosted Jazzy Runner Setup

This is the operational checklist for attaching a self-hosted GitHub
Actions runner that can execute the
`live-runtime-evidence` workflow and produce real, bag-backed runtime
evidence for this repository.

The platform is **not safety-certified.** This document describes
engineering qualification discipline and nothing more.

## 1. Required host

| Component        | Required                                | Verification                                         |
|------------------|------------------------------------------|------------------------------------------------------|
| OS               | Ubuntu 24.04 LTS (Noble Numbat)          | `lsb_release -ds` returns "Ubuntu 24.04…"            |
| ROS distribution | ROS 2 Jazzy desktop                      | `ros2 --help` succeeds after `source /opt/ros/jazzy/setup.bash` |
| Simulator        | Gazebo Harmonic                          | `gz sim --version` returns "Gazebo Sim, version 8.x" |
| Build tool       | colcon (Python 3.12+)                    | `colcon --help` succeeds                             |
| ROS bridge       | `ros_gz_bridge`                          | `ros2 pkg list                                        \| grep ros_gz_bridge` |
| rosbag2          | rosbag2 + MCAP storage plugin if available | `ros2 bag --help` and `ros2 bag info --help` succeed |
| Python           | 3.12.x                                   | `python3 --version`                                  |
| GitHub runner    | Actions Runner ≥ 2.317                   | `./run.sh --version` from the runner install         |

If any row is `not present`, do not attach the runner. The workflow
will write `not_executed` evidence rather than fabricate a live run.

## 2. Required environment variables

The runner must inject:

| Variable                       | Value                                                                                                                  |
|--------------------------------|------------------------------------------------------------------------------------------------------------------------|
| `RUNNER_ENVIRONMENT`           | `self-hosted` (set automatically by recent Actions Runner versions). The workflow refuses `github-hosted`.             |
| `ROS_DOMAIN_ID`                | Pick a unique integer per runner; do not share with another machine on the same LAN.                                   |
| `RMW_IMPLEMENTATION`           | `rmw_fastrtps_cpp` (default for Jazzy) or `rmw_cyclonedds_cpp`. Match the runner's tested DDS implementation.          |
| `GZ_SIM_RESOURCE_PATH`         | Append the rover sim model paths if you launch headless.                                                               |

## 3. Required runner labels

The `live-runtime-evidence` workflow uses
`runs-on: [self-hosted, ros-jazzy, gazebo]`. Apply all three labels
when registering the runner:

```bash
./config.sh \
  --url https://github.com/mpalmer79/rover-safety-platform \
  --labels self-hosted,ros-jazzy,gazebo \
  --name rover-runner-01 \
  --work _work
```

The repository CI tests assert that the workflow declares all three
labels. Removing any of them will fail CI.

## 4. Required permissions

The runner host needs:

* read/write access to `${HOME}/rover_ws` for `colcon build`;
* read/write access to the workflow's working directory for
  `evidence/runtime/<run_id>/` artefacts;
* permission to bind ROS DDS sockets on `lo` (no special privileges
  required if the runner user is in `dialout` for any optional
  hardware ports — there is no requirement for it in simulation).

Do not run the runner as root. Do not grant the runner permission to
push to this repository; the workflow only uploads artefacts.

## 5. Disk layout

```
${HOME}/actions-runner/    # GitHub Actions runner install
${HOME}/rover_ws/          # the colcon workspace built by the workflow
${HOME}/_work/<run_id>/rover-safety-platform/   # workflow checkout
```

Reserve at least:

* 5 GiB for the workspace build (`rover_ws/install`, `rover_ws/build`);
* 1 GiB free per live evidence run (a 30-second smoke bag is
  typically <50 MiB; a 5-minute qualification bag can reach 500 MiB).

The workflow uploads artefacts with `retention-days: 30` for
evidence and `retention-days: 90` for the maturity baseline. Local
disk should be sized for at least one rolling week of runs.

## 6. Per-runner profile

Copy the committed template and replace placeholders on the runner
host (this file is gitignored, so keep it on the runner only):

```bash
cp live-runtime/runner-profile.template.json \
   live-runtime/runner-profile.local.json
$EDITOR live-runtime/runner-profile.local.json
```

Required edits:

* `runner_id`: the value passed to `./config.sh --name`.
* `workspace_path`: absolute path to `rover_ws` on the runner.
* `python_version`: actual `python3 --version` output.
* `bag_format`: `mcap` (preferred) or `db3`.

The committed template stays `runner_status: unqualified`. Only the
local profile may be promoted by the pipeline after a passing
bag-backed run.

## 7. Verification dry run

Before the first real run, do a dry run from the runner shell:

```bash
source /opt/ros/jazzy/setup.bash
python3 rover_ws/tools/run_live_runtime_pipeline.py \
  --scenario-plan live-runtime/scenario-plans/smoke-live-runtime.yaml \
  --runner-profile live-runtime/runner-profile.local.json \
  --output evidence/runtime/dry-run-$(date -u +%Y%m%dT%H%M%SZ) \
  --dry-run
```

The expected output is:

```
mode: dry_run
status: not_executed
reason: dry-run requested
```

If the runner profile fails validation, fix the local profile before
attaching the runner to the workflow.

## 8. First real run

Trigger `live-runtime-evidence` from the GitHub Actions UI with the
default smoke scenario plan and `promote_baseline=false`. Inspect
the uploaded `evidence/runtime/<run_id>/evidence.md` and the
`bag-manifest.json`. Only after a bag-backed result reproduces
should you re-trigger the workflow with `promote_baseline=true`.

## 9. Artefact retention expectations

| Artefact                                    | Retention | Source                              |
|---------------------------------------------|-----------|-------------------------------------|
| `evidence/runtime/<run_id>/`                | 30 days   | uploaded by `live-runtime-evidence` |
| `live-runtime/baselines/maturity-baseline.json` | 90 days | uploaded by `live-runtime-evidence` |
| host qualification log                      | 30 days   | bundled with the evidence artefact  |
| colcon build log                            | 30 days   | bundled with the evidence artefact  |

These match the workflow's `retention-days` values. Increase them
only if you have a reviewer agreement to hold evidence longer.
