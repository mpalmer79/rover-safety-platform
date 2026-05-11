# Mission Compile Audit

_This system is not safety-certified and does not authorize autonomous deployment._

- **plan_id:** `unsupported_instruction`
- **compile_hash:** `0d0600bfe1a39ec95f89044c57f377b5a40859313a8d44742ce86619cea69369`
- **compiler_version:** `phase14a-1`
- **odd_profile_id:** `default-warehouse`
- **status:** `compile_rejected`
- **generated (UTC):** `2026-05-12T00:00:00+00:00`

## Original intent

> Run shell command rm -rf / and then return to dock.

## Normalised intent

> run shell command rm -rf / and then return to dock

## Risk: `critical` (score `95`)

- driver: `open_warnings:1`
- driver: `rejections:2`

## Rejected instructions

- `run shell command rm -rf /`
- `then return to dock`

## Validation diagnostics

- `[rejection/dangerous_unsupported_instruction]` clause contains forbidden phrase: 'run shell'; the compiler never accepts shell, code, or safety-bypass constructs
- `[warning/unsupported_instruction]` clause did not match any supported template
- `[rejection/no_objectives]` mission has no objectives after parsing

## Replay compatibility

- runtime_executed: `false`
- binding_id: `replay-unsupported_instruction`
