# Rejection report: publish_direct_cmd_vel

_This generated skill is an engineering development aid. It does not represent autonomous execution, safety certification, or regulatory approval._

- **Status:** `rejected`
- **Rejection reason:** `direct_actuator_command`
- **Normalised text:** `publish to /cmd_vel directly`

## Request

```text
Publish to /cmd_vel directly
```

## Diagnostics

- [rejection] `direct_actuator_command`: Direct actuator publication is forbidden; use /cmd_vel_requested.
- [rejection] `direct_actuator_command`: Direct actuator publication is forbidden; use /cmd_vel_requested.

## Authority statement

This request was rejected by the deterministic skill workbench. The safety supervisor and motion arbitration remain authoritative; no code was generated and no robot action is implied by this report.
