# Replay Review Runbook

This runbook is the operational guide for the Phase 7 replay review
workflow. The platform is **not** safety-certified; this runbook
describes engineering replay-review discipline only.

The replay review layer is **read-only with respect to runtime
evidence and rosbag2 artefacts**. It inspects, indexes, and produces
metadata. It does **not** open bag files itself; that work is left
to Foxglove.

## Bag-backed evidence input (Phase 14)

The Phase 14 live runtime pipeline produces the bag artefacts this
runbook consumes. When the pipeline writes
`evidence/runtime/<run_id>/`, the bag lives at
`evidence/runtime/<run_id>/bag/` and the canonical classification
lives in `evidence/runtime/<run_id>/bag-manifest.json`. A run is
only `bag_backed` when the manifest's `status` is `bag_backed` —
see `docs/LIVE_RUNTIME_EVIDENCE_PIPELINE.md` for the full contract.
This runbook never upgrades a `partial` or `missing_bag` run into a
bag-backed review.

## 1. Prerequisites

The full live path requires:

| Component | Required version | Purpose |
| --- | --- | --- |
| Ubuntu | 24.04 LTS (Noble) | host OS |
| ROS 2 Jazzy | full desktop install | rclpy, ros2 CLI, rosbag2 |
| Gazebo Harmonic | matching Jazzy | physics + sensor simulation |
| Python | 3.12 | matches the workspace's pinned interpreter |
| `colcon` | 2.x | builds `rover_ws/` |
| Foxglove Studio | latest | bag replay + layout import |

CI runs only the static path. The replay review layer's tests do
**not** require Foxglove or ROS to be installed.

## 2. Collect a runtime run

```bash
source /opt/ros/jazzy/setup.bash
source rover_ws/install/setup.bash
python3 rover_ws/tools/qualified_runtime_run.py \
  --ros-launch \
  --evidence-root evidence/runtime \
  --run-id "runtime-$(date -u +%Y%m%dT%H%M%SZ)" \
  --canonical-report
```

This populates `evidence/runtime/<run_id>/` and (when configured)
`runs/<run_id>/bags/`. The bag artefacts are gitignored — they live
on the recording host until they are uploaded as workflow artefacts.

## 3. Reconstruct an incident

```bash
python3 rover_ws/tools/reconstruct_incident.py \
  --runtime-run "evidence/runtime/<run_id>" \
  --incident-id "live-<run_id>" \
  --output "incidents/live-<run_id>"
```

The Phase 6 incident bundle is the **input** to the replay review
layer. If `incident-report.json` is missing, the replay tools refuse
to produce a manifest.

## 4. Build a replay review bundle

```bash
python3 rover_ws/tools/build_replay_review_bundle.py \
  --incident "incidents/live-<run_id>" \
  --run "evidence/runtime/<run_id>" \
  --runs-root runs/verify
```

The CLI:

1. Inspects every documented bag location:
   - `incidents/<incident_id>/bags/`
   - `evidence/runtime/<run_id>/bags/`
   - `runs/<run_id>/bags/`
2. Produces `replay-review-manifest.json`, `replay-review.md`,
   `foxglove-session.json`, `replay-markers.json`,
   `replay-review-report.{md,json}`.

When no bag is present (CI, fresh clone, static-only incident) the
manifest reports `bag_status` ∈ `{missing_bag, static_only}`. The
report's `replay_execution_status` mirrors this — it never claims
`ready` without evidence.

### 4.1 Status vocabulary

| Status | Meaning |
| --- | --- |
| `ready` | Bag chunks + `metadata.yaml` present; reviewer can load directly. |
| `partial` | Some bag artefacts present (chunks or metadata, not both). |
| `missing_bag` | No bag artefacts detected for a non-static incident. |
| `static_only` | The underlying incident is static-only; no bag is expected. |
| `not_executed` | Live replay was skipped (CI / no Jazzy host). |
| `failed` | A required check failed (e.g. incident-report missing). |
| `passed` | Reserved for a complete pipeline including operator review. |

## 5. Validate the bundle

```bash
python3 rover_ws/tools/validate_replay_review.py \
  --incident "incidents/live-<run_id>"
```

The validator runs the static checks (incident-report present,
timeline present, markers generated, layout exists, session
well-formed, bag artefacts present, expected topics present) and
prints the aggregate status. A failed check returns a non-zero exit
code; `not_executed` and `partial` do not fail CI.

## 6. Open Foxglove

1. Launch Foxglove Studio.
2. **Layout → Import from file…** → select
   `foxglove/layouts/incident-review-layout.json`.
3. **Data source → Open local file…** → select the file listed in
   the manifest's `bag_indices[].artifacts[]` whose kind is `mcap`
   (preferred) or `db3`.

The layout pre-configures five panels: safety state, requested-vs-
authorised cmd_vel, system health, safety events, mission events.

## 7. Inspect markers

The bundle's `replay-markers.json` lists up to seven markers:

* `first_fault`
* `first_safety_transition`
* `first_command_intervention`
* `safe_stop`
* `estop_latched`
* `recovery_started` / `recovery_completed`
* `mission_abort`
* `terminal_outcome`

Each marker carries `sim_time_ns` (when the timeline entry has it),
`relative_time_ms`, the source event id, the source file, and the
causality confidence label. Use `sim_time_ns` to align the Foxglove
playhead; when `alignment` is `partial` align manually using the
surrounding context.

## 8. Compare report claims to telemetry

Open the incident report alongside Foxglove:

| Incident report cell | Foxglove panel | Cross-check |
| --- | --- | --- |
| Safety state sequence | `Safety state` plot | Step transitions match. |
| Command authorisation summary | `Requested vs authorised cmd_vel` | Authorised never exceeds requested in NORMAL; zeroed in SAFE_STOP. |
| Replay integrity summary | `System health` | Health degrades correlate with sensor faults. |
| Causality chain | `Safety events` log | Each link's source_event_id is present in the log. |

Record any discrepancy in a separate document; **do not mutate the
incident bundle**. The Phase 7 layer is read-only.

## 9. Interpreting missing bags

A `missing_bag` status is honest, not a failure:

* CI runs always report `missing_bag` — gitignored bags aren't
  available in CI.
* A `static_only` incident never has a bag — the Phase-6 evidence
  status drives the Phase-7 bag status.
* On a Jazzy host with rosbag2 enabled, the bag should appear under
  `runs/<run_id>/bags/`. If it does not, check the
  `record_bag:=true` argument to the launch.

The replay review report says exactly which directories were
inspected; use that list to track down a misplaced bag.

## 10. Interpreting partial marker alignment

A marker with `alignment=partial` means the underlying timeline
entry has a `relative_time_ms` but no `sim_time_ns` (typical for
roll-up summaries like `motion_arbitration.summary`). The Foxglove
playhead cannot be positioned by clock; align it manually using the
event log or the surrounding event before/after.

## 11. Self-hosted live workflow

`.github/workflows/ros-jazzy-replay-review.yml` orchestrates the
full live path on a self-hosted Jazzy + Gazebo runner labelled
`ros-jazzy`. The workflow is `workflow_dispatch` only — it does
**not** run on github-hosted runners. The runbook in
`docs/RUNTIME_QUALIFICATION_RUNBOOK.md` covers runner setup.

## 12. Known limitations

- The platform is **not** safety-certified.
- Live bag replay requires Foxglove Studio + a recorded bag on a
  Jazzy host. CI runs do not exercise live replay.
- The Foxglove session JSON we ship (`foxglove-session.json` per
  incident) is **internal**: the `schema_version` field marks it as
  `rover-replay-review/1`. It is not an official Foxglove import
  format. Use it as supplementary metadata; the canonical layout is
  what Foxglove imports.
- Markers without `sim_time_ns` are aligned to relative time only;
  align the Foxglove playhead manually.

## 13. Related documents

- [docs/INCIDENT_RECONSTRUCTION.md](INCIDENT_RECONSTRUCTION.md)
- [docs/INCIDENT_ANALYSIS_STRATEGY.md](INCIDENT_ANALYSIS_STRATEGY.md)
- [docs/FOXGLOVE_REPLAY_WORKFLOW.md](FOXGLOVE_REPLAY_WORKFLOW.md)
- [docs/REPLAY_SYSTEM.md](REPLAY_SYSTEM.md)
- [docs/RUNTIME_QUALIFICATION_RUNBOOK.md](RUNTIME_QUALIFICATION_RUNBOOK.md)
- [docs/REPLAY_REVIEW_INDEX.md](REPLAY_REVIEW_INDEX.md) — generated index of replay-ready incidents.

This runbook does not claim safety certification. It documents the
operations that produce honest, repeatable engineering replay-review
artefacts for ROS 2 Jazzy + Gazebo Harmonic incidents.
