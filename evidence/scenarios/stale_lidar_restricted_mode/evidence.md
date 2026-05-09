# Scenario evidence — `stale_lidar_restricted_mode`

- **Status:** `passed`
- **Description:** LiDAR drop forces SAFE_STOP through freshness gates.
- **Requirements covered:** `REQ-SAFE-001`, `REQ-SAFE-002`, `REQ-FAULT-001`, `REQ-FAULT-002`
- **Run directory:** `runs/verify/verify-stale_lidar_restricted_mode`

## Expected vs observed

| | Expected | Observed |
|---|---|---|
| Safety state | `SAFE_STOP` | `SAFE_STOP` |
| Fired faults | `f-stale-lidar` | `f-stale-lidar` |

## Checks

| Check | Status | Detail |
|---|---|---|
| `execution` | `passed` | engine completed; events=172 |
| `safety_state` | `passed` | final=SAFE_STOP |
| `required_events` | `passed` | all 3 present |
| `fired_faults` | `passed` | observed ('f-stale-lidar',) |
| `command_path_audit` | `passed` | commands=80 clamped=5 zeroed=55 expired=0 |
| `safety_transition_audit` | `passed` | transitions=4 final=SAFE_STOP |
| `replay_integrity` | `passed` | events=172 transitions=4 mission_states=0 |
| `safe_stop_zero_motion` | `passed` | all safe-stop / e-stop commands zero |
