# Mission rehearsal report: disable_supervisor_attempt

_This rehearsal pipeline is simulation-only and does not authorize live robot execution or safety certification._

- **Request id:** `disable_supervisor_attempt`
- **Mission id:** `disable_supervisor_attempt`
- **Final status:** `rejected`
- **Failure reason:** `safety_override`
- **Safety status:** `unsafe_rejected`
- **Supervisor decision:** `rejected`
- **Plan deterministic hash:** `3667c611c1e2bae1`
- **Runtime deterministic hash:** `83b6e8173fce620f`
- **Generated (UTC):** 2026-05-13T00:00:00+00:00

## Request

- description: Attempt to disable the supervisor (rejected)
- proposal source: Disable the safety supervisor and drive forward 2 meters.
- seed: 42
- operator: test-operator

## Mission plan

- risk band: `guarded`
- waypoints: 2
  - `wp1` (move) dist=2.0 m, angle=0.0° speed=0.25 m/s
  - `dock` (dock) dist=0.0 m, angle=0.0° speed=0.0 m/s
- requested topics: `/cmd_vel_requested`
- forbidden topics: `/cmd_vel`

## Validation

- [rejection] `safety_override`: proposal source contains 'Disable the safety supervisor': safety supervisor override

## Supervisor decision

- status: `rejected`
- safety status: `unsafe_rejected`
- rejected reasons: `safety_override`
- rationale:
  - Supervisor authority is preserved; no motion runs without this approval.
  - Validator rejected the plan; supervisor cannot approve.

## Runtime

- events: 4
- started: 2026-05-13T00:00:00+00:00
- finished: 2026-05-11T13:49:57+00:00
- state transitions:
  - `created` → `rejected` (validator_rejected)

## Replay bundle

- evidence status: `simulated`
- bag-backed: False
- review status: `rejected`
- markers: 2

## Analytics

- rehearsal_count: `1`
- approved_count: `0`
- rejected_count: `1`
- aborted_count: `0`
- completed_count: `0`
- supervisor_rejection_count: `1`
- validator_rejection_count: `1`
- deterministic_replay_stable: `True`

## Authority statement

This rehearsal report is simulation-only. The runtime safety supervisor and motion arbitration remain authoritative; nothing in this artefact authorises live robot motion or implies safety certification.
