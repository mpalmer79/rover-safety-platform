# Compiled Mission Plan

_This system is not safety-certified and does not authorize autonomous deployment._

- **plan_id:** `restricted_zone_rejected`
- **status:** `compile_rejected`
- **compile_hash:** `720396c6ef15bd8d5c29294ff718c4df105615adb0c432b5e631e16443e88f95`
- **compiler_version:** `phase14a-1`
- **odd_profile_id:** `default-warehouse`
- **generated (UTC):** `2026-05-12T00:00:00+00:00`
- **replay_binding_id:** `replay-restricted_zone_rejected`

## Intent

> Original: Drive to restricted_corridor_one.

> Normalised: drive to restricted_corridor_one

## Objectives

- **obj-01** (move): move/restricted_corridor_one  
  - parameters: target=`restricted_corridor_one`  
  - source clause: `drive to restricted_corridor_one`

## Constraints

- (no constraints compiled)

## Risk

- band: `critical`
- score: `95`
- drivers:
  - `rejections:1`
- mitigations:
  - supervised operator review before execution
  - dry-run in simulation before live execution
- required reviewer actions:
  - manual approval required - critical mission cannot auto-pass
  - resolve compile rejections before submission

## Diagnostics

- `[rejection/odd_violation]` objective targets prohibited region 'restricted_corridor_one' for ODD profile 'default-warehouse'
  - clause: `drive to restricted_corridor_one`
  - field: `region`

## Mission graph (Mermaid)

```mermaid
flowchart TD
    start["Mission start"]
    end["Mission rejected"]
    start -->|"rejected"| end
```

## Explainability chain

- USER INPUT: Drive to restricted_corridor_one.
- NORMALIZED INPUT: drive to restricted_corridor_one
- EXTRACTED CLAUSES:
-   - [move_to_target] drive to restricted_corridor_one :: target=restricted_corridor_one
- NORMALIZED OBJECTIVES:
-   - obj-01 move :: move/restricted_corridor_one
- VALIDATION DIAGNOSTICS:
-   - [rejection/odd_violation] objective targets prohibited region 'restricted_corridor_one' for ODD profile 'default-warehouse'
- RISK CLASSIFICATION: band=critical score=95 drivers=['rejections:1']
- FINAL COMPILED PLAN STATUS: compile_rejected
