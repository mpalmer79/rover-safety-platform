# Scenario evidence — `safe_stop_during_active_mission`

- **Status:** `passed`
- **Description:** Mid-mission LiDAR drop drives SAFE_STOP + MISSION_DEGRADED.
- **Requirements covered:** `REQ-SAFE-002`, `REQ-MISSION-001`, `REQ-FAULT-001`
- **Run directory:** `/tmp/p3-final-runs/verify-safe_stop_during_active_mission`

## Expected vs observed

| | Expected | Observed |
|---|---|---|
| Safety state | `SAFE_STOP` | `SAFE_STOP` |
| Mission state | `MISSION_DEGRADED` | `MISSION_DEGRADED` |
| Fired faults | `f-stale-lidar` | `f-stale-lidar` |

## Checks

| Check | Status | Detail |
|---|---|---|
| `execution` | `passed` | engine completed; events=479 |
| `safety_state` | `passed` | final=SAFE_STOP |
| `mission_state` | `passed` | final=MISSION_DEGRADED |
| `required_events` | `passed` | all 3 present |
| `fired_faults` | `passed` | observed ('f-stale-lidar',) |
| `command_path_audit` | `passed` | commands=150 clamped=5 zeroed=105 expired=1 |
| `safety_transition_audit` | `passed` | transitions=4 final=SAFE_STOP |
| `replay_integrity` | `passed` | events=479 transitions=4 mission_states=3 |
| `safe_stop_zero_motion` | `passed` | all safe-stop / e-stop commands zero |
