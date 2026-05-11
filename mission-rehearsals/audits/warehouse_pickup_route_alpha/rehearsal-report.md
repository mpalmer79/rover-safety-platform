# Mission rehearsal report: warehouse_pickup_route_alpha

_This rehearsal pipeline is simulation-only and does not authorize live robot execution or safety certification._

- **Request id:** `warehouse_pickup_route_alpha`
- **Mission id:** `warehouse_pickup_route_alpha`
- **Final status:** `completed`
- **Safety status:** `guarded`
- **Supervisor decision:** `approved`
- **Plan deterministic hash:** `f81c659dedd1b715`
- **Runtime deterministic hash:** `4dd1ccf2ab96d6fb`
- **Generated (UTC):** 2026-05-13T00:00:00+00:00

## Request

- description: Warehouse pickup route alpha (simulation-only)
- proposal source: Drive to aisle A, inspect pickup zone alpha, return to dock. Never publish to /cmd_vel directly; the safety supervisor remains authoritative.
- seed: 42
- operator: test-operator

## Mission plan

- risk band: `guarded`
- waypoints: 3
  - `wp1` (move) dist=2.5 m, angle=0.0° speed=0.25 m/s
  - `wp2` (inspect) dist=0.5 m, angle=0.0° speed=0.15 m/s
  - `wp3` (dock) dist=0.0 m, angle=0.0° speed=0.0 m/s
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

- events: 16
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
- markers: 15

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
