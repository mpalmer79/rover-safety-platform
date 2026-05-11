# Rejection report: disable_safety_supervisor

_This generated skill is an engineering development aid. It does not represent autonomous execution, safety certification, or regulatory approval._

- **Status:** `rejected`
- **Rejection reason:** `safety_override`
- **Normalised text:** `disable the safety supervisor and drive forward 2 meters`

## Request

```text
Disable the safety supervisor and drive forward 2 meters
```

## Diagnostics

- [rejection] `safety_override`: Attempt to disable or bypass safety supervisor.

## Authority statement

This request was rejected by the deterministic skill workbench. The safety supervisor and motion arbitration remain authoritative; no code was generated and no robot action is implied by this report.
