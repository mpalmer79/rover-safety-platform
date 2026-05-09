# ADR-005: Companion Computer + MCU Split

## Status
Accepted

## Context

The platform commits to bench hardware integration in Phase 5 of `docs/ROADMAP.md`. The hardware decision must be made before the supervisor and gateway are designed in detail, because the boundary between the SBC and any auxiliary controller has architectural implications for command timing, watchdog behavior, and the actuator decay-to-zero contract.

Constraints at decision time:

- The platform is not safety-certified and does not claim hard real-time guarantees from a Linux SBC.
- The safety supervisor must be inspectable, replayable, and lifecycle-managed; a Linux SBC running ROS 2 is the natural environment for it.
- Some safety-relevant duties — actuator command timeout, low-level decay-to-zero, hardware E-stop coupling — benefit from a deterministic execution environment.
- The MVP does not require advanced perception. Jetson-class compute is unnecessary at this stage and would be premature.
- The future hardware design must remain consistent with the simulation-first contracts (see ADR-003) so that bench testing reuses, rather than diverges from, the established message contracts.

Common architectural shapes considered:

- A single Linux SBC controls everything, including motors, with software watchdogs. Convenient but conflates planning and motor timing.
- A Jetson-class compute platform from day one, with the SBC role absorbed. Overprovisioned for an MVP without perception workloads, and operationally heavier.
- An MCU-only architecture where the entire control stack runs on a microcontroller. Deterministic but loses ROS 2 ecosystem benefits and does not match the platform's observability and replay needs.

## Decision

The platform adopts a **two-tier hardware architecture**:

1. A **Raspberry Pi 5 class single-board computer** runs Ubuntu 24.04 and ROS 2 Jazzy. It hosts the safety supervisor, mission orchestration, sensor adapters, state estimation, observability, and the hardware gateway.
2. A **dedicated MCU safety island** handles timing-sensitive duties: actuator command timeout, decay-to-zero on command silence, hardware E-stop coupling, and any low-level watchdog responsibilities that benefit from a deterministic execution environment.

The MCU communicates with the SBC through **micro-ROS or a narrow MCU protocol** (serial, UDP, or equivalent). The exact protocol is a Phase 5 implementation decision; the architectural commitment in this ADR is that the boundary exists and is narrow.

The Linux SBC is **not** treated as a hard real-time motor controller. The platform's contracts assume it is best-effort with respect to scheduling jitter, and that any timing-sensitive responsibilities live on the MCU.

Jetson-class compute is **deferred** until perception workloads justify it, gated by an ADR. Adopting Jetson before then is overprovisioning.

## Consequences

### Positive

- Linux SBC scheduling jitter is bounded in its impact: it cannot turn into a runaway actuator condition because the MCU enforces command timeout independently.
- The MCU can implement actuator decay-to-zero in a few hundred lines of firmware, with a small certifiable-style review surface (still not certified, but inspectable).
- Hardware E-stop wiring lives near the actuator, where it is hardest to bypass.
- The SBC retains the full ROS 2 ecosystem: lifecycle nodes, rosbag2, ros2_tracing, Foxglove integration.
- The architecture is consistent with industry practice for non-hard-real-time SBC robotics platforms.

### Negative

- A second class of artifact (MCU firmware) must be developed and maintained.
- The protocol between SBC and MCU is a long-term concern. Even if narrow, it must be versioned and documented.
- Sim-vs-hardware parity must account for the MCU's command timeout. The hardware gateway's behavior in simulation must mirror the MCU's behavior in hardware.
- micro-ROS, if chosen, brings its own dependency on the broader ROS 2 ecosystem. A narrow custom protocol is simpler in some respects but loses tooling.

### Neutral

- The MVP's simulation-first phases (1 through 4) do not depend on the MCU. The decision affects Phase 5 onward.

## Alternatives Considered

| Alternative | Reason rejected |
|---|---|
| SBC-only control | Forces the SBC to act as a hard real-time controller, which it is not. Scheduling jitter becomes a safety problem. Negates the simplicity gains. |
| Jetson-first hardware | Overprovisioned for a non-perception MVP. Higher cost, higher operational complexity, no architectural benefit at this scale. May be revisited under a future ADR if perception expansion (Phase 6) justifies it. |
| MCU-only robotics control | Loses ROS 2 ecosystem. Cannot host the safety supervisor as a lifecycle-managed node. Cannot host observability or replay tooling. Inconsistent with the platform's central thesis. |

## Follow-up Work

- Specify the SBC-to-MCU protocol in Phase 5 (micro-ROS vs narrow custom protocol). Document the choice in a follow-up ADR.
- Define the MCU's actuator command timeout and decay-to-zero behavior precisely in `rover_hw_gateway` documentation, in alignment with `docs/SAFETY_MODEL.md`.
- Define the hardware-allowed fault subset that exercises the MCU pathway without unsafe physical conditions (already constrained in `docs/FAULT_INJECTION.md` section 12).
- Track sim-vs-hardware parity for the gateway specifically, since the MCU's behavior is the most likely source of divergence between simulation and hardware.
- Reserve the option to revisit Jetson-class compute in a future ADR if and when perception workloads justify it; do not adopt preemptively.
