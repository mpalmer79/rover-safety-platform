# Compiled Mission Plan

_This system is not safety-certified and does not authorize autonomous deployment._

- **plan_id:** `ambiguous_request`
- **status:** `compile_rejected`
- **compile_hash:** `f42ffd207e169e775cbec5a4e8cdffcc654120039bcf0c6c3b442c16d58b450f`
- **compiler_version:** `phase14a-1`
- **odd_profile_id:** `default-warehouse`
- **generated (UTC):** `2026-05-12T00:00:00+00:00`
- **replay_binding_id:** `replay-ambiguous_request`

## Intent

> Original: Go somewhere near the loading area and check it out.

> Normalised: go somewhere near the loading area and check it out

## Objectives

- (no objectives compiled)

## Constraints

- (no constraints compiled)

## Risk

- band: `critical`
- score: `95`
- drivers:
  - `open_warnings:2`
  - `rejections:1`
- mitigations:
  - supervised operator review before execution
  - dry-run in simulation before live execution
- required reviewer actions:
  - manual approval required - critical mission cannot auto-pass
  - resolve compile rejections before submission

## Diagnostics

- `[warning/ambiguous_clause]` clause is ambiguous and was not converted to an objective: matched phrase 'somewhere near'
  - clause: `go somewhere near the loading area`
- `[warning/unsupported_instruction]` clause did not match any supported template
  - clause: `check it out`
- `[rejection/no_objectives]` mission has no objectives after parsing

## Rejected clauses

- `go somewhere near the loading area`
- `check it out`

## Mission graph (Mermaid)

```mermaid
flowchart TD
    start["Mission start"]
    end["Mission rejected"]
    start -->|"rejected"| end
```

## Explainability chain

- USER INPUT: Go somewhere near the loading area and check it out.
- NORMALIZED INPUT: go somewhere near the loading area and check it out
- EXTRACTED CLAUSES: (none accepted)
- REJECTED CLAUSES:
-   - go somewhere near the loading area
-   - check it out
- VALIDATION DIAGNOSTICS:
-   - [warning/ambiguous_clause] clause is ambiguous and was not converted to an objective: matched phrase 'somewhere near'
-   - [warning/unsupported_instruction] clause did not match any supported template
-   - [rejection/no_objectives] mission has no objectives after parsing
- RISK CLASSIFICATION: band=critical score=95 drivers=['open_warnings:2', 'rejections:1']
- FINAL COMPILED PLAN STATUS: compile_rejected
