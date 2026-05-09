# Scenario evidence — `wheel_slip_degraded_mode`

- **Status:** `passed`
- **Description:** Rough-terrain slip + IMU bias; ACTIVE_DEGRADED.
- **Requirements covered:** `REQ-SAFE-001`, `REQ-FAULT-001`, `REQ-FAULT-002`
- **Run directory:** `runs/verify/verify-wheel_slip_degraded_mode`

## Expected vs observed

| | Expected | Observed |
|---|---|---|
| Safety state | `ACTIVE_DEGRADED` | `ACTIVE_DEGRADED` |
| Fired faults | `f-imu-bias`, `f-slip` | `f-imu-bias`, `f-slip` |

## Checks

| Check | Status | Detail |
|---|---|---|
| `execution` | `passed` | engine completed; events=73 |
| `safety_state` | `passed` | final=ACTIVE_DEGRADED |
| `required_events` | `passed` | all 2 present |
| `fired_faults` | `passed` | observed ('f-imu-bias', 'f-slip') |
| `command_path_audit` | `passed` | commands=60 clamped=45 zeroed=2 expired=0 |
| `safety_transition_audit` | `passed` | transitions=3 final=ACTIVE_DEGRADED |
| `replay_integrity` | `passed` | events=73 transitions=3 mission_states=0 |
