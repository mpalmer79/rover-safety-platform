# Scenario evidence — `nominal_waypoint_patrol`

- **Status:** `passed`
- **Description:** Three-waypoint patrol; mission completes cleanly.
- **Requirements covered:** `REQ-SAFE-001`, `REQ-MISSION-001`, `REQ-REPLAY-001`
- **Run directory:** `runs/verify/verify-nominal_waypoint_patrol`

## Expected vs observed

| | Expected | Observed |
|---|---|---|
| Safety state | `ACTIVE_NORMAL` | `ACTIVE_NORMAL` |
| Mission state | `MISSION_COMPLETE` | `MISSION_COMPLETE` |

## Checks

| Check | Status | Detail |
|---|---|---|
| `execution` | `passed` | engine completed; events=318 |
| `safety_state` | `passed` | final=ACTIVE_NORMAL |
| `mission_state` | `passed` | final=MISSION_COMPLETE |
| `required_events` | `passed` | all 2 present |
| `forbidden_events` | `passed` | all 1 absent |
| `command_path_audit` | `passed` | commands=300 clamped=0 zeroed=2 expired=4 |
| `safety_transition_audit` | `passed` | transitions=2 final=ACTIVE_NORMAL |
| `replay_integrity` | `passed` | events=318 transitions=2 mission_states=3 |
