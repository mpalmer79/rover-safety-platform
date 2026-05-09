# Scenario evidence — `command_timeout_safe_stop`

- **Status:** `passed`
- **Description:** Hardware gateway silent; SAFE_STOP via gateway watchdog.
- **Requirements covered:** `REQ-SAFE-001`, `REQ-SAFE-002`, `REQ-FAULT-001`, `REQ-FAULT-002`
- **Run directory:** `runs/verify/verify-command_timeout_safe_stop`

## Expected vs observed

| | Expected | Observed |
|---|---|---|
| Safety state | `SAFE_STOP` | `SAFE_STOP` |
| Fired faults | `f-cmd-timeout` | `f-cmd-timeout` |

## Checks

| Check | Status | Detail |
|---|---|---|
| `execution` | `passed` | engine completed; events=119 |
| `safety_state` | `passed` | final=SAFE_STOP |
| `required_events` | `passed` | all 3 present |
| `fired_faults` | `passed` | observed ('f-cmd-timeout',) |
| `command_path_audit` | `passed` | commands=80 clamped=0 zeroed=57 expired=0 |
| `safety_transition_audit` | `passed` | transitions=3 final=SAFE_STOP |
| `replay_integrity` | `passed` | events=119 transitions=3 mission_states=0 |
| `safe_stop_zero_motion` | `passed` | all safe-stop / e-stop commands zero |
