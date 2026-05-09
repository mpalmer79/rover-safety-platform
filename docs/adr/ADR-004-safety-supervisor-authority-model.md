# ADR-004: Safety Supervisor Authority Model

## Status
Accepted

## Context

The platform's central thesis is that autonomy must remain inspectable, bounded, replayable, and operationally explainable under degraded conditions. That thesis collapses if any subsystem other than a designated safety authority can authorize motion.

The decision is therefore not whether to have a safety supervisor — the architecture demands one — but where authority for motion authorization lives, who can request motion, who can clamp it, and who can write to the actuator interface.

Common alternatives in robotics codebases:

- The planner directly publishes velocity commands consumed by motor controllers.
- Safety is a layer of decorators applied to mission code.
- Multiple subsystems share authority through a consensus or voting mechanism.

Each of these has trade-offs that conflict with the platform's deterministic and replay-oriented goals.

The platform must, by design, make it architecturally impossible for the mission layer to bypass the safety supervisor. Convention and review are insufficient.

## Decision

The platform adopts a **single-authority safety supervisor model**.

The essential rules:

1. **The safety supervisor owns final motion authorization.** It is the only subsystem that publishes `/cmd_vel_authorized`.
2. **The mission layer cannot write actuator commands.** The mission layer publishes only `/cmd_vel_requested`. The hardware gateway has no subscription to this topic.
3. **The hardware gateway accepts only authorized commands.** It subscribes only to `/cmd_vel_authorized`. It enforces an independent command timeout that decays motion to zero in the absence of authorized commands.
4. **Fault injection cannot directly set safety state.** The fault subsystem alters inputs and timing; the supervisor reacts to those inputs through normal mechanisms.
5. **Safety transitions must emit events.** Every state transition produces a `safety_transition.entered` event conforming to `docs/EVENT_MODEL.md`. State transitions without events are invalid.
6. **`ACTIVE_DEGRADED` and `SAFE_STOP` are enforced centrally.** The supervisor is the only authority that decides these states. Mission, planner, and gateway subsystems must not implement parallel degraded or safe-stop logic.

The supervisor's responsibilities, restrictions, and watchdog and freshness model are defined in `docs/SAFETY_MODEL.md`. This ADR locks in the authority model itself.

## Consequences

### Positive

- The mission layer is structurally incapable of bypassing safety arbitration.
- Reasoning about a recorded run reduces to inspecting the supervisor's state transitions and arbitration events.
- Replay analysis is tractable: one canonical authority, one canonical state machine, one canonical event vocabulary for safety transitions.
- Adding new mission behavior cannot, by construction, expand motion authority.
- Adding new fault classes cannot, by construction, mutate safety state.

### Negative

- The supervisor is a critical path. Bugs in the supervisor have outsized impact, and the supervisor must be tested with the rigor described in `docs/TESTING_STRATEGY.md`.
- The supervisor must publish `/cmd_vel_authorized` at the configured rate even in `SAFE_STOP` and `E_STOP_LATCHED`. Operationally cheap, architecturally required.
- A supervisor outage is treated as a serious fault, not a degraded operating mode. The hardware gateway's independent command timeout is the secondary safeguard.

### Neutral

- The `/cmd_vel_requested` versus `/cmd_vel_authorized` separation imposes a small but visible amount of topic plumbing. The visibility is the point; it is the architectural enforcement of the model.

## Alternatives Considered

| Alternative | Reason rejected |
|---|---|
| Planner-direct actuator control | Couples mission and motion authority. Bypassing safety becomes a function of code paths instead of architecture. Does not scale to fault-driven validation. |
| Distributed safety decisions across multiple subsystems | Replay becomes intractable: which subsystem caused the transition? Consensus or voting introduces nondeterminism without architectural benefit at the platform's scale. |
| Mission-owned safety transitions | Allows the mission to relax restrictions when convenient. Defeats the purpose of bounded autonomy and degraded-mode containment. |
| Decorators or middleware filters around mission outputs | Effective in some codebases, but invisible to topic-level inspection. Replay analysts cannot easily see the boundary. The platform prefers explicit topic separation. |

## Follow-up Work

- Implement contract tests asserting that no subsystem other than the supervisor publishes to `/cmd_vel_authorized` (see `docs/TESTING_STRATEGY.md` section 13.5).
- Implement contract tests asserting that the hardware gateway has no subscription to `/cmd_vel_requested`.
- Implement negative tests asserting that fault injection cannot set `/safety/state` (see `docs/TESTING_STRATEGY.md` section 13.4).
- Document operator pathways for activation, E-stop, and reset in the supervisor's interface specification.
- Track supervisor performance characteristics (publication rate, jitter) in run metadata starting in Phase 3.
