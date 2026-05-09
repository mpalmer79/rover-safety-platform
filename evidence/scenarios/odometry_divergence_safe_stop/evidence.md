# Scenario evidence — `odometry_divergence_safe_stop`

- **Status:** `passed`
- **Description:** Encoder/IMU disagreement; ACTIVE_DEGRADED.
- **Requirements covered:** `REQ-SAFE-001`, `REQ-FAULT-001`, `REQ-FAULT-002`
- **Run directory:** `/tmp/p3-final-runs/verify-odometry_divergence_safe_stop`

## Expected vs observed

| | Expected | Observed |
|---|---|---|
| Safety state | `ACTIVE_DEGRADED` | `ACTIVE_DEGRADED` |
| Fired faults | `f-disagreement` | `f-disagreement` |

## Checks

| Check | Status | Detail |
|---|---|---|
| `execution` | `passed` | engine completed; events=74 |
| `safety_state` | `passed` | final=ACTIVE_DEGRADED |
| `required_events` | `passed` | all 2 present |
| `fired_faults` | `passed` | observed ('f-disagreement',) |
| `command_path_audit` | `passed` | commands=80 clamped=65 zeroed=2 expired=0 |
| `safety_transition_audit` | `passed` | transitions=3 final=ACTIVE_DEGRADED |
| `replay_integrity` | `passed` | events=74 transitions=3 mission_states=0 |
