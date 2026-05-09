# Scenario evidence — `estop_latched_manual_reset_required`

- **Status:** `passed`
- **Description:** Operator E-stop latches and does not self-clear.
- **Requirements covered:** `REQ-SAFE-003`, `REQ-OP-001`
- **Run directory:** `/tmp/p3-final-runs/verify-estop_latched_manual_reset_required`

## Expected vs observed

| | Expected | Observed |
|---|---|---|
| Safety state | `E_STOP_LATCHED` | `E_STOP_LATCHED` |

## Checks

| Check | Status | Detail |
|---|---|---|
| `execution` | `passed` | engine completed; events=52 |
| `safety_state` | `passed` | final=E_STOP_LATCHED |
| `required_events` | `passed` | all 1 present |
| `command_path_audit` | `passed` | commands=60 clamped=0 zeroed=47 expired=0 |
| `safety_transition_audit` | `passed` | transitions=3 final=E_STOP_LATCHED |
| `replay_integrity` | `passed` | events=52 transitions=3 mission_states=0 |
| `safe_stop_zero_motion` | `passed` | all safe-stop / e-stop commands zero |
