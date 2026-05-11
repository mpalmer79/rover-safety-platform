# Mission Compile Audit

_This system is not safety-certified and does not authorize autonomous deployment._

- **plan_id:** `contradictory_request`
- **compile_hash:** `2d829235e3787196fe14de150382e250d055dcc4a935986d1fd3d894f6f49658`
- **compiler_version:** `phase14a-1`
- **odd_profile_id:** `default-warehouse`
- **status:** `compile_rejected`
- **generated (UTC):** `2026-05-12T00:00:00+00:00`

## Original intent

> Drive to waypoint alpha. Do not enter waypoint alpha. Return to dock.

## Normalised intent

> drive to waypoint alpha. do not enter waypoint alpha. return to dock

## Risk: `critical` (score `95`)

- driver: `mission_complexity:10`
- driver: `rejections:1`

## Validation diagnostics

- `[rejection/contradiction]` mission both visits and avoids region 'alpha'

## Replay compatibility

- runtime_executed: `false`
- binding_id: `replay-contradictory_request`
