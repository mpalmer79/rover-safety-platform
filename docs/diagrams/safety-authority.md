# Safety Authority

The platform is **not safety-certified**. This diagram shows the
single-authority motion-command path that every actuator command in
the system must pass through.

```mermaid
flowchart LR
    op[Operator inputs<br/>e-stop / reset / mode] --> supervisor
    fresh[Freshness gates<br/>lidar / odom / cmd] --> supervisor
    wd[Watchdogs] --> supervisor
    conf[Confidence scoring] --> supervisor

    mission[Mission runtime] -->|requests<br/>motion| supervisor
    nav[Navigation / planner] -->|requests<br/>motion| supervisor

    supervisor((Safety supervisor<br/>state machine))

    supervisor -->|authorises<br/>motion| arb[Motion arbitration]
    arb -->|clamped &<br/>reason-coded| gw[Hardware gateway]

    supervisor -.->|safety-transition<br/>events| evt[(events.jsonl)]
    arb -.->|command-audit<br/>events| evt

    classDef authority stroke-width:3px;
    classDef forbidden fill:#ffe0e0,stroke:#cc0000,stroke-dasharray:4 2;
    class supervisor authority;

    bypass[Direct actuator<br/>path]:::forbidden
    bypass -. forbidden .-> gw
```

## Authority rules

1. **Only the supervisor authorises motion.** Mission, navigation,
   perception, and operator code may *request* motion. They cannot
   command the gateway directly.
2. **State-machine guards every authorisation.** Safety states are
   `ACTIVE_NORMAL`, `ACTIVE_DEGRADED`, `RESTRICTED`, `SAFE_STOP`,
   `E_STOP_LATCHED`, `RECOVERY`. Each transition is allowed-list
   checked and reason-coded.
3. **E-stop is latched.** Leaving `E_STOP_LATCHED` requires an
   explicit operator-acknowledged reset; nothing else can clear it.
4. **`SAFE_STOP` zeroes commands.** Authorised commands in
   `SAFE_STOP` are zero, period.
5. **`RESTRICTED` clamps velocity.** Authorised commands honour the
   restricted envelope, irrespective of what the requester asked
   for.
6. **Faults change inputs, not state.** Fault injection mutates
   sensor readings, command timeouts, bridge connectivity, or
   watchdog pets — never the state machine.

## How the rules are proven

| Rule | Proven by |
| --- | --- |
| Single authoriser | `tools/audit_command_path.py` (every authorised command has a paired prior request) |
| Allowed-list transitions | `tools/audit_safety_transitions.py` |
| `SAFE_STOP` zeroing | scenario `safe_stop_during_active_mission`, supervisor unit tests |
| E-stop latching | scenario `estop_latched_manual_reset_required` |
| `RESTRICTED` clamping | scenario `stale_lidar_restricted_mode` |
| Faults do not mutate state | absence of `SafetyState` writes in `backend/app/faults/`; supervisor unit tests under fault inputs |

## Related documents

- [`docs/SAFETY_MODEL.md`](../SAFETY_MODEL.md)
- [`docs/EVENT_MODEL.md`](../EVENT_MODEL.md)
- [`docs/FAULT_INJECTION.md`](../FAULT_INJECTION.md)
- [`ARCHITECTURE.md`](../../ARCHITECTURE.md)
- [`docs/diagrams/system-flow.md`](system-flow.md)
