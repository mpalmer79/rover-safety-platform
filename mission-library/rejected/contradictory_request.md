# Compiled Mission Plan

_This system is not safety-certified and does not authorize autonomous deployment._

- **plan_id:** `contradictory_request`
- **status:** `compile_rejected`
- **compile_hash:** `2d829235e3787196fe14de150382e250d055dcc4a935986d1fd3d894f6f49658`
- **compiler_version:** `phase14a-1`
- **odd_profile_id:** `default-warehouse`
- **generated (UTC):** `2026-05-12T00:00:00+00:00`
- **replay_binding_id:** `replay-contradictory_request`

## Intent

> Original: Drive to waypoint alpha. Do not enter waypoint alpha. Return to dock.

> Normalised: drive to waypoint alpha. do not enter waypoint alpha. return to dock

## Objectives

- **obj-01** (move): move/alpha  
  - parameters: target=`alpha`  
  - source clause: `drive to waypoint alpha`
- **obj-03** (return_to_dock): return_to_dock  
  - parameters: (none)  
  - source clause: `return to dock`

## Constraints

- **con-02** (avoid_region): avoid_region/alpha  
  - parameters: region=`alpha`  
  - source clause: `do not enter waypoint alpha`

## Risk

- band: `critical`
- score: `95`
- drivers:
  - `mission_complexity:10`
  - `rejections:1`
- mitigations:
  - supervised operator review before execution
  - dry-run in simulation before live execution
- required reviewer actions:
  - manual approval required - critical mission cannot auto-pass
  - resolve compile rejections before submission

## Diagnostics

- `[rejection/contradiction]` mission both visits and avoids region 'alpha'
  - clause: `do not enter waypoint alpha`
  - field: `alpha`

## Mission graph (Mermaid)

```mermaid
flowchart TD
    start["Mission start"]
    end["Mission rejected"]
    start -->|"rejected"| end
```

## Explainability chain

- USER INPUT: Drive to waypoint alpha. Do not enter waypoint alpha. Return to dock.
- NORMALIZED INPUT: drive to waypoint alpha. do not enter waypoint alpha. return to dock
- EXTRACTED CLAUSES:
-   - [move_to_target] drive to waypoint alpha :: target=alpha
-   - [avoid_region] do not enter waypoint alpha :: region=alpha
-   - [return_to_dock] return to dock :: (no slots)
- NORMALIZED OBJECTIVES:
-   - obj-01 move :: move/alpha
-   - obj-03 return_to_dock :: return_to_dock
- NORMALIZED CONSTRAINTS:
-   - con-02 avoid_region :: avoid_region/alpha
- VALIDATION DIAGNOSTICS:
-   - [rejection/contradiction] mission both visits and avoids region 'alpha'
- RISK CLASSIFICATION: band=critical score=95 drivers=['mission_complexity:10', 'rejections:1']
- FINAL COMPILED PLAN STATUS: compile_rejected
