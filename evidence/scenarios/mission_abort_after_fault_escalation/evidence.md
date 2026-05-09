# Scenario evidence — `mission_abort_after_fault_escalation`

- **Status:** `passed`
- **Description:** Repeated waypoint timeouts; mission aborts after exhausting budget.
- **Requirements covered:** `REQ-MISSION-002`
- **Run directory:** `/tmp/p3-final-runs/verify-mission_abort_after_fault_escalation`

## Expected vs observed

| | Expected | Observed |
|---|---|---|
| Safety state | `ACTIVE_NORMAL` | `ACTIVE_NORMAL` |
| Mission state | `MISSION_ABORTED` | `MISSION_ABORTED` |
| Recovery engagements | ≥ 3 | 5 |

## Checks

| Check | Status | Detail |
|---|---|---|
| `execution` | `passed` | engine completed; events=358 |
| `safety_state` | `passed` | final=ACTIVE_NORMAL |
| `mission_state` | `passed` | final=MISSION_ABORTED |
| `required_events` | `passed` | all 2 present |
| `recovery_engagements` | `passed` | observed 5; expected at least 3 |
| `command_path_audit` | `passed` | commands=250 clamped=0 zeroed=2 expired=83 |
| `safety_transition_audit` | `passed` | transitions=2 final=ACTIVE_NORMAL |
| `replay_integrity` | `passed` | events=358 transitions=2 mission_states=10 |
