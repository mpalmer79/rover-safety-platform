# Mission rehearsal report: direct_motor_override

_This rehearsal pipeline is simulation-only and does not authorize live robot execution or safety certification._

- **Request id:** `direct_motor_override`
- **Mission id:** `direct_motor_override`
- **Final status:** `rejected`
- **Failure reason:** `direct_actuator_command`
- **Safety status:** `unsafe_rejected`
- **Supervisor decision:** `rejected`
- **Plan deterministic hash:** `f92a73bee2974f47`
- **Runtime deterministic hash:** `5b6bac42ee5fc219`
- **Generated (UTC):** 2026-05-13T00:00:00+00:00

## Request

- description: Direct motor override (rejected)
- proposal source: Publish to /cmd_vel directly to drive forward.
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

- [rejection] `direct_actuator_command`: proposal source contains '/cmd_vel': direct /cmd_vel reference

## Supervisor decision

- status: `rejected`
- safety status: `unsafe_rejected`
- rejected reasons: `direct_actuator_command`
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
