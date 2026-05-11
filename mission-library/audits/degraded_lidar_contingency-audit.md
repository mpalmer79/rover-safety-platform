# Mission Compile Audit

_This system is not safety-certified and does not authorize autonomous deployment._

- **plan_id:** `degraded_lidar_contingency`
- **compile_hash:** `929588f3613b840609a12b0ee467f04a3210288c2a4673db088797207c5f9835`
- **compiler_version:** `phase14a-1`
- **odd_profile_id:** `default-warehouse`
- **status:** `compile_ok`
- **generated (UTC):** `2026-05-12T00:00:00+00:00`

## Original intent

> Inspect inspection_zone_north. Safe-stop on lidar stale. Continue under degraded conditions. Return to dock if lidar stale.

## Normalised intent

> inspect inspection_zone_north. safe-stop on lidar stale. continue under degraded conditions. return to dock if lidar stale

## Risk: `low` (score `20`)

- driver: `extended_autonomy_stages:1`
- driver: `safety_trigger_present`
- driver: `recovery_directive_present`

## Replay compatibility

- runtime_executed: `false`
- binding_id: `replay-degraded_lidar_contingency`
