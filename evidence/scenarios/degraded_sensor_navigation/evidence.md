# Scenario evidence — `degraded_sensor_navigation`

- **Status:** `passed`
- **Description:** Mission completes despite ACTIVE_DEGRADED supervisor state.
- **Requirements covered:** `REQ-MISSION-001`, `REQ-FAULT-001`
- **Run directory:** `runs/verify/verify-degraded_sensor_navigation`

## Expected vs observed

| | Expected | Observed |
|---|---|---|
| Safety state | `ACTIVE_DEGRADED` | `ACTIVE_DEGRADED` |
| Mission state | `MISSION_COMPLETE` | `MISSION_COMPLETE` |
| Fired faults | `f-imu-bias` | `f-imu-bias` |

## Checks

| Check | Status | Detail |
|---|---|---|
| `execution` | `passed` | engine completed; events=323 |
| `safety_state` | `passed` | final=ACTIVE_DEGRADED |
| `mission_state` | `passed` | final=MISSION_COMPLETE |
| `required_events` | `passed` | all 2 present |
| `fired_faults` | `passed` | observed ('f-imu-bias',) |
| `command_path_audit` | `passed` | commands=180 clamped=2 zeroed=2 expired=126 |
| `safety_transition_audit` | `passed` | transitions=3 final=ACTIVE_DEGRADED |
| `replay_integrity` | `passed` | events=323 transitions=3 mission_states=3 |
