# Runtime validation, mission, and verification tools

Standalone CLIs grouped by phase. Each tool prints a structured
summary and exits with a non-zero status on failure. They are
runnable:

* by hand during local debugging,
* from CI (without ROS 2 / Gazebo installed),
* from the `rover_ws/tests/manual.md` acceptance script (with a
  Jazzy host).

All tools accept `--json` to emit the structured result as JSON for
CI piping.

## Setup

```bash
# Make `app.*` importable.
cd backend && pip install -e . && cd ..
```

## Phase 1C — runtime / replay validators

| Tool | What it validates |
|---|---|
| `tools/validate_bridge_topics.py <bridge.yaml>` | ros_gz_bridge YAML against ADR-004 (only `/cmd_vel_authorized` is bridged ROS_TO_GZ on a motion topic, no `/cmd_vel*` forwards, all required topics present). |
| `tools/validate_tf_tree.py <rover.urdf.xacro>` | URDF link/joint structure: required frames, single root, no orphans, no duplicate parents. |
| `tools/validate_event_integrity.py <events.jsonl>` | Every line conforms to the canonical event envelope; no duplicate event IDs. |
| `tools/validate_replay_run.py <runs/<run_id>>` | Run directory layout + `metadata.json` schema + `events.jsonl` schema + per-producer ordering + linked-event resolution. |
| `tools/validate_safety_pipeline.py` | Drives the deterministic engine through six in-process checks: only the supervisor publishes authorised motion; SAFE_STOP forces zero motion; E_STOP_LATCHED does not self-clear; clamping emits an event; fault injection emits no `safety_transition.*`; no other module constructs `AuthorizedMotionCommand`. |
| `tools/run_scenario_suite.py [<runs_root>]` | Executes the Phase 1C + Phase 2 scenarios, validates each run directory, asserts expected final state, and prints a tabular summary. |

## Phase 2 — mission validators

| Tool | What it validates |
|---|---|
| `tools/validate_mission_run.py <runs/<run_id>>` | Mission-level run-directory checks: `mission_state_transitions.jsonl`, `waypoint_events.jsonl`, `recovery_events.jsonl`, `world_model_snapshots.jsonl`. |

## Phase 3 — verification, audits, evidence

| Tool | Purpose |
|---|---|
| `tools/audit_command_path.py <runs/<run_id>>` | Audits `commands.jsonl`: only the supervisor's arbiter constructs `AuthorizedMotionCommand`; SAFE_STOP / E_STOP / forced-zero states never carry non-zero motion; ACTIVE_* states never exceed documented limits. |
| `tools/audit_safety_transitions.py <runs/<run_id>>` | Audits safety state transitions in `events.jsonl` against `app.safety.transitions`. Enforces `E_STOP_LATCHED` and `SAFE_STOP` outbound restrictions and reason-code presence. |
| `tools/verify_replay_integrity.py <runs/<run_id>>` | Phase 3 wrapper that composes the Phase 1C and Phase 2 validators into a single `passed`/`failed`/`partial`/`not_executed` status. |
| `tools/generate_evidence.py [--scenario <id>]` | Runs every (or selected) scenario through the verifier and writes `evidence/scenarios/<scenario_id>/` with `evidence.json`, `evidence.md`, `events-summary.md`, `replay-integrity.json`, `command-audit.json`, `safety-transition-audit.json`. |
| `tools/generate_traceability.py [--with-verification]` | Generates `verification/traceability.json` and `docs/TRACEABILITY_MATRIX.md`. With `--with-verification` it runs the verifier first so each row carries live status. |
| `tools/generate_verification_report.py` | Generates `docs/SCENARIO_VERIFICATION_REPORT.md` and `verification/verification_report.json` from a fresh verifier run. Distinguishes `passed`, `failed`, `partial`, `skipped`, `not_executed`. |

## Reproducing a Phase 3 verification run

```bash
# Run every scenario, write evidence, generate the report and matrix.
python tools/generate_verification_report.py \
    --runs-root runs/verify \
    --evidence-root evidence \
    --md-out docs/SCENARIO_VERIFICATION_REPORT.md \
    --json-out verification/verification_report.json
python tools/generate_traceability.py \
    --json-out verification/traceability.json \
    --md-out docs/TRACEABILITY_MATRIX.md \
    --with-verification \
    --runs-root runs/verify \
    --evidence-root evidence
```

A healthy run prints `overall=passed`. Anything else (`partial`,
`failed`, `not_executed`) is a regression and must be triaged before
merge. **The platform is not safety-certified;** these tools
demonstrate engineering verification discipline only.
