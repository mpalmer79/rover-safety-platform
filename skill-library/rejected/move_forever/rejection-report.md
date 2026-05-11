# Rejection report: move_forever

_This generated skill is an engineering development aid. It does not represent autonomous execution, safety certification, or regulatory approval._

- **Status:** `rejected`
- **Rejection reason:** `unbounded_motion`
- **Normalised text:** `drive forward forever`

## Request

```text
Drive forward forever
```

## Diagnostics

- [rejection] `unbounded_motion`: Unbounded motion request; every motion must be duration-bounded.

## Authority statement

This request was rejected by the deterministic skill workbench. The safety supervisor and motion arbitration remain authoritative; no code was generated and no robot action is implied by this report.
