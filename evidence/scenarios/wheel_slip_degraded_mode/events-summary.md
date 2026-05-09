# Events summary

Source: `/tmp/p3-final-runs/verify-wheel_slip_degraded_mode/events.jsonl`

## Safety transitions
- `t=0ms` `safety_transition.entered` reason `boot_complete` safety=`INACTIVE` — BOOT -> INACTIVE: boot complete; awaiting activation
- `t=200ms` `safety_transition.entered` reason `operator_activate` safety=`ACTIVE_NORMAL` — INACTIVE -> ACTIVE_NORMAL: operator activation accepted
- `t=1500ms` `safety_transition.entered` reason `imu_bias` safety=`ACTIVE_DEGRADED` — ACTIVE_NORMAL -> ACTIVE_DEGRADED: degraded inputs detected
- `t=4500ms` `safety_transition.refused` reason `invalid_transition` safety=`ACTIVE_DEGRADED` — refused ACTIVE_DEGRADED -> ACTIVE_NORMAL: nominal operation
- `t=4600ms` `safety_transition.refused` reason `invalid_transition` safety=`ACTIVE_DEGRADED` — refused ACTIVE_DEGRADED -> ACTIVE_NORMAL: nominal operation
- `t=4700ms` `safety_transition.refused` reason `invalid_transition` safety=`ACTIVE_DEGRADED` — refused ACTIVE_DEGRADED -> ACTIVE_NORMAL: nominal operation
- `t=4800ms` `safety_transition.refused` reason `invalid_transition` safety=`ACTIVE_DEGRADED` — refused ACTIVE_DEGRADED -> ACTIVE_NORMAL: nominal operation
- `t=4900ms` `safety_transition.refused` reason `invalid_transition` safety=`ACTIVE_DEGRADED` — refused ACTIVE_DEGRADED -> ACTIVE_NORMAL: nominal operation
- `t=5000ms` `safety_transition.refused` reason `invalid_transition` safety=`ACTIVE_DEGRADED` — refused ACTIVE_DEGRADED -> ACTIVE_NORMAL: nominal operation
- `t=5100ms` `safety_transition.refused` reason `invalid_transition` safety=`ACTIVE_DEGRADED` — refused ACTIVE_DEGRADED -> ACTIVE_NORMAL: nominal operation
- `t=5200ms` `safety_transition.refused` reason `invalid_transition` safety=`ACTIVE_DEGRADED` — refused ACTIVE_DEGRADED -> ACTIVE_NORMAL: nominal operation
- `t=5300ms` `safety_transition.refused` reason `invalid_transition` safety=`ACTIVE_DEGRADED` — refused ACTIVE_DEGRADED -> ACTIVE_NORMAL: nominal operation
- `t=5400ms` `safety_transition.refused` reason `invalid_transition` safety=`ACTIVE_DEGRADED` — refused ACTIVE_DEGRADED -> ACTIVE_NORMAL: nominal operation
- `t=5500ms` `safety_transition.refused` reason `invalid_transition` safety=`ACTIVE_DEGRADED` — refused ACTIVE_DEGRADED -> ACTIVE_NORMAL: nominal operation
- `t=5600ms` `safety_transition.refused` reason `invalid_transition` safety=`ACTIVE_DEGRADED` — refused ACTIVE_DEGRADED -> ACTIVE_NORMAL: nominal operation
- `t=5700ms` `safety_transition.refused` reason `invalid_transition` safety=`ACTIVE_DEGRADED` — refused ACTIVE_DEGRADED -> ACTIVE_NORMAL: nominal operation
- `t=5800ms` `safety_transition.refused` reason `invalid_transition` safety=`ACTIVE_DEGRADED` — refused ACTIVE_DEGRADED -> ACTIVE_NORMAL: nominal operation
- `t=5900ms` `safety_transition.refused` reason `invalid_transition` safety=`ACTIVE_DEGRADED` — refused ACTIVE_DEGRADED -> ACTIVE_NORMAL: nominal operation

## Mission lifecycle
_None._

## Mission waypoint events
_None._

## Mission recovery events
_None._

## World model events
_None._

## Fault lifecycle
- `t=0ms` `fault_injection.armed` reason `fault_armed` safety=`BOOT` — fault armed: f-slip (wheel_slip)
- `t=0ms` `fault_injection.armed` reason `fault_armed` safety=`BOOT` — fault armed: f-imu-bias (imu_bias)
- `t=1500ms` `fault_injection.fired` reason `fault_fired` safety=`BOOT` — fault fired: f-slip (wheel_slip)
- `t=1500ms` `fault_injection.fired` reason `fault_fired` safety=`BOOT` — fault fired: f-imu-bias (imu_bias)
- `t=4500ms` `fault_injection.cleared` reason `fault_cleared` safety=`BOOT` — fault cleared: f-slip (wheel_slip)
- `t=4500ms` `fault_injection.cleared` reason `fault_cleared` safety=`BOOT` — fault cleared: f-imu-bias (imu_bias)

## Watchdogs
_None._
