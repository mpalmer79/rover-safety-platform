# Phase 1C runtime validation tools

Standalone CLIs that exercise the validators in
`backend/app/validation/`. Each tool prints a structured summary and
exits with a non-zero status when validation fails. They are runnable:

* by hand during local debugging,
* from CI (without ROS 2 / Gazebo installed),
* from the `rover_ws/tests/manual.md` acceptance script (with a Jazzy
  host).

## Setup

```bash
# Make `app.*` importable.
cd backend && pip install -e . && cd ..
```

## Tools

| Tool | What it validates |
|---|---|
| `tools/validate_bridge_topics.py <bridge.yaml>` | ros_gz_bridge YAML against ADR-004 (only `/cmd_vel_authorized` is bridged ROS_TO_GZ on a motion topic, no `/cmd_vel*` forwards, all required topics present). |
| `tools/validate_tf_tree.py <rover.urdf.xacro>` | URDF link/joint structure: required frames, single root, no orphans, no duplicate parents. |
| `tools/validate_event_integrity.py <events.jsonl>` | Every line conforms to the canonical event envelope; no duplicate event IDs. |
| `tools/validate_replay_run.py <runs/<run_id>>` | Run directory layout + `metadata.json` schema + `events.jsonl` schema + per-producer ordering + linked-event resolution. |
| `tools/validate_safety_pipeline.py` | Drives the deterministic engine through six in-process checks: only the supervisor publishes authorised motion; SAFE_STOP forces zero motion; E_STOP_LATCHED does not self-clear; clamping emits an event; fault injection emits no `safety_transition.*`; no other module constructs `AuthorizedMotionCommand`. |
| `tools/run_scenario_suite.py [<runs_root>]` | Executes the seven Phase 1C scenarios end-to-end, validates each run directory, asserts expected final state, and prints a tabular summary. |

All tools accept `--json` to emit the structured result as JSON for CI
piping.
