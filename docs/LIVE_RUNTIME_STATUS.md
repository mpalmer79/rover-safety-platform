# Live Runtime Status

_Short-form status page distinguishing static-source, static-workspace, and live-runtime checks. The platform is **not safety-certified**._

- **Run id:** `qualified-2026-05-10`
- **Mode:** `static-only`
- **Generated:** 2026-05-10T00:01:44+00:00
- **Overall status:** `partial`

## static-source

| Check | Status | Detail |
|---|---|---|
| `host_qualification` | `partial` | 4 of 9 host checks passed |

## static-workspace

| Check | Status | Detail |
|---|---|---|
| `scenario_pack[authorized_motion_path]` | `passed` | ok |
| `scenario_pack[command_timeout_safe_stop]` | `passed` | ok |
| `scenario_pack[estop_latched_manual_reset_required]` | `passed` | ok |
| `scenario_pack[nominal_runtime_launch]` | `passed` | ok |
| `scenario_pack[safe_stop_command_zeroing]` | `passed` | ok |
| `scenario_pack[stale_lidar_restricted_mode]` | `passed` | ok |
| `static.bridge_yaml_valid` | `passed` | validated 8 topics |
| `static.required_topics_declared` | `passed` | 12 required topics declared |
| `static.urdf_tf_tree` | `passed` | 8 links validated; runtime root=odom (published by simulator) |
| `static.full_system_launch_composes_required_packages` | `passed` | full_system.launch.py composes simulation, safety, observability, diagnostics |
| `static.node_modules_present` | `passed` | 4 node module families present |
| `static.safety_bridge_authority_invariant` | `passed` | supervisor publishes /cmd_vel_authorized and never publishes /cmd_vel |
| `static.runtime_validation_runbook_complete` | `passed` | runbook covers prerequisites, launch, validation, and tooling |
| `launch_smoke_test` | `not_executed` | live launch not exercised; ran static-only mode (every required node declared) |
|   _reason_ |   | rclpy not importable: No module named 'rclpy' |
| `topic_probe` | `not_executed` | live topic graph not exercised; ran static-only mode |
|   _reason_ |   | rclpy not importable: No module named 'rclpy' |
| `tf_probe` | `not_executed` | live tf graph not exercised; ran static-only mode (URDF link/joint check passed) |
|   _reason_ |   | rclpy not importable: No module named 'rclpy' |
| `command_path_probe` | `passed` | 4 command-path invariant(s) verified statically |
|   _reason_ |   | rclpy not importable: No module named 'rclpy' |

## live-runtime

_No `live-runtime` checks recorded for this run._
