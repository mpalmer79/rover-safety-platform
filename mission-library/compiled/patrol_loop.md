# Compiled Mission Plan

_This system is not safety-certified and does not authorize autonomous deployment._

- **plan_id:** `patrol_loop`
- **status:** `compile_ok`
- **compile_hash:** `9ec6bfbe652020e9c6d91e01c9c18209fd5420d662c71b738e392c98a024f793`
- **compiler_version:** `phase14a-1`
- **odd_profile_id:** `default-warehouse`
- **generated (UTC):** `2026-05-12T00:00:00+00:00`
- **replay_binding_id:** `replay-patrol_loop`

## Intent

> Original: Patrol patrol_loop_a. Pause at checkpoint bravo. Return to dock.

> Normalised: patrol patrol_loop_a. pause at checkpoint bravo. return to dock

## Objectives

- **obj-01** (patrol): patrol/patrol_loop_a  
  - parameters: zone=`patrol_loop_a`  
  - source clause: `patrol patrol_loop_a`
- **obj-02** (pause): pause/bravo  
  - parameters: target=`bravo`  
  - source clause: `pause at checkpoint bravo`
- **obj-03** (return_to_dock): return_to_dock  
  - parameters: (none)  
  - source clause: `return to dock`

## Constraints

- (no constraints compiled)

## Risk

- band: `moderate`
- score: `35`
- drivers:
  - `mission_complexity:20`
  - `extended_autonomy_stages:1`

## Mission graph (Mermaid)

```mermaid
flowchart TD
    start["Mission start"]
    n_01["patrol/patrol_loop_a"]
    n_02["pause/bravo"]
    n_03["return_to_dock"]
    end["Mission end"]
    start --> n_01
    n_01 --> n_02
    n_02 --> n_03
    n_03 --> end
```

## Explainability chain

- USER INPUT: Patrol patrol_loop_a. Pause at checkpoint bravo. Return to dock.
- NORMALIZED INPUT: patrol patrol_loop_a. pause at checkpoint bravo. return to dock
- EXTRACTED CLAUSES:
-   - [patrol_area] patrol patrol_loop_a :: zone=patrol_loop_a
-   - [pause_at_checkpoint] pause at checkpoint bravo :: target=bravo
-   - [return_to_dock] return to dock :: (no slots)
- NORMALIZED OBJECTIVES:
-   - obj-01 patrol :: patrol/patrol_loop_a
-   - obj-02 pause :: pause/bravo
-   - obj-03 return_to_dock :: return_to_dock
- VALIDATION DIAGNOSTICS: (none)
- RISK CLASSIFICATION: band=moderate score=35 drivers=['mission_complexity:20', 'extended_autonomy_stages:1']
- FINAL COMPILED PLAN STATUS: compile_ok
