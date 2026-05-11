# Mission rehearsal report: emergency_stop_rehearsal

_This rehearsal pipeline is simulation-only and does not authorize live robot execution or safety certification._

- **Request id:** `emergency_stop_rehearsal`
- **Mission id:** `emergency_stop_rehearsal`
- **Final status:** `completed`
- **Safety status:** `safe`
- **Supervisor decision:** `approved`
- **Plan deterministic hash:** `06d24bc424006848`
- **Runtime deterministic hash:** `bc0107c8577fc76e`
- **Generated (UTC):** 2026-05-13T00:00:00+00:00

## Request

- description: Stop the rover immediately
- proposal source: Stop the robot immediately.
- seed: 42
- operator: test-operator

## Mission plan

- risk band: `low`
- waypoints: 1
  - `stop` (stop) dist=0.0 m, angle=0.0° speed=0.0 m/s
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

- events: 8
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
- markers: 7

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
