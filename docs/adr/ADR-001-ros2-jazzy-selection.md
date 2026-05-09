# ADR-001: ROS 2 Jazzy Selection

## Status
Accepted

## Context

The Autonomous Safety Validation Rover Platform requires a middleware foundation that supports lifecycle-managed nodes, deterministic communication patterns, mature simulator interoperability, and a multi-year support horizon. The platform is intended to evolve from a simulation-first MVP through bench hardware integration without forcing a middleware migration along the way.

ROS 2 is the natural candidate. The remaining decision is which ROS 2 distribution to standardize on for the platform's foundational period.

Relevant constraints at decision time:

- The platform targets Ubuntu 24.04 as the host OS for both the simulation host and the SBC.
- The platform uses Gazebo Harmonic as the primary simulator; ROS 2 Jazzy is the distribution aligned to it.
- Nav2 and `BehaviorTree.CPP` are required components; both are supported on ROS 2 Jazzy.
- `robot_localization`, `rosbag2` with the MCAP storage plugin, `ros2_tracing`, and Foxglove integrations are required and stable on ROS 2 Jazzy.
- The platform requires lifecycle-managed nodes for safety-critical subsystems.
- The platform requires DDS-backed communication with QoS controls.
- Long-term support is required because the platform's value compounds with stable artifacts (recorded runs, scenarios, ADRs).

Alternatives considered:

- ROS 2 Rolling: tracks the development tip, no support horizon, churn unacceptable for a platform whose value depends on stable replay artifacts.
- Older ROS 2 distributions (e.g., Humble): viable today but misaligned with Ubuntu 24.04 and Gazebo Harmonic. Selecting an older LTS would force a migration before hardware bring-up.
- Custom middleware over a non-ROS transport: rejected outright. Loses the entire ROS 2 ecosystem (Nav2, lifecycle, rosbag2, Foxglove, ros2_tracing) for no offsetting architectural gain at this stage.

## Decision

The platform standardizes on **ROS 2 Jazzy** on **Ubuntu 24.04** for the foundational period covering Phases 0 through 5 of `docs/ROADMAP.md`.

This decision applies to:

- the simulation host
- the bench hardware SBC (Raspberry Pi 5 class)
- CI runners that exercise the platform

The MCU safety island (Phase 5+) does not run ROS 2; it communicates with the SBC through micro-ROS or a narrow protocol, as defined in ADR-005.

## Consequences

### Positive

- Long-term support aligned with Ubuntu 24.04 reduces the probability of a forced migration during the platform's most active development period.
- Lifecycle-managed nodes are natively supported and used by the safety supervisor and other safety-relevant subsystems.
- `BehaviorTree.CPP`, Nav2, `robot_localization`, and the MCAP storage plugin are all first-class on Jazzy.
- ROS 2 Jazzy aligns with Gazebo Harmonic without requiring custom integration work for the simulation bridge.
- DDS-based communication with QoS controls is sufficient for the platform's deterministic communication needs without custom transport.

### Negative

- The platform inherits the ROS 2 Jazzy lifecycle calendar. Patch and minor updates must be tracked.
- Workarounds for distribution-specific issues become part of the platform's maintenance burden.
- Switching distributions later requires deliberate planning and an ADR.

### Neutral

- Tooling that is distribution-agnostic (Foxglove, MCAP) remains usable across future migrations.

## Alternatives Considered

| Alternative | Reason rejected |
|---|---|
| ROS 2 Rolling | No support horizon. Replay artifacts must remain stable across many months; Rolling churn defeats this. |
| ROS 2 Humble | Aligned with Ubuntu 22.04 and earlier Gazebo. Selecting it would force a migration during hardware bring-up. |
| Older ROS 2 distributions | End-of-life or near end-of-life, with no path forward to Gazebo Harmonic. |
| Custom middleware | Loses Nav2, lifecycle, rosbag2, ros2_tracing, and Foxglove integration. No architectural gain at this scale. |

## Follow-up Work

- Pin the ROS 2 Jazzy minor version used in CI in `metadata.json` for every recorded run, per `docs/REPLAY_SYSTEM.md`.
- Document the deprecation policy for moving off Jazzy when its support window ends; do not commit to a successor distribution in this ADR.
- Track upstream changes that affect lifecycle, DDS QoS defaults, or `rosbag2` MCAP behavior, as they may invalidate test assumptions.
