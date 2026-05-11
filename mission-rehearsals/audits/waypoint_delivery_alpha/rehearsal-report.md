# Mission rehearsal report: waypoint_delivery_alpha

_This rehearsal pipeline is simulation-only and does not authorize live robot execution or safety certification._

- **Request id:** `waypoint_delivery_alpha`
- **Mission id:** `waypoint_delivery_alpha`
- **Final status:** `completed`
- **Safety status:** `guarded`
- **Supervisor decision:** `approved`
- **Plan deterministic hash:** `5706db76d64866ec`
- **Runtime deterministic hash:** `60d8ab6cf2f9de78`
- **Generated (UTC):** 2026-05-13T00:00:00+00:00

## Request

- description: Deliver to waypoint alpha and return
- proposal source: Deliver to waypoint alpha, return to dock.
- seed: 42
- operator: test-operator

## Mission plan

- risk band: `guarded`
- waypoints: 2
  - `alpha` (move) dist=4.0 m, angle=0.0° speed=0.25 m/s
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
