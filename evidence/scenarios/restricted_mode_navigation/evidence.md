# Scenario evidence — `restricted_mode_navigation`

- **Status:** `passed`
- **Description:** Mission passes through a restricted-speed zone; clamped, completes.
- **Requirements covered:** `REQ-SAFE-004`, `REQ-MISSION-001`, `REQ-WORLD-001`
- **Run directory:** `/tmp/p3-final-runs/verify-restricted_mode_navigation`

## Expected vs observed

| | Expected | Observed |
|---|---|---|
| Safety state | `ACTIVE_NORMAL` | `ACTIVE_NORMAL` |
| Mission state | `MISSION_COMPLETE` | `MISSION_COMPLETE` |

## Checks

| Check | Status | Detail |
|---|---|---|
| `execution` | `passed` | engine completed; events=472 |
| `safety_state` | `passed` | final=ACTIVE_NORMAL |
| `mission_state` | `passed` | final=MISSION_COMPLETE |
| `required_events` | `passed` | all 1 present |
| `command_path_audit` | `passed` | commands=250 clamped=0 zeroed=2 expired=82 |
| `safety_transition_audit` | `passed` | transitions=2 final=ACTIVE_NORMAL |
| `replay_integrity` | `passed` | events=472 transitions=2 mission_states=3 |
