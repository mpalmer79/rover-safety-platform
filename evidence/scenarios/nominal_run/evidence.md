# Scenario evidence — `nominal_run`

- **Status:** `passed`
- **Description:** Healthy nominal run; supervisor reaches ACTIVE_NORMAL.
- **Requirements covered:** `REQ-SAFE-001`, `REQ-REPLAY-001`
- **Run directory:** `runs/verify/verify-nominal_run`

## Expected vs observed

| | Expected | Observed |
|---|---|---|
| Safety state | `ACTIVE_NORMAL` | `ACTIVE_NORMAL` |

## Checks

| Check | Status | Detail |
|---|---|---|
| `execution` | `passed` | engine completed; events=6 |
| `safety_state` | `passed` | final=ACTIVE_NORMAL |
| `required_events` | `passed` | all 2 present |
| `forbidden_events` | `passed` | all 1 absent |
| `command_path_audit` | `passed` | commands=80 clamped=0 zeroed=2 expired=0 |
| `safety_transition_audit` | `passed` | transitions=2 final=ACTIVE_NORMAL |
| `replay_integrity` | `passed` | events=6 transitions=2 mission_states=0 |
