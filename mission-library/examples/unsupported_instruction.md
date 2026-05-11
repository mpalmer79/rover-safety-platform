# Example: unsupported_instruction

_Forbidden construct; the compiler rejects it as dangerous._

- Expected status: `compile_rejected`
- Actual status: `compile_rejected`
- Risk: `critical` (score `95`)
- Objectives: 0
- Constraints: 0
- Diagnostics: 3

## Intent

> Run shell command rm -rf / and then return to dock.

## Files

- plan json: `mission-library/rejected/unsupported_instruction.json`
- plan md:   `mission-library/rejected/unsupported_instruction.md`
- audit:     `mission-library/audits/unsupported_instruction-audit.json`
- replay:    `mission-library/rejected/unsupported_instruction-replay-binding.json`
