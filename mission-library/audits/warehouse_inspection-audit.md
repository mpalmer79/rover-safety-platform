# Mission Compile Audit

_This system is not safety-certified and does not authorize autonomous deployment._

- **plan_id:** `warehouse_inspection`
- **compile_hash:** `af2ea27c7cc698d7c2d2cffddaf95fc6247fcd1f9636cfd0ad11820cbb3bdef9`
- **compiler_version:** `phase14a-1`
- **odd_profile_id:** `default-warehouse`
- **status:** `compile_ok`
- **generated (UTC):** `2026-05-12T00:00:00+00:00`

## Original intent

> Drive to waypoint bravo. Inspect loading_zone_two. Avoid restricted corridors. Return to dock if lidar health degrades. Limit speed to 1.0 m/s.

## Normalised intent

> drive to waypoint bravo. inspect loading_zone_two. avoid restricted corridors. return to dock if lidar health degrades. limit speed to 1.0 m/s

## Risk: `low` (score `15`)

- driver: `mission_complexity:10`
- driver: `extended_autonomy_stages:1`
- driver: `recovery_directive_present`
- driver: `speed_limited_below_odd`

## Replay compatibility

- runtime_executed: `false`
- binding_id: `replay-warehouse_inspection`
