# Scenario evidence — `bridge_disconnect_safe_stop`

- **Status:** `passed`
- **Description:** Bridge disconnect; multi-stream freshness violation.
- **Requirements covered:** `REQ-SAFE-001`, `REQ-SAFE-002`, `REQ-FAULT-001`, `REQ-FAULT-002`
- **Run directory:** `runs/verify/verify-bridge_disconnect_safe_stop`

## Expected vs observed

| | Expected | Observed |
|---|---|---|
| Safety state | `SAFE_STOP` | `SAFE_STOP` |
| Fired faults | `f-bridge` | `f-bridge` |

## Checks

| Check | Status | Detail |
|---|---|---|
| `execution` | `passed` | engine completed; events=384 |
| `safety_state` | `passed` | final=SAFE_STOP |
| `required_events` | `passed` | all 2 present |
| `fired_faults` | `passed` | observed ('f-bridge',) |
| `command_path_audit` | `passed` | commands=80 clamped=4 zeroed=56 expired=0 |
| `safety_transition_audit` | `passed` | transitions=4 final=SAFE_STOP |
| `replay_integrity` | `passed` | events=384 transitions=4 mission_states=0 |
| `safe_stop_zero_motion` | `passed` | all safe-stop / e-stop commands zero |
