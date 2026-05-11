# Mission Compile Audit

_This system is not safety-certified and does not authorize autonomous deployment._

- **plan_id:** `patrol_loop`
- **compile_hash:** `9ec6bfbe652020e9c6d91e01c9c18209fd5420d662c71b738e392c98a024f793`
- **compiler_version:** `phase14a-1`
- **odd_profile_id:** `default-warehouse`
- **status:** `compile_ok`
- **generated (UTC):** `2026-05-12T00:00:00+00:00`

## Original intent

> Patrol patrol_loop_a. Pause at checkpoint bravo. Return to dock.

## Normalised intent

> patrol patrol_loop_a. pause at checkpoint bravo. return to dock

## Risk: `moderate` (score `35`)

- driver: `mission_complexity:20`
- driver: `extended_autonomy_stages:1`

## Replay compatibility

- runtime_executed: `false`
- binding_id: `replay-patrol_loop`
