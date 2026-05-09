# ADR-003: Simulation-First Strategy

## Status
Accepted

## Context

The platform is intended to validate deterministic autonomous rover behavior under degraded operational conditions. The validation surface must be repeatable, instrumented, and bounded. Hardware-first development on a single bench rover would compromise all three properties.

Constraints at decision time:

- The MVP is a portfolio platform, not a deployed product. Schedule and cost must be calibrated accordingly.
- Safety-relevant behavior must be exercised against fault scenarios that are unsafe to recreate physically (e.g., wheel slip on hardware, watchdog expirations during motion).
- Replay is a platform requirement; reproducible scenarios are the primary input to replay.
- Hardware integration is committed for Phase 5 onward, but the architecture must be validated first.

Alternatives considered:

- Hardware-first: prioritize bench hardware before autonomy is well-formed. Common in hobby projects, unsuitable here.
- Hybrid-first: develop simulation and hardware in lockstep from day one. High coordination cost; tends to produce two half-built systems.
- Perception-first: build a camera-driven stack first and back into safety. Misaligned with the platform's deterministic and safety-centric goals; defers the safety surface to last.

## Decision

The platform follows a **simulation-first** strategy.

Practically, this means:

1. The simulator (Gazebo Harmonic, see ADR-002) is the primary integration environment for Phases 1 through 4 of `docs/ROADMAP.md`.
2. All safety-relevant behavior is exercised in simulation before any equivalent behavior runs on hardware.
3. Hardware bench integration in Phase 5 reuses the same message contracts, the same supervisor, the same fault subsystem, and the same observability and replay tooling.
4. Hardware abstraction is validated by ensuring that only the gateway and sensor adapters differ between simulation and hardware. The autonomy stack remains agnostic.
5. Fault injection runs in simulation by default; only the hardware-allowed subset (per `docs/FAULT_INJECTION.md` section 12) runs on hardware.

## Consequences

### Positive

- Deterministic iteration: scenarios can be re-run, recorded, and compared.
- Safety testing precedes physical motion: dangerous fault scenarios are exercised in simulation, not on a moving rover.
- Cost control: a single bench rover suffices for Phase 5 because most validation is already done.
- Fault injection is decoupled from hardware risk.
- Faster debugging: simulation can be paused, rewound, and replayed.
- Hardware abstraction is validated, not assumed: the message contract is exercised before hardware exists.
- Replay artifacts compound across phases. A scenario recorded in Phase 3 is still useful in Phase 5.

### Negative

- The platform inherits any weaknesses of the simulator (physics fidelity, sensor models, simulator-version drift).
- Sim-vs-hardware parity is a real risk. Mitigated by the parity tests defined in `docs/TESTING_STRATEGY.md` section 10 and by the explicit parity tracking in `docs/REPLAY_SYSTEM.md`.
- Some failure modes (electrical, mechanical) are not representable in simulation. The MVP scope explicitly excludes them; future hardware safety analysis will need separate treatment.

### Neutral

- Workstation requirements are higher because the simulator is the primary environment. Acceptable for a portfolio platform with developer-class hardware.

## Alternatives Considered

| Alternative | Reason rejected |
|---|---|
| Hardware-first | Cannot exercise unsafe fault scenarios without risk; cannot iterate quickly; produces ad-hoc autonomy that resists later structuring. |
| Hybrid-first | Doubles coordination cost, tends to produce two half-built systems, dilutes architectural focus. |
| Perception-first | Misaligned with deterministic and safety-centric goals. Pushes safety surface to last, which is the opposite of what this platform exists to demonstrate. |

## Follow-up Work

- Maintain a shared message contract between `rover_sim_gazebo` and the future `rover_hw_gateway` hardware variant. Any divergence must be intentional and documented.
- Track sim-vs-hardware parity per scenario starting in Phase 5 (see `docs/TESTING_STRATEGY.md` section 10).
- Pin simulator versions in run metadata, as required by `docs/REPLAY_SYSTEM.md`.
- Treat any safety-relevant behavior that has not been exercised in simulation as a gap, not an exception.
