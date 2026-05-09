# Fault Injection Strategy

## 1. Purpose

This document defines the fault injection strategy for the Autonomous Safety Validation Rover Platform.

Fault injection is a first-class platform capability. It exists so that the safety supervisor, the state estimator, and the mission layer can be exercised against realistic failure modes in simulation, deterministically and repeatably. Without it, the platform cannot demonstrate that degraded behavior is bounded, explainable, and replayable.

The fault injection subsystem is `rover_fault_injection`. It is independent from the simulator, independent from the mission layer, and independent from the safety supervisor.

This document does not claim safety certification. Fault injection here is an engineering and validation tool, not a regulatory artifact.

---

## 2. Fault Injection Principles

### 2.1 Faults alter inputs and timing, not safety state

The fault injection subsystem is not allowed to set `/safety/state`, transition the supervisor's state machine, or write `/cmd_vel_authorized`. It alters the inputs and timing observed by other subsystems. The safety supervisor reacts to those inputs through its normal mechanisms.

This is an architectural rule. Any fault implementation that sets safety state directly is a defect.

### 2.2 Faults are explicit and named

Every fault has:

- a `fault_class` from the controlled list in section 4
- a configured `injection_point`
- a configured set of parameters
- a lifecycle (`armed`, `fired`, `cleared`)

Anonymous or implicit faults are not permitted.

### 2.3 Faults are scoped

A fault has explicit boundaries: the topic it touches, the time window in which it is active, the rover instance it targets, and the simulation world in which it applies. Faults must not leak across runs or scenarios.

### 2.4 Faults are observable

Every transition in a fault's lifecycle emits a `fault_injection.*` event conforming to `docs/EVENT_MODEL.md`. The fault must be visible in the event stream and in the recorded bag.

### 2.5 Faults are reproducible

Given a scenario, a seed (where applicable), and a pinned simulator and rover description, the same fault sequence must produce the same observable behavior up to documented determinism limits (see `docs/REPLAY_SYSTEM.md`).

### 2.6 Faults must not silently mask each other

Multiple concurrent faults are permitted, but each must emit its own events. The fault subsystem may not collapse two faults into one observation.

### 2.7 Faults do not mutate hardware in MVP

Hardware bring-up does not use the fault injection subsystem to physically damage or stress hardware. Hardware bench testing uses a restricted subset of fault classes that operate at the software boundary, with operator presence.

---

## 3. Architectural Boundaries

The fault injection subsystem must:

- live in `rover_fault_injection`
- expose configuration through scenario files, not hard-coded values
- publish to `/faults/injected` for every lifecycle transition, in addition to the structured event stream
- never subscribe to `/safety/state` for the purpose of changing its own behavior
- never subscribe to `/cmd_vel_authorized` for the purpose of changing motion
- be loadable and unloadable as a lifecycle node

The fault injection subsystem must not:

- run inside the supervisor process
- run inside the hardware gateway process
- be combined with mission orchestration

---

## 4. Supported MVP Fault Classes

| Fault Class | Description |
|---|---|
| `stale_lidar` | LiDAR scans stop or are delayed past the freshness window. |
| `encoder_drift` | Wheel-encoder odometry drifts by a configured rate or step. |
| `imu_bias` | IMU acceleration or angular-rate samples are biased by a configured offset. |
| `bridge_disconnect` | The simulation-to-ROS bridge or a transport link drops. |
| `command_timeout` | The hardware gateway stops consuming `/cmd_vel_authorized` or stops heartbeating. |
| `watchdog_expiration` | A registered watchdog is deliberately not petted, simulating a hung subsystem. |
| `packet_delay` | A configured topic experiences added latency. |
| `sensor_disagreement` | Two sensors that should agree (e.g. encoder-derived velocity vs IMU-derived velocity) are made to disagree. |
| `wheel_slip` | Simulated wheel slip causes encoder readings to diverge from ground-truth motion. |

Adding a fault class requires updating this document and the producing module. New fault classes must declare their injection point, expected detection, expected response, required events, and replay requirements.

---

## 5. Fault Lifecycle

A fault progresses through these phases:

1. **Configured** — the scenario file defines the fault's class, injection point, parameters, schedule, and seed.
2. **Armed** — the fault subsystem has loaded the configuration and is ready to fire. Emits `fault_injection.armed`.
3. **Fired** — the fault is actively altering inputs or timing. Emits `fault_injection.fired`. Continues to publish heartbeat events while fired if the fault is long-lived (configurable).
4. **Cleared** — the fault has stopped altering inputs or timing. Emits `fault_injection.cleared`.

Faults can be scheduled by:

- absolute simulator time
- delta from scenario start
- triggered by an operator action
- triggered by a specific event in the event stream (with explicit reason codes only)

Trigger by event must not depend on `/safety/state` or any motion topic, to avoid coupling fault injection to safety control loops.

---

## 6. Injection Points

The `injection_point` field describes where the fault acts. Allowed values:

| Injection Point | Effect |
|---|---|
| `topic.publish` | Drop, delay, or modify messages at publish time on the named topic. |
| `topic.subscribe` | Drop, delay, or modify messages at subscribe time on the named topic. |
| `bridge.gz_to_ros` | Affect the Gazebo-to-ROS bridge specifically. |
| `bridge.ros_to_gz` | Affect the ROS-to-Gazebo bridge specifically. |
| `gateway.consume` | Cause the hardware gateway to delay or stop consuming authorized commands. |
| `watchdog.skip_pet` | Cause the named watchdog owner to skip petting its watchdog. |

Injection points that mutate `/safety/state`, `/cmd_vel_authorized`, or the supervisor's internal state are prohibited.

---

## 7. Per-Class Fault Specifications

### 7.1 `stale_lidar`

| Field | Value |
|---|---|
| Description | LiDAR scans on `/scan` stop or are delayed beyond the freshness threshold. |
| Injection Point | `topic.publish` on `/scan` (or `bridge.gz_to_ros` for the corresponding sim topic) |
| Parameters | `mode`: `drop` \| `delay`; `delay_ms` for `delay`; `duration_ms` for the active window |
| Expected Detection | Sensor adapter and supervisor freshness gate detect staleness |
| Expected Safety Response | Transition to `ACTIVE_DEGRADED` past the degraded threshold; transition to `SAFE_STOP` past the safe-stop threshold |
| Required Events | `fault_injection.armed`, `fault_injection.fired`, `sensor_health.stale`, `safety_transition.entered ACTIVE_DEGRADED`, optional `safety_transition.entered SAFE_STOP`, `fault_injection.cleared`, `sensor_health.recovered` |
| Replay Requirement | Must reproduce the same sequence and timing to within the deterministic replay limits in `docs/REPLAY_SYSTEM.md` |

### 7.2 `encoder_drift`

| Field | Value |
|---|---|
| Description | Wheel-encoder odometry drifts at a configured rate or step. |
| Injection Point | `topic.publish` on `/odom` (or the wheel-encoder topic upstream of `/odom`) |
| Parameters | `drift_rate_mps_per_s`, `drift_step_m`, `axis`, `duration_ms` |
| Expected Detection | State-estimation divergence; sensor disagreement against IMU-derived velocity |
| Expected Safety Response | Confidence drop, transition to `ACTIVE_DEGRADED`, possible escalation to `SAFE_STOP` |
| Required Events | `fault_injection.armed`, `fault_injection.fired`, `state_estimation.diverged`, `sensor_health.disagreement`, appropriate `safety_transition.*`, `fault_injection.cleared` |
| Replay Requirement | Same |

### 7.3 `imu_bias`

| Field | Value |
|---|---|
| Description | Constant or ramped bias on IMU acceleration or angular rate. |
| Injection Point | `topic.publish` on `/imu` |
| Parameters | `axis`, `bias_value`, `ramp_rate`, `duration_ms` |
| Expected Detection | Localization confidence drop, sensor disagreement |
| Expected Safety Response | Transition to `ACTIVE_DEGRADED`, possible escalation |
| Required Events | `fault_injection.*`, `sensor_health.bias_detected`, `safety_transition.*` |
| Replay Requirement | Same |

### 7.4 `bridge_disconnect`

| Field | Value |
|---|---|
| Description | The simulation-to-ROS bridge drops, or the inverse direction drops. |
| Injection Point | `bridge.gz_to_ros` or `bridge.ros_to_gz` |
| Parameters | `direction`, `duration_ms` |
| Expected Detection | Multiple freshness gates fire simultaneously; bridge health check fails |
| Expected Safety Response | Transition to `SAFE_STOP` with reason `bridge_disconnect` |
| Required Events | `fault_injection.*`, multiple `sensor_health.stale` events, `safety_transition.entered SAFE_STOP` |
| Replay Requirement | Same |

### 7.5 `command_timeout`

| Field | Value |
|---|---|
| Description | The hardware gateway stops consuming `/cmd_vel_authorized` or stops heartbeating to the supervisor. |
| Injection Point | `gateway.consume` |
| Parameters | `mode`: `silent_consumer` \| `silent_heartbeat`; `duration_ms` |
| Expected Detection | Supervisor's gateway watchdog expires |
| Expected Safety Response | Transition to `SAFE_STOP` with reason `gateway_silent`; gateway independently decays to zero motion on its own command timeout |
| Required Events | `fault_injection.*`, `watchdog.expired`, `safety_transition.entered SAFE_STOP`, `motion_arbitration.zeroed` from gateway |
| Replay Requirement | Same |

### 7.6 `watchdog_expiration`

| Field | Value |
|---|---|
| Description | A registered watchdog owner skips petting its watchdog, simulating a hung subsystem. |
| Injection Point | `watchdog.skip_pet` |
| Parameters | `watchdog_name`, `duration_ms` |
| Expected Detection | Watchdog expiration |
| Expected Safety Response | The state transition configured for that watchdog |
| Required Events | `fault_injection.*`, `watchdog.expired`, `safety_transition.*` |
| Replay Requirement | Same |

### 7.7 `packet_delay`

| Field | Value |
|---|---|
| Description | Adds latency to a configured topic. |
| Injection Point | `topic.publish` or `topic.subscribe` |
| Parameters | `topic`, `delay_ms`, `jitter_ms`, `duration_ms` |
| Expected Detection | Freshness gates, control-loop instability where applicable |
| Expected Safety Response | Depends on which topic. May cause `ACTIVE_DEGRADED` or `SAFE_STOP`. |
| Required Events | `fault_injection.*`, downstream `sensor_health.*` and `safety_transition.*` as appropriate |
| Replay Requirement | Same |

### 7.8 `sensor_disagreement`

| Field | Value |
|---|---|
| Description | Forces two sensors that should agree to disagree above tolerance. |
| Injection Point | `topic.publish` on the targeted secondary sensor topic |
| Parameters | `delta`, `axis`, `mode`: `step` \| `ramp`; `duration_ms` |
| Expected Detection | Confidence subsystem disagreement detector |
| Expected Safety Response | `ACTIVE_DEGRADED`, possible escalation |
| Required Events | `fault_injection.*`, `sensor_health.disagreement`, `safety_transition.*` |
| Replay Requirement | Same |

### 7.9 `wheel_slip`

| Field | Value |
|---|---|
| Description | Simulated wheel slip; encoder readings diverge from ground-truth motion. |
| Injection Point | Simulator-side configuration or `topic.publish` on `/odom` |
| Parameters | `slip_factor`, `wheels`, `duration_ms` |
| Expected Detection | State-estimation divergence; disagreement between odometry and IMU |
| Expected Safety Response | `ACTIVE_RESTRICTED` if mild, `ACTIVE_DEGRADED` if persistent, `SAFE_STOP` if severe |
| Required Events | `fault_injection.*`, `state_estimation.diverged`, `safety_transition.*` |
| Replay Requirement | Same |

---

## 8. Observability Requirements

For every fault, the system must produce:

1. A `fault_injection.armed` event when the fault is loaded but not yet active.
2. A `fault_injection.fired` event at the moment the fault begins altering inputs or timing.
3. Heartbeat `fault_injection.fired` events at a configurable cadence for long-running faults.
4. A `fault_injection.cleared` event when the fault stops altering inputs or timing.
5. Periodic publication on `/faults/injected` reflecting the current set of active faults.

The events must include in `attributes`:

- `fault_class`
- `injection_point`
- the parameters used
- the schedule definition
- the seed (if applicable)

---

## 9. Replay Requirements

Each fault must:

- be reproducible from a pinned scenario file, simulator version, rover description, and seed
- emit the same sequence of `fault_injection.*` events on replay, in the same order, at equivalent simulator times
- be present in the recorded bag via `/faults/injected`
- be re-emittable from the event stream alone (i.e., a replay analyst can reconstruct the fault timeline from `events.jsonl` without the bag)

If a fault implementation cannot satisfy these requirements, it is not eligible for inclusion in the supported MVP fault classes and must be marked `experimental` in scenario files until it is.

---

## 10. Safety Constraints on the Fault Subsystem

The fault subsystem must:

1. Never write to `/safety/state`.
2. Never write to `/cmd_vel_authorized`.
3. Never set the supervisor's lifecycle state.
4. Never disable the supervisor's watchdogs except via the `watchdog.skip_pet` injection point against a single named watchdog owned by a peer subsystem.
5. Never alter `/tf_static` for a robot description fundamental to safety arbitration without an explicit ADR.
6. Refuse to load on hardware bench unless the configured fault classes are present in the hardware-allowed subset.
7. Default to `cleared` on shutdown, on lifecycle deactivation, and on supervisor `E_STOP_LATCHED`.

The supervisor's `E_STOP_LATCHED` must clear all active faults by side effect of the fault subsystem observing the operator E-stop. The fault subsystem subscribes to operator events for this purpose; it does not subscribe to `/safety/state` for routine operation.

---

## 11. Test Acceptance Criteria

A fault class is considered acceptance-tested when:

1. A scenario exists that arms, fires, and clears the fault.
2. The expected events are emitted in the expected order with the expected reason codes.
3. The supervisor reaches the expected safety state under the fault.
4. The supervisor returns to `ACTIVE_*` only after passing through `RECOVERY`.
5. Replay of the recorded run reproduces the event timeline within deterministic replay limits.
6. A separate negative test asserts that the fault subsystem does not bypass safety: a deliberately misconfigured fault must not transition `/safety/state` directly.

These criteria are tracked in `docs/TESTING_STRATEGY.md` under the `fault_injection` test category.

---

## 12. Hardware-Allowed Subset

For bench hardware testing, only the following fault classes are permitted:

- `stale_lidar` (software-side, by withholding the topic)
- `packet_delay` (software-side)
- `command_timeout` (software-side)
- `watchdog_expiration` (software-side)

Faults that depend on simulator-only mechanics (`wheel_slip` via simulator config, `bridge_disconnect` against `ros_gz_bridge`) are not applicable to hardware. Faults that involve unsafe physical conditions are not part of this subsystem at all.
