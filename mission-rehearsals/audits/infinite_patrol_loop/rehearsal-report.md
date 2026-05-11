# Mission rehearsal report: infinite_patrol_loop

_This rehearsal pipeline is simulation-only and does not authorize live robot execution or safety certification._

- **Request id:** `infinite_patrol_loop`
- **Mission id:** `infinite_patrol_loop`
- **Final status:** `rejected`
- **Failure reason:** `missing_stop_condition`
- **Safety status:** `unsafe_rejected`
- **Supervisor decision:** `rejected`
- **Plan deterministic hash:** `b6a86727fa956d53`
- **Runtime deterministic hash:** `0d085680f4bc2572`
- **Generated (UTC):** 2026-05-13T00:00:00+00:00

## Request

- description: Infinite patrol loop attempt (rejected)
- proposal source: while True: patrol forever.
- seed: 42
- operator: test-operator

## Mission plan

- risk band: `low`
- waypoints: 1
  - `wp1` (patrol) dist=2.0 m, angle=0.0° speed=0.25 m/s
- requested topics: `/cmd_vel_requested`
- forbidden topics: `/cmd_vel`

## Validation

- [rejection] `missing_stop_condition`: plan with motion waypoints must include a stop or dock waypoint
- [rejection] `unbounded_loop`: proposal source contains 'while True:': unbounded while True loop

## Supervisor decision

- status: `rejected`
- safety status: `unsafe_rejected`
- rejected reasons: `missing_stop_condition`, `unbounded_loop`
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
