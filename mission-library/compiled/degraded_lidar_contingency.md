# Compiled Mission Plan

_This system is not safety-certified and does not authorize autonomous deployment._

- **plan_id:** `degraded_lidar_contingency`
- **status:** `compile_ok`
- **compile_hash:** `929588f3613b840609a12b0ee467f04a3210288c2a4673db088797207c5f9835`
- **compiler_version:** `phase14a-1`
- **odd_profile_id:** `default-warehouse`
- **generated (UTC):** `2026-05-12T00:00:00+00:00`
- **replay_binding_id:** `replay-degraded_lidar_contingency`

## Intent

> Original: Inspect inspection_zone_north. Safe-stop on lidar stale. Continue under degraded conditions. Return to dock if lidar stale.

> Normalised: inspect inspection_zone_north. safe-stop on lidar stale. continue under degraded conditions. return to dock if lidar stale

## Objectives

- **obj-01** (inspect): inspect/inspection_zone_north  
  - parameters: zone=`inspection_zone_north`  
  - source clause: `inspect inspection_zone_north`

## Constraints

- **con-02** (safety_trigger): safety_trigger/lidar stale  
  - parameters: trigger=`lidar stale`  
  - source clause: `safe-stop on lidar stale`
- **con-03** (contingency): contingency  
  - parameters: (none)  
  - source clause: `continue under degraded conditions`
- **con-04** (recovery_directive): recovery_directive/lidar stale  
  - parameters: trigger=`lidar stale`  
  - source clause: `return to dock if lidar stale`

## Risk

- band: `low`
- score: `20`
- drivers:
  - `extended_autonomy_stages:1`
  - `safety_trigger_present`
  - `recovery_directive_present`

## Mission graph (Mermaid)

```mermaid
flowchart TD
    start["Mission start"]
    n_01["inspect/inspection_zone_north"]
    end["Mission end"]
    recovery_dock["Recovery: return to dock"]
    start --> n_01
    n_01 --> end
    n_01 -->|"safety_trigger"| recovery_dock
    recovery_dock --> end
```

## Explainability chain

- USER INPUT: Inspect inspection_zone_north. Safe-stop on lidar stale. Continue under degraded conditions. Return to dock if lidar stale.
- NORMALIZED INPUT: inspect inspection_zone_north. safe-stop on lidar stale. continue under degraded conditions. return to dock if lidar stale
- EXTRACTED CLAUSES:
-   - [inspect_zone] inspect inspection_zone_north :: zone=inspection_zone_north
-   - [safe_stop_on_trigger] safe-stop on lidar stale :: trigger=lidar stale
-   - [continue_under_degraded] continue under degraded conditions :: (no slots)
-   - [recovery_directive_return_to_dock] return to dock if lidar stale :: trigger=lidar stale
- NORMALIZED OBJECTIVES:
-   - obj-01 inspect :: inspect/inspection_zone_north
- NORMALIZED CONSTRAINTS:
-   - con-02 safety_trigger :: safety_trigger/lidar stale
-   - con-03 contingency :: contingency
-   - con-04 recovery_directive :: recovery_directive/lidar stale
- VALIDATION DIAGNOSTICS: (none)
- RISK CLASSIFICATION: band=low score=20 drivers=['extended_autonomy_stages:1', 'safety_trigger_present', 'recovery_directive_present']
- FINAL COMPILED PLAN STATUS: compile_ok
