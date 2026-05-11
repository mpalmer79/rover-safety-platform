# Mission rehearsal report: bounded_forward_patrol

_This rehearsal pipeline is simulation-only and does not authorize live robot execution or safety certification._

- **Request id:** `bounded_forward_patrol`
- **Mission id:** `bounded_forward_patrol`
- **Final status:** `completed`
- **Safety status:** `safe`
- **Supervisor decision:** `approved`
- **Plan deterministic hash:** `7c7a9fb2b6cb5e2f`
- **Runtime deterministic hash:** `dcfca23fc834dcdd`
- **Generated (UTC):** 2026-05-13T00:00:00+00:00

## Request

- description: Bounded forward patrol with a single stop
- proposal source: Patrol forward bounded distance and dock.
- seed: 42
- operator: test-operator

## Mission plan

- risk band: `low`
- waypoints: 2
  - `wp1` (patrol) dist=3.0 m, angle=0.0° speed=0.25 m/s
  - `wp2` (dock) dist=0.0 m, angle=0.0° speed=0.0 m/s
- requested topics: `/cmd_vel_requested`
- forbidden topics: `/cmd_vel`

## Validation

_validation passed cleanly_

## Supervisor decision

- status: `approved`
- safety status: `safe`
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
