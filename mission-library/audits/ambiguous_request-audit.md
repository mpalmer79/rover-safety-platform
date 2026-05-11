# Mission Compile Audit

_This system is not safety-certified and does not authorize autonomous deployment._

- **plan_id:** `ambiguous_request`
- **compile_hash:** `f42ffd207e169e775cbec5a4e8cdffcc654120039bcf0c6c3b442c16d58b450f`
- **compiler_version:** `phase14a-1`
- **odd_profile_id:** `default-warehouse`
- **status:** `compile_rejected`
- **generated (UTC):** `2026-05-12T00:00:00+00:00`

## Original intent

> Go somewhere near the loading area and check it out.

## Normalised intent

> go somewhere near the loading area and check it out

## Risk: `critical` (score `95`)

- driver: `open_warnings:2`
- driver: `rejections:1`

## Rejected instructions

- `go somewhere near the loading area`
- `check it out`

## Validation diagnostics

- `[warning/ambiguous_clause]` clause is ambiguous and was not converted to an objective: matched phrase 'somewhere near'
- `[warning/unsupported_instruction]` clause did not match any supported template
- `[rejection/no_objectives]` mission has no objectives after parsing

## Replay compatibility

- runtime_executed: `false`
- binding_id: `replay-ambiguous_request`
