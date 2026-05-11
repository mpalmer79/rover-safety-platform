# Rejection report: execute_shell_command

_This generated skill is an engineering development aid. It does not represent autonomous execution, safety certification, or regulatory approval._

- **Status:** `rejected`
- **Rejection reason:** `shell_or_code_execution`
- **Normalised text:** `run shell command to start the rover`

## Request

```text
Run shell command to start the rover
```

## Diagnostics

- [rejection] `shell_or_code_execution`: Shell command requests are not supported.
- [rejection] `shell_or_code_execution`: Shell command execution is not supported.

## Authority statement

This request was rejected by the deterministic skill workbench. The safety supervisor and motion arbitration remain authoritative; no code was generated and no robot action is implied by this report.
