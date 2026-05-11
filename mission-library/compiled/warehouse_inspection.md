# Compiled Mission Plan

_This system is not safety-certified and does not authorize autonomous deployment._

- **plan_id:** `warehouse_inspection`
- **status:** `compile_ok`
- **compile_hash:** `af2ea27c7cc698d7c2d2cffddaf95fc6247fcd1f9636cfd0ad11820cbb3bdef9`
- **compiler_version:** `phase14a-1`
- **odd_profile_id:** `default-warehouse`
- **generated (UTC):** `2026-05-12T00:00:00+00:00`
- **replay_binding_id:** `replay-warehouse_inspection`

## Intent

> Original: Drive to waypoint bravo. Inspect loading_zone_two. Avoid restricted corridors. Return to dock if lidar health degrades. Limit speed to 1.0 m/s.

> Normalised: drive to waypoint bravo. inspect loading_zone_two. avoid restricted corridors. return to dock if lidar health degrades. limit speed to 1.0 m/s

## Objectives

- **obj-01** (move): move/bravo  
  - parameters: target=`bravo`  
  - source clause: `drive to waypoint bravo`
- **obj-02** (inspect): inspect/loading_zone_two  
  - parameters: zone=`loading_zone_two`  
  - source clause: `inspect loading_zone_two`

## Constraints

- **con-03** (avoid_region): avoid_region/restricted corridors  
  - parameters: region=`restricted corridors`  
  - source clause: `avoid restricted corridors`
- **con-04** (recovery_directive): recovery_directive/lidar health degrades  
  - parameters: trigger=`lidar health degrades`  
  - source clause: `return to dock if lidar health degrades`
- **con-05** (speed_limit): speed_limit/1.0  
  - parameters: limit_mps=`1.0`  
  - source clause: `limit speed to 1.0 m/s`

## Risk

- band: `low`
- score: `15`
- drivers:
  - `mission_complexity:10`
  - `extended_autonomy_stages:1`
  - `recovery_directive_present`
  - `speed_limited_below_odd`

## Mission graph (Mermaid)

```mermaid
flowchart TD
    start["Mission start"]
    n_01["move/bravo"]
    n_02["inspect/loading_zone_two"]
    end["Mission end"]
    start --> n_01
    n_01 --> n_02
    n_02 --> end
```

## Explainability chain

- USER INPUT: Drive to waypoint bravo. Inspect loading_zone_two. Avoid restricted corridors. Return to dock if lidar health degrades. Limit speed to 1.0 m/s.
- NORMALIZED INPUT: drive to waypoint bravo. inspect loading_zone_two. avoid restricted corridors. return to dock if lidar health degrades. limit speed to 1.0 m/s
- EXTRACTED CLAUSES:
-   - [move_to_target] drive to waypoint bravo :: target=bravo
-   - [inspect_zone] inspect loading_zone_two :: zone=loading_zone_two
-   - [avoid_region] avoid restricted corridors :: region=restricted corridors
-   - [recovery_directive_return_to_dock] return to dock if lidar health degrades :: trigger=lidar health degrades
-   - [speed_limit] limit speed to 1.0 m/s :: limit_mps=1.0
- NORMALIZED OBJECTIVES:
-   - obj-01 move :: move/bravo
-   - obj-02 inspect :: inspect/loading_zone_two
- NORMALIZED CONSTRAINTS:
-   - con-03 avoid_region :: avoid_region/restricted corridors
-   - con-04 recovery_directive :: recovery_directive/lidar health degrades
-   - con-05 speed_limit :: speed_limit/1.0
- VALIDATION DIAGNOSTICS: (none)
- RISK CLASSIFICATION: band=low score=15 drivers=['mission_complexity:10', 'extended_autonomy_stages:1', 'recovery_directive_present', 'speed_limited_below_odd']
- FINAL COMPILED PLAN STATUS: compile_ok
