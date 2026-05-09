# Events summary

Source: `/tmp/p3-final-runs/verify-odometry_divergence_safe_stop/events.jsonl`

## Safety transitions
- `t=0ms` `safety_transition.entered` reason `boot_complete` safety=`INACTIVE` — BOOT -> INACTIVE: boot complete; awaiting activation
- `t=200ms` `safety_transition.entered` reason `operator_activate` safety=`ACTIVE_NORMAL` — INACTIVE -> ACTIVE_NORMAL: operator activation accepted
- `t=1500ms` `safety_transition.entered` reason `sensor_disagreement` safety=`ACTIVE_DEGRADED` — ACTIVE_NORMAL -> ACTIVE_DEGRADED: degraded inputs detected

## Mission lifecycle
_None._

## Mission waypoint events
_None._

## Mission recovery events
_None._

## World model events
_None._

## Fault lifecycle
- `t=0ms` `fault_injection.armed` reason `fault_armed` safety=`BOOT` — fault armed: f-disagreement (sensor_disagreement)
- `t=1500ms` `fault_injection.fired` reason `fault_fired` safety=`BOOT` — fault fired: f-disagreement (sensor_disagreement)

## Watchdogs
_None._
