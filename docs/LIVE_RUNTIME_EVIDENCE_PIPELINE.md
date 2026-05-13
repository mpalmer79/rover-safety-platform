# Live Runtime Evidence Pipeline

Phase 13 introduces the live ROS 2 / Gazebo runtime evidence pipeline.
The platform is **not safety-certified**; this document describes
engineering qualification infrastructure, not a regulatory artifact.

**Phase 17C downstream.** When a Phase 13 self-hosted runner
produces a `bag-manifest.json` with `bag_status = bag_backed`, an
operator may post-process the bag into
`evidence/runtime/<run_id>/pose-samples.jsonl` and run
`tools/generate_spatial_replay.py` to emit a
`spatial-replay/runs/<run_id>/` directory the Mission Control UI
can render. See `docs/BAG_BACKED_SPATIAL_REPLAY.md` and
`docs/BAG_TO_TRAJECTORY_PIPELINE.md`.

## 1. Goal

Move from `static-only / fixture-backed` evidence to live ROS 2 /
Gazebo runtime evidence with real `rosbag2` artifacts — without
faking the transition. Until a self-hosted Jazzy + Gazebo runner
exists, every live run honestly reports `not_executed`.

## 2. Architectural placement

The live pipeline is a *new input* to the existing evidence
pipelines. It does **not** replace any of them.

```
                        ┌──────────────────────────────┐
                        │ live ROS 2 / Gazebo runtime  │
                        │ (self-hosted Jazzy host)     │
                        └──────────────┬───────────────┘
                                       │ bags + events
                                       ▼
   evidence/runtime/<run_id>/  ←  Phase 13 capture
                                       │
                                       ▼
                          incident reconstruction (Phase 6)
                                       │
                                       ▼
                          replay review bundle (Phase 7)
                                       │
                                       ▼
                          replay analytics (Phase 8)
                                       │
                                       ▼
                          reliability impact (Phase 9)
                                       │
                                       ▼
                          programme review (Phase 10)
                                       │
                                       ▼
                          reviewer export (Phase 11)
```

Existing contracts remain authoritative. The live layer just
produces the same shapes those layers already consume.

## 3. Outputs per live run

```
evidence/runtime/<run_id>/
  metadata.json              run id, plan id, runner id, times, disclaimer
  runner-profile.json        the host that produced (or attempted) the run
  live-run-summary.json      overall status (passed/failed/partial/skipped/not_executed)
  bag-manifest.json          bag status + artifact paths + topic inventory
  bags/                      real bag files (mcap or sqlite3) when bag_backed
  logs/                      launch + node logs
  events.jsonl               supervisor events captured during the run
  qualification-summary.md   human-readable summary
  known-limitations.md       honest gap list (always present)
```

When live execution does not occur, the same layout is produced
with `bag_status=not_executed` and a structured reason string.

## 4. Status vocabularies

| Vocabulary | Values |
| --- | --- |
| Run status | `passed`, `failed`, `partial`, `skipped`, `not_executed` |
| Bag status | `bag_backed`, `missing_bag`, `partial`, `not_executed`, `invalid` |
| Runner qualification | `qualified`, `partial`, `not_qualified`, `unknown` |

## 5. Honesty rules

1. `bag_backed` requires at least one bag file *that exists on disk*
   plus a metadata YAML. Static fixtures cannot become `bag_backed`.
2. `not_executed` requires a structured `not_executed_reason`.
3. The runner profile validator must pass before live execution may
   start; otherwise the runner aborts with `not_executed` and the
   reason becomes the validator output.
4. The `live-runtime-evidence.yml` workflow declares
   `runs-on: [self-hosted, ros-jazzy, gazebo]` and
   `workflow_dispatch` only — it cannot run on a GitHub-hosted
   `ubuntu-*` runner. A static check fails the build if a
   `ubuntu-` runner ever appears in the file.
5. The downstream pipeline orchestrator
   (`rover_ws/tools/process_live_runtime_evidence.py`) preserves
   the manifest's `bag_status` verbatim — it never upgrades
   `static_only` / `missing_bag` to `bag_backed`.

## 6. Modules

`backend/app/live_runtime/`:

| Module | Role |
| --- | --- |
| `models.py` | Status constants, dataclasses, disclaimer constant. |
| `runner_profile.py` | Profile loading, validation, JSON Schema. |
| `scenario_plan.py` | YAML scenario plan loading + validation. |
| `bag_manifest.py` | Bag manifest construction, validation, bag-backed check. |
| `evidence_capture.py` | Build the `evidence/runtime/<id>/` bundle. |
| `maturity.py` | Aggregate live runs into a maturity report. |
| `report.py` | Render the maturity report (JSON + Markdown). |

CLIs (`rover_ws/tools/`):

| Tool | Purpose |
| --- | --- |
| `live_bag_capture.py` | Drives a live run; writes the evidence bundle (or a `not_executed` bundle). |
| `validate_live_runtime_evidence.py` | Validates a bundle against the honesty rules. |
| `process_live_runtime_evidence.py` | Feeds a bundle into downstream pipelines (dry-run by default). |
| `generate_live_runtime_maturity_report.py` | Aggregates + renders the maturity report. |

## 7. Workflow

`.github/workflows/live-runtime-evidence.yml`:

* `runs-on: [self-hosted, ros-jazzy, gazebo]` (never GitHub-hosted),
* `workflow_dispatch` only,
* fails fast with an explicit error if `ROS_DISTRO != jazzy`,
* qualifies the host → builds the workspace → captures bags →
  validates evidence → processes downstream → regenerates the
  maturity report → uploads artifacts.

If GitHub-hosted CI ever attempts to claim live execution, the
guard step exits non-zero — by design.

## 8. What this layer does NOT do

* It does not invent bags, events, or runner profiles.
* It does not run new autonomy or new safety logic.
* It does not change existing report shapes.
* It does not weaken any prior phase's invariants.
* It does not claim safety certification.

## 9. Related documents

- [`LIVE_BAG_CAPTURE_RUNBOOK.md`](LIVE_BAG_CAPTURE_RUNBOOK.md)
- [`LIVE_RUNNER_PROFILE.md`](LIVE_RUNNER_PROFILE.md)
- [`LIVE_RUNTIME_MATURITY_REPORT.md`](LIVE_RUNTIME_MATURITY_REPORT.md)
- [`REPLAY_SYSTEM.md`](REPLAY_SYSTEM.md)
- [`REPLAY_REVIEW_RUNBOOK.md`](REPLAY_REVIEW_RUNBOOK.md)
- [`REPLAY_ANALYTICS.md`](REPLAY_ANALYTICS.md)
- [`PROGRAMME_REVIEW.md`](PROGRAMME_REVIEW.md)
- [`REVIEWER_EXPORTS.md`](REVIEWER_EXPORTS.md)
- [`ROADMAP.md`](ROADMAP.md)
