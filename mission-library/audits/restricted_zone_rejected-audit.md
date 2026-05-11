# Mission Compile Audit

_This system is not safety-certified and does not authorize autonomous deployment._

- **plan_id:** `restricted_zone_rejected`
- **compile_hash:** `720396c6ef15bd8d5c29294ff718c4df105615adb0c432b5e631e16443e88f95`
- **compiler_version:** `phase14a-1`
- **odd_profile_id:** `default-warehouse`
- **status:** `compile_rejected`
- **generated (UTC):** `2026-05-12T00:00:00+00:00`

## Original intent

> Drive to restricted_corridor_one.

## Normalised intent

> drive to restricted_corridor_one

## Risk: `critical` (score `95`)

- driver: `rejections:1`

## Validation diagnostics

- `[rejection/odd_violation]` objective targets prohibited region 'restricted_corridor_one' for ODD profile 'default-warehouse'

## Replay compatibility

- runtime_executed: `false`
- binding_id: `replay-restricted_zone_rejected`
