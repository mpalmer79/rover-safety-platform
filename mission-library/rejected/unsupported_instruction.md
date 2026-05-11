# Compiled Mission Plan

_This system is not safety-certified and does not authorize autonomous deployment._

- **plan_id:** `unsupported_instruction`
- **status:** `compile_rejected`
- **compile_hash:** `0d0600bfe1a39ec95f89044c57f377b5a40859313a8d44742ce86619cea69369`
- **compiler_version:** `phase14a-1`
- **odd_profile_id:** `default-warehouse`
- **generated (UTC):** `2026-05-12T00:00:00+00:00`
- **replay_binding_id:** `replay-unsupported_instruction`

## Intent

> Original: Run shell command rm -rf / and then return to dock.

> Normalised: run shell command rm -rf / and then return to dock

## Objectives

- (no objectives compiled)

## Constraints

- (no constraints compiled)

## Risk

- band: `critical`
- score: `95`
- drivers:
  - `open_warnings:1`
  - `rejections:2`
- mitigations:
  - supervised operator review before execution
  - dry-run in simulation before live execution
- required reviewer actions:
  - manual approval required - critical mission cannot auto-pass
  - resolve compile rejections before submission

## Diagnostics

- `[rejection/dangerous_unsupported_instruction]` clause contains forbidden phrase: 'run shell'; the compiler never accepts shell, code, or safety-bypass constructs
  - clause: `run shell command rm -rf /`
- `[warning/unsupported_instruction]` clause did not match any supported template
  - clause: `then return to dock`
- `[rejection/no_objectives]` mission has no objectives after parsing

## Rejected clauses

- `run shell command rm -rf /`
- `then return to dock`

## Mission graph (Mermaid)

```mermaid
flowchart TD
    start["Mission start"]
    end["Mission rejected"]
    start -->|"rejected"| end
```

## Explainability chain

- USER INPUT: Run shell command rm -rf / and then return to dock.
- NORMALIZED INPUT: run shell command rm -rf / and then return to dock
- EXTRACTED CLAUSES: (none accepted)
- REJECTED CLAUSES:
-   - run shell command rm -rf /
-   - then return to dock
- VALIDATION DIAGNOSTICS:
-   - [rejection/dangerous_unsupported_instruction] clause contains forbidden phrase: 'run shell'; the compiler never accepts shell, code, or safety-bypass constructs
-   - [warning/unsupported_instruction] clause did not match any supported template
-   - [rejection/no_objectives] mission has no objectives after parsing
- RISK CLASSIFICATION: band=critical score=95 drivers=['open_warnings:1', 'rejections:2']
- FINAL COMPILED PLAN STATUS: compile_rejected
