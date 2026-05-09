# Scenario evidence — `waypoint_timeout_recovery`

- **Status:** `passed`
- **Description:** Unreachable waypoint; recovery exhausts budget; MISSION_ABORTED.
- **Requirements covered:** `REQ-MISSION-001`, `REQ-MISSION-002`
- **Run directory:** `runs/verify/verify-waypoint_timeout_recovery`

## Expected vs observed

| | Expected | Observed |
|---|---|---|
| Safety state | `ACTIVE_NORMAL` | `ACTIVE_NORMAL` |
| Mission state | `MISSION_ABORTED` | `MISSION_ABORTED` |
| Recovery engagements | ≥ 2 | 4 |

## Checks

| Check | Status | Detail |
|---|---|---|
| `execution` | `passed` | engine completed; events=369 |
| `safety_state` | `passed` | final=ACTIVE_NORMAL |
| `mission_state` | `passed` | final=MISSION_ABORTED |
| `required_events` | `passed` | all 2 present |
| `recovery_engagements` | `passed` | observed 4; expected at least 2 |
| `command_path_audit` | `passed` | commands=250 clamped=0 zeroed=2 expired=98 |
| `safety_transition_audit` | `passed` | transitions=2 final=ACTIVE_NORMAL |
| `replay_integrity` | `passed` | events=369 transitions=2 mission_states=8 |
