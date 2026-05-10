# Foxglove Replay Workflow

This document explains how to use the Foxglove integration shipped
with the Phase 6 incident analysis layer. The platform is **not**
safety-certified; this workflow is engineering review tooling.

## 1. What ships with the repo

| Artefact | Purpose |
| --- | --- |
| `foxglove/layouts/incident-review-layout.json` | Canonical Foxglove layout for incident review. Five panels: safety state plot, requested-vs-authorised cmd_vel plot, system health diagnostic, safety-events log, mission-events log. |
| `incidents/<incident_id>/foxglove-replay-hints.json` | Per-incident hint file: recommended topics, timeline markers (first fault / first safety transition / first command intervention / terminal), command + diagnostic + fault topic groups, and a pointer to the layout. |
| `backend/app/incident_analysis/foxglove.py` | Pure-logic generator for the hints + layout. Tests do not require Foxglove to be installed. |

## 2. Prerequisites for live replay

Foxglove is **not** required to generate the hints. Tests, CI, and
the reporter all run without it. A reviewer who wants to actually
replay a recorded bag needs:

- Foxglove Studio (desktop or web) with bag-replay support,
- A recorded bag for the run id under review (typically under
  `runs/<run_id>/bags/`),
- The canonical layout: `foxglove/layouts/incident-review-layout.json`.

## 3. Workflow

### 3.1 Generate the incident bundle

```bash
python3 rover_ws/tools/reconstruct_incident.py \
  --scenario evidence/scenarios/<scenario_id> \
  --runs-root runs/verify \
  --incident-id <id> \
  --output incidents/<id>
```

This writes `foxglove-replay-hints.json` alongside the rest of the
bundle.

### 3.2 Open the bag in Foxglove

1. Open Foxglove Studio.
2. **Layout → Import from file…** → select
   `foxglove/layouts/incident-review-layout.json`.
3. **Data source → Open local file…** → select the bag for the run
   under review (e.g. `runs/<run_id>/bags/rover-bag.mcap`).
4. The five panels are pre-configured against the topics listed in
   `recommended_topics`.

### 3.3 Use the timeline markers

The hints file lists up to four markers:

```json
[
  {"label": "first_fault", "sim_time_ns": ..., "event_type": "fault_injection.fired", ...},
  {"label": "first_safety_transition", ...},
  {"label": "first_command_intervention", ...},
  {"label": "terminal", ...}
]
```

In Foxglove, scrub the timeline to each marker's `sim_time_ns` (or
the equivalent ROS time) to inspect the chain visually. The marker
`label` matches the timeline indices used in `incident-report.md`.

### 3.4 Cross-reference with the report

| Incident-report cell | Foxglove panel |
| --- | --- |
| Safety state sequence | Plot panel: `/safety/state.state` |
| Command authorisation summary | Plot panel: requested vs authorised cmd_vel |
| Replay integrity summary | Diagnostic summary: `/system/health` |
| Causality chain | Logs: `/safety/events` (use the chain's relations as keywords) |

## 4. Authoring custom layouts

Place additional layouts under `foxglove/layouts/`. The hint file
takes a `layout_path` parameter (relative to the repo root) so a
reviewer can swap layouts without re-running the analysis layer.

When committing a new layout:

1. Validate the JSON parses (`python -m json.tool < layout.json`).
2. Avoid Foxglove version-specific configById entries that are not
   present in the canonical layout, or note the requirement at the
   top of the file.

## 5. Limitations

- Foxglove is **not** automatically installed by the repo; it is a
  separate runtime.
- Bag formats vary; the canonical layout assumes `.mcap` recordings
  produced by `rosbag2`.
- Hints are static metadata; they do not stream live data.
- Replay does not exercise the safety supervisor — it only renders
  what was recorded. Use the runtime validator and qualification
  orchestrator (Phase 4 / Phase 5) for live verification.

## 6. Phase 7 replay review bundles

Phase 7 augments the per-incident bundle with a replay review
manifest, a Foxglove session JSON (internal `rover-replay-review/1`
schema), markers aligned to replay time, and a validator. The
canonical workflow is documented in
[docs/REPLAY_REVIEW_RUNBOOK.md](REPLAY_REVIEW_RUNBOOK.md). Bundle
files (`replay-review-manifest.json`, `replay-review-report.md`,
`foxglove-session.json`, `replay-markers.json`) live alongside the
incident report under `incidents/<incident_id>/`.

## 7. Related documents

- [docs/INCIDENT_RECONSTRUCTION.md](INCIDENT_RECONSTRUCTION.md)
- [docs/INCIDENT_ANALYSIS_STRATEGY.md](INCIDENT_ANALYSIS_STRATEGY.md)
- [docs/REPLAY_SYSTEM.md](REPLAY_SYSTEM.md)
- [docs/REPLAY_REVIEW_RUNBOOK.md](REPLAY_REVIEW_RUNBOOK.md)
- [docs/REPLAY_REVIEW_INDEX.md](REPLAY_REVIEW_INDEX.md)
