# Rejection report: spin_motors_directly

_This generated skill is an engineering development aid. It does not represent autonomous execution, safety certification, or regulatory approval._

- **Status:** `rejected`
- **Rejection reason:** `direct_motor_control`
- **Normalised text:** `spin the motors directly to drive forward`

## Request

```text
Spin the motors directly to drive forward
```

## Diagnostics

- [rejection] `direct_motor_control`: Direct motor control is out of scope; use /cmd_vel_requested only.

## Authority statement

This request was rejected by the deterministic skill workbench. The safety supervisor and motion arbitration remain authoritative; no code was generated and no robot action is implied by this report.
