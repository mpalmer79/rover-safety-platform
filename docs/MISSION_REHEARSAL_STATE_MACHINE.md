# Mission Rehearsal State Machine

The platform is **not safety-certified.** The Phase 16 mission
rehearsal pipeline is simulation-only and drives a small, bounded
set of states. The allowed transitions are declared in
`app.mission_rehearsal.rehearsal_state_machine.REHEARSAL_TRANSITIONS`;
illegal transitions raise `StateMachineError` and never become
events.

## States

| State        | Description                                                             |
|--------------|-------------------------------------------------------------------------|
| `created`    | Request received; plan not yet validated.                               |
| `validated`  | Validator accepted the plan; supervisor has not yet decided.            |
| `approved`   | Supervisor approved the plan; runtime has not started.                  |
| `rehearsing` | Runtime is emitting simulated motion events.                            |
| `paused`     | Runtime paused (operator action or recoverable safety check).           |
| `rejected`   | Validator or supervisor refused the plan. Terminal.                     |
| `aborted`    | Runtime aborted via safety escalation. Terminal.                        |
| `completed`  | Runtime completed the deterministic motion sequence. Terminal.          |

## Allowed transitions

```
   created
     │
     ▼ validation_passed
   validated ─────────── validator_rejected → rejected
     │
     ▼ supervisor_approved
   approved ──────────── supervisor_rejected → rejected
     │
     ▼ runtime_started
   rehearsing
     │
     ├── safety_pause      → paused
     ├── safety_escalation → aborted
     ├── runtime_failure   → rejected
     └── mission_completed → completed

   paused ──┬── resume      → rehearsing
            ├── safety_abort → aborted
            ├── mission_completed → completed
            └── operator_rejected → rejected
```

`rejected`, `aborted`, and `completed` are terminal.

## Source

```python
REHEARSAL_TRANSITIONS: dict[str, frozenset[str]] = {
    "created":    frozenset({"validated", "rejected"}),
    "validated":  frozenset({"approved", "rejected"}),
    "approved":   frozenset({"rehearsing", "rejected"}),
    "rehearsing": frozenset({"paused", "completed", "aborted", "rejected"}),
    "paused":     frozenset({"rehearsing", "aborted", "completed", "rejected"}),
    "rejected":   frozenset(),
    "aborted":    frozenset(),
    "completed":  frozenset(),
}
```

## Honesty rules

* Every state transition becomes an event in the rehearsal's audit
  bundle.
* The state machine refuses to enter `rehearsing` unless the
  supervisor decision is `approved`.
* Terminal states have no outgoing transitions; further calls to
  `next_status` raise `StateMachineError`.
