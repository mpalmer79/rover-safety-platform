# Example: degraded_lidar_contingency

_Mission with degraded-mode contingency + recovery directive._

- Expected status: `compile_ok`
- Actual status: `compile_ok`
- Risk: `low` (score `20`)
- Objectives: 1
- Constraints: 3
- Diagnostics: 0

## Intent

> Inspect inspection_zone_north. Safe-stop on lidar stale. Continue under degraded conditions. Return to dock if lidar stale.

## Files

- plan json: `mission-library/compiled/degraded_lidar_contingency.json`
- plan md:   `mission-library/compiled/degraded_lidar_contingency.md`
- audit:     `mission-library/audits/degraded_lidar_contingency-audit.json`
- replay:    `mission-library/compiled/degraded_lidar_contingency-replay-binding.json`
