# Mission rehearsal report: inspection_lane_beta

_This rehearsal pipeline is simulation-only and does not authorize live robot execution or safety certification._

- **Request id:** `inspection_lane_beta`
- **Mission id:** `inspection_lane_beta`
- **Final status:** `completed`
- **Safety status:** `guarded`
- **Supervisor decision:** `approved`
- **Plan deterministic hash:** `175532b90b9f7a7b`
- **Runtime deterministic hash:** `099a5e38572dbf43`
- **Generated (UTC):** 2026-05-13T00:00:00+00:00

## Request

- description: Inspect lane beta and dock
- proposal source: Inspect lane beta sensors, then dock.
- seed: 42
- operator: test-operator

## Mission plan

- risk band: `guarded`
- waypoints: 2
  - `beta` (inspect) dist=1.5 m, angle=0.0° speed=0.2 m/s
  - `dock` (dock) dist=0.0 m, angle=0.0° speed=0.0 m/s
- requested topics: `/cmd_vel_requested`
- forbidden topics: `/cmd_vel`

## Validation

_validation passed cleanly_

## Supervisor decision

- status: `approved`
- safety status: `guarded`
- rationale:
  - Supervisor authority is preserved; no motion runs without this approval.
  - Bounded motion, allowed topics, and stop condition verified.

## Runtime

- events: 12
- started: 2026-05-13T00:00:00+00:00
- finished: 2026-05-11T13:49:57+00:00
- state transitions:
  - `created` → `validated` (validation_passed)
  - `validated` → `approved` (supervisor_approved)
  - `approved` → `rehearsing` (runtime_started)
  - `rehearsing` → `completed` (mission_completed)

## Replay bundle

- evidence status: `simulated`
- bag-backed: False
- review status: `passed`
- markers: 11

## Analytics

- rehearsal_count: `1`
- approved_count: `1`
- rejected_count: `0`
- aborted_count: `0`
- completed_count: `1`
- supervisor_rejection_count: `0`
- validator_rejection_count: `0`
- deterministic_replay_stable: `True`

## Authority statement

This rehearsal report is simulation-only. The runtime safety supervisor and motion arbitration remain authoritative; nothing in this artefact authorises live robot motion or implies safety certification.
