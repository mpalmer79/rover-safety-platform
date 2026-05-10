# Live Runner Profile

The platform is **not safety-certified**. The live runner profile
describes the host that executes (or attempts to execute) Phase 13
live runs. Without a complete and validated profile, the live
pipeline aborts with `not_executed` — by design.

## 1. File location

`live-runtime/runner-profile.json`

The shipped file is a *template* with `qualification_status: unknown`
and `supports_gazebo: false / supports_rosbag2: false`. Replacing
it with a real profile is the first step in moving a host from
`unknown` to `qualified`.

## 2. Schema

The JSON Schema (draft 2020-12) lives at
`live-runtime/runner-profile.schema.json`. Every field is required
unless marked otherwise.

| Field | Type | Notes |
| --- | --- | --- |
| `runner_id` | string | A stable identifier for the host. |
| `host_os` | string | e.g. `ubuntu-24.04`. |
| `ros_distro` | string | e.g. `jazzy`. |
| `gazebo_version` | string | e.g. `harmonic`. |
| `colcon_version` | string | The output of `colcon --version`. |
| `workspace_path` | string | Absolute path to the built workspace. |
| `supports_gazebo` | bool | Must be `true` for live execution. |
| `supports_rosbag2` | bool | Must be `true` for `bag_backed` evidence. |
| `supports_foxglove_optional` | bool | Optional; affects replay-review bundle build. |
| `runner_labels` | string[] | Should include `self-hosted`, `ros-jazzy`, `gazebo`. |
| `last_qualified_at` | string | ISO 8601 UTC. Empty until first qualification run. |
| `qualification_status` | enum | `qualified`, `partial`, `not_qualified`, `unknown`. |
| `known_limitations` | string[] | Honest list of caveats. |

## 3. Qualification states

| State | Meaning |
| --- | --- |
| `qualified` | The host validates clean, supports Gazebo + rosbag2, and produced a recent `passed` live run. |
| `partial` | The host validates but a recent live run produced `partial` results (missing topics, etc.). |
| `not_qualified` | The host fails validation; live execution will abort with `not_executed`. |
| `unknown` | No qualification has been attempted yet. (Default for the shipped template.) |

Honest invariant: `runner_supports_live_execution(profile)` returns
`True` only when the profile validates *and* both
`supports_gazebo` and `supports_rosbag2` are `True`.

## 4. Updating the profile

The profile is owned by the operator of the self-hosted runner.
The recommended flow:

1. Provision the runner with Jazzy + Harmonic + colcon + rosbag2.
2. Run `python rover_ws/tools/qualify_ros_host.py --json` and use
   its output to populate the profile.
3. Set `supports_gazebo`, `supports_rosbag2`,
   `supports_foxglove_optional` honestly.
4. Set `runner_labels` to include `self-hosted`, `ros-jazzy`,
   `gazebo` (matching the workflow's `runs-on`).
5. Set `qualification_status` to the truthful state.
6. Commit the updated `live-runtime/runner-profile.json`.

## 5. Validation

Validate the profile before each live run:

```python
from app.live_runtime import (
    load_runner_profile,
    validate_runner_profile,
    runner_supports_live_execution,
)

profile = load_runner_profile("live-runtime/runner-profile.json")
warnings = validate_runner_profile(profile)
print("warnings:", warnings)
print("can run live:", runner_supports_live_execution(profile))
```

`live_bag_capture.py` does this automatically and aborts with
`not_executed` if `runner_supports_live_execution` returns
`False`, recording the validator output as the `not_executed`
reason.

## 6. Honesty rules

* Never set `qualification_status: qualified` on a host that has
  not produced a `passed` live run with real bag artefacts.
* Never set `supports_rosbag2: true` on a host without a working
  `ros2 bag` install.
* Never set `supports_gazebo: true` on a host without Gazebo.
* The validator is intentionally pessimistic — when in doubt, leave
  the field `false` and let the runner emit `not_executed`.

## 7. Related documents

- [`LIVE_RUNTIME_EVIDENCE_PIPELINE.md`](LIVE_RUNTIME_EVIDENCE_PIPELINE.md)
- [`LIVE_BAG_CAPTURE_RUNBOOK.md`](LIVE_BAG_CAPTURE_RUNBOOK.md)
- [`RUNTIME_QUALIFICATION_RUNBOOK.md`](RUNTIME_QUALIFICATION_RUNBOOK.md)
