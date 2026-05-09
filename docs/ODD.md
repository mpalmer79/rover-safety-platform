# Operational Design Domain (ODD)

## 1. Purpose

This document defines the Operational Design Domain (ODD) for the Autonomous Safety Validation Rover Platform.

The ODD specifies the bounded set of operational conditions in which the rover is permitted to attempt autonomous behavior. Outside the ODD, the system is expected to detect the boundary violation, transition to a defined safety state, and emit replayable evidence of the transition.

The ODD is binding on the rest of the system. The mission layer, the planner, the safety supervisor, and the hardware gateway must all reason about the ODD as a first-class operational constraint. Any subsystem that does not enforce or respect the ODD is considered defective.

This document does not claim safety certification, regulatory compliance, or industrial qualification. The ODD exists to make the rover's behavior bounded, explainable, and replayable, not to assert formal safety guarantees.

---

## 2. Scope

The ODD applies to:

- the simulation-first MVP running under Gazebo Harmonic on Ubuntu 24.04
- the future bench hardware bring-up using a Raspberry Pi 5 class SBC and a dedicated MCU safety layer
- any replayed incident reconstruction that uses the same message contracts

The ODD does not apply to:

- offline analysis tooling
- developer benches without an active rover or simulated rover
- training data generation pipelines that do not command motion

---

## 3. Supported Environment

### 3.1 Indoor and semi-structured simulated environments

The MVP operates inside one of the following:

- a Gazebo Harmonic world that models flat or near-flat indoor floor plans
- a Gazebo Harmonic world that models a semi-structured outdoor area with bounded obstacles, predictable lighting, and known terrain assumptions
- a small bench surface for hardware bring-up with manually placed obstacles

### 3.2 Terrain

Allowed terrain:

- flat hard floor (sim and bench)
- low-pile carpet equivalent in simulation
- short uniform tile or laminate equivalent in simulation
- gentle ramps below the slope limit defined in section 6

Disallowed terrain:

- staircases
- gravel
- mud
- loose granular surfaces
- high-pile carpet
- standing water
- ice
- terrain with discontinuous height changes greater than 2 cm

### 3.3 Indoor / outdoor assumptions

The MVP is treated as an indoor / semi-structured platform.

Outdoor operation is permitted only in simulation worlds that explicitly model bounded outdoor scenes. GNSS-based outdoor autonomy is out of scope for the MVP and is deferred until a later phase.

### 3.4 Lighting assumptions

Lighting is not a primary input to the MVP because the perception stack is deliberately camera-deferred.

Simulation lighting must be:

- consistent across a given run
- deterministic when scenarios are replayed
- not used as a primary localization or detection input

Hardware bench lighting must:

- not damage the LiDAR (no direct sunlight into the scanner during bring-up)
- be sufficient for the operator to observe the platform

### 3.5 Obstacle assumptions

Allowed obstacles:

- static rigid obstacles with bounded dimensions
- slow-moving simulated obstacles introduced through scenario configuration
- bounded soft obstacles in simulation, treated as hard collisions for safety purposes

Disallowed obstacles:

- humans in the active operating area during hardware bench tests
- pets or other live animals in the active operating area
- transparent obstacles (glass walls, clear acrylic) without an explicit sensor mitigation
- highly reflective obstacles that defeat the LiDAR without an explicit sensor mitigation

### 3.6 Connectivity assumptions

The MVP assumes:

- a stable on-host ROS 2 graph over DDS
- a stable Gazebo Harmonic instance reachable via `ros_gz_bridge`
- developer-side Foxglove connection treated as best-effort, not safety-critical
- no dependence on cloud connectivity for any safety-critical decision

Network loss does not authorize motion. The hardware gateway must continue to honor the last authorized command policy, including timeouts, regardless of operator or telemetry connectivity.

---

## 4. Unsupported Environment

The MVP is explicitly out of domain in the following conditions:

- public roads
- public sidewalks
- crowded indoor areas with uncontrolled human traffic
- environments with unmapped staircases or drop-offs
- environments with active forklifts, vehicles, or industrial machinery
- environments with active welding, cutting, or other high-EMI sources adjacent to the rover
- environments with hazardous materials
- environments where loss of motion control could cause harm to people, animals, or property of significant value

The platform is not safety-certified. Operating outside the supported environment is a documentation violation, not a guaranteed failure mode.

---

## 5. Operational Assumptions

The following are treated as preconditions for any `ACTIVE_*` state.

| Assumption | Source |
|---|---|
| LiDAR scan publishing at the configured rate | `/scan` |
| Wheel encoder odometry publishing at the configured rate | `/odom` |
| IMU publishing at the configured rate | `/imu` |
| Static and dynamic transforms available | `/tf`, `/tf_static` |
| Authorized command pathway healthy | `/cmd_vel_authorized` consumer alive |
| Safety supervisor in a non-fault lifecycle state | `/safety/state` |

If any of these is missing, stale, or invalid at activation time, the safety supervisor must refuse to enter `ACTIVE_NORMAL` and must surface a structured event explaining the refusal.

---

## 6. Operational Limits

### 6.1 Velocity limits

| Mode | Linear velocity (max) | Angular velocity (max) |
|---|---|---|
| `ACTIVE_NORMAL` | 0.6 m/s | 1.0 rad/s |
| `ACTIVE_RESTRICTED` | 0.3 m/s | 0.6 rad/s |
| `ACTIVE_DEGRADED` | 0.15 m/s | 0.3 rad/s |
| `SAFE_STOP` | 0.0 m/s | 0.0 rad/s |
| `E_STOP_LATCHED` | 0.0 m/s | 0.0 rad/s |

These limits are enforced by the safety supervisor and clamped by the motion arbitration stage. Mission and planner outputs that exceed these limits must be clamped, and the clamping must emit a `motion_arbitration` event.

### 6.2 Slope limits

| Mode | Max sustained slope | Max momentary slope |
|---|---|---|
| `ACTIVE_NORMAL` | 5 deg | 8 deg |
| `ACTIVE_RESTRICTED` | 3 deg | 5 deg |
| `ACTIVE_DEGRADED` | 0 deg | 2 deg |

Exceeding the momentary limit is treated as an out-of-domain condition and triggers a transition toward `SAFE_STOP`.

### 6.3 Acceleration limits

| Mode | Max linear accel | Max angular accel |
|---|---|---|
| `ACTIVE_NORMAL` | 0.5 m/s² | 1.0 rad/s² |
| `ACTIVE_RESTRICTED` | 0.25 m/s² | 0.5 rad/s² |
| `ACTIVE_DEGRADED` | 0.15 m/s² | 0.3 rad/s² |

---

## 7. Sensor Assumptions

The MVP sensor stack is:

- 2D LiDAR
- wheel encoders
- IMU
- contact / bumper channel

For each sensor, the MVP assumes:

- a known, fixed mounting geometry expressed in `/tf_static`
- a documented expected publishing rate
- documented freshness thresholds enforced by the safety supervisor
- documented disagreement thresholds where multiple sensors observe overlapping state

Cameras, GNSS, depth sensors, radar, and ultrasonics are deferred. Adding any of them without a corresponding ADR and an updated ODD is prohibited.

---

## 8. Simulation Assumptions

The simulation environment is treated as the primary integration surface for the MVP.

The simulation must:

- run under Gazebo Harmonic
- expose sensors through ROS 2 topics that match the hardware contract
- support deterministic scenario replay where physics permits
- expose simulated faults only through the fault injection subsystem, never by directly mutating safety state

Simulation worlds should be versioned alongside the code that targets them. A scenario is not considered reproducible unless the world, the rover description, and the launch parameters are pinned.

---

## 9. ODD Condition Table

| Condition | Supported Range | Out-of-Domain Trigger | Expected System Response |
|---|---|---|---|
| Surface type | Flat hard floor, low-pile carpet, short ramps | Stairs, gravel, mud, ice, height steps > 2 cm | Transition toward `SAFE_STOP`, emit `safety_transition` event with reason `odd_terrain` |
| Slope | ≤ 5 deg sustained, ≤ 8 deg momentary in `ACTIVE_NORMAL` | Slope above momentary limit | Transition toward `SAFE_STOP`, reason `odd_slope` |
| Linear velocity | ≤ 0.6 m/s in `ACTIVE_NORMAL` | Authorized command exceeds limit | Clamp at arbitration, emit `motion_arbitration` event with reason `velocity_clamp` |
| Angular velocity | ≤ 1.0 rad/s in `ACTIVE_NORMAL` | Authorized command exceeds limit | Clamp at arbitration, emit `motion_arbitration` event with reason `angular_clamp` |
| LiDAR freshness | Last scan within configured staleness window | Stale beyond window | Transition to `ACTIVE_DEGRADED` or `SAFE_STOP` per policy, emit `sensor_health` event with reason `stale_lidar` |
| IMU freshness | Last sample within configured staleness window | Stale beyond window | Transition to `ACTIVE_DEGRADED` or `SAFE_STOP`, reason `stale_imu` |
| Encoder freshness | Last sample within configured staleness window | Stale beyond window | Transition to `ACTIVE_DEGRADED` or `SAFE_STOP`, reason `stale_encoders` |
| Sensor disagreement | Within configured tolerance | Disagreement above tolerance | Transition to `ACTIVE_DEGRADED`, reason `sensor_disagreement` |
| Bridge / transport health | DDS healthy, ros_gz_bridge alive in sim | Bridge disconnect or DDS partition | Transition to `SAFE_STOP`, reason `bridge_disconnect` |
| Authorized command consumer | Hardware gateway alive and consuming `/cmd_vel_authorized` | Consumer silent past timeout | Transition to `SAFE_STOP`, reason `command_timeout` |
| Watchdog | All registered watchdogs petted within window | Any watchdog expired | Transition to `SAFE_STOP` or `E_STOP_LATCHED` per policy, reason `watchdog_expiration` |
| Operator E-stop | Not asserted | Asserted | Transition to `E_STOP_LATCHED`, reason `operator_estop` |
| Connectivity to operator UI | Best-effort | Loss | No effect on motion authority. Telemetry queue may grow until backpressure thresholds are reached. |

---

## 10. Safe-Stop Triggers

The safety supervisor must initiate a transition toward `SAFE_STOP` on any of:

- ODD violation as listed in section 9
- watchdog expiration
- authorized command timeout
- bridge or transport disconnect
- explicit safe-stop request from a privileged operator pathway
- any sensor stream stale beyond the `SAFE_STOP` threshold
- any safety-critical lifecycle node entering an error state

`SAFE_STOP` always commands zero linear and zero angular velocity. Recovery from `SAFE_STOP` is permitted only through the `RECOVERY` state.

---

## 11. ODD Exit Conditions

An ODD exit is any condition that moves the rover from a supported operational range to an unsupported one.

ODD exits must:

- be detected by the safety supervisor or by a sensor adapter that reports to the safety supervisor
- emit a structured `safety_transition` event with the offending condition
- result in a transition to a more restrictive safety state, never a less restrictive one
- never be silently corrected by the planner or mission layer

It is acceptable for an ODD exit to be transient and to clear on its own. The state machine must still record the entry and the exit, and must not return to `ACTIVE_NORMAL` without passing through `RECOVERY`.

---

## 12. Recovery Requirements

To exit `SAFE_STOP` toward `ACTIVE_*`, the system must:

1. enter `RECOVERY`
2. revalidate every required input listed in section 5
3. confirm the offending ODD condition is no longer present
4. emit a `safety_transition` event with reason `recovery_validated`
5. only then transition to the appropriate `ACTIVE_*` state, which may be a more restrictive state than the one originally interrupted

`E_STOP_LATCHED` is not recoverable without an explicit operator reset action, even if the underlying condition has cleared.

---

## 13. Non-Goals

The following are explicitly outside the MVP ODD:

- camera-first perception
- visual SLAM
- GNSS-based outdoor autonomy
- multi-rover coordination
- public road or sidewalk operation
- humanoid or manipulation behavior
- cloud-dependent autonomy
- continuous learning at runtime
- end-to-end neural control
- Isaac Sim integration
- Jetson-class compute as a baseline

These are deferred. They may become candidate work in later phases, but only with a corresponding ADR, an updated ODD, and explicit acceptance gates.

---

## 14. Change Control

The ODD is a controlling document. Changes to the ODD must:

- be made by editing this file
- be accompanied by an ADR if the change widens supported conditions, adds a new sensor class, or alters safety limits
- be reflected in `docs/SAFETY_MODEL.md`, `docs/FAULT_INJECTION.md`, and `docs/TESTING_STRATEGY.md` where they impose new requirements
- not be made implicitly through code changes
