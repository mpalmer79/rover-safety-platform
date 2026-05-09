# Scenario evidence — `keepout_zone_violation`

- **Status:** `passed`
- **Description:** Keepout violation triggers SAFE_STOP_ESCALATION recovery.
- **Requirements covered:** `REQ-MISSION-001`, `REQ-WORLD-001`
- **Run directory:** `/tmp/p3-final-runs/verify-keepout_zone_violation`

## Expected vs observed

| | Expected | Observed |
|---|---|---|
| Safety state | `ACTIVE_NORMAL` | `ACTIVE_NORMAL` |
| Mission state | `MISSION_DEGRADED` | `MISSION_DEGRADED` |

## Checks

| Check | Status | Detail |
|---|---|---|
| `execution` | `passed` | engine completed; events=235 |
| `safety_state` | `passed` | final=ACTIVE_NORMAL |
| `mission_state` | `passed` | final=MISSION_DEGRADED |
| `required_events` | `passed` | all 3 present |
| `command_path_audit` | `passed` | commands=120 clamped=0 zeroed=2 expired=1 |
| `safety_transition_audit` | `passed` | transitions=2 final=ACTIVE_NORMAL |
| `replay_integrity` | `passed` | events=235 transitions=2 mission_states=3 |
