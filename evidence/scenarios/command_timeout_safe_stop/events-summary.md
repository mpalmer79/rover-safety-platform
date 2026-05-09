# Events summary

Source: `/tmp/p3-final-runs/verify-command_timeout_safe_stop/events.jsonl`

## Safety transitions
- `t=0ms` `safety_transition.entered` reason `boot_complete` safety=`INACTIVE` — BOOT -> INACTIVE: boot complete; awaiting activation
- `t=200ms` `safety_transition.entered` reason `operator_activate` safety=`ACTIVE_NORMAL` — INACTIVE -> ACTIVE_NORMAL: operator activation accepted
- `t=2500ms` `safety_transition.entered` reason `gateway_silent` safety=`SAFE_STOP` — ACTIVE_NORMAL -> SAFE_STOP: watchdog escalation

## Mission lifecycle
_None._

## Mission waypoint events
_None._

## Mission recovery events
_None._

## World model events
_None._

## Fault lifecycle
- `t=0ms` `fault_injection.armed` reason `fault_armed` safety=`BOOT` — fault armed: f-cmd-timeout (command_timeout)
- `t=2000ms` `fault_injection.fired` reason `fault_fired` safety=`BOOT` — fault fired: f-cmd-timeout (command_timeout)

## Watchdogs
- `t=2500ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=2600ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=2700ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=2800ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=2900ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=3000ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=3100ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=3200ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=3300ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=3400ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=3500ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=3600ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=3700ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=3800ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=3900ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=4000ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=4100ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=4200ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=4300ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=4400ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=4500ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=4600ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=4700ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=4800ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=4900ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=5000ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=5100ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=5200ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=5300ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=5400ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=5500ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=5600ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=5700ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=5800ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=5900ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=6000ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=6100ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=6200ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=6300ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=6400ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=6500ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=6600ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=6700ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=6800ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=6900ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=7000ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=7100ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=7200ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=7300ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=7400ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=7500ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=7600ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=7700ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=7800ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
- `t=7900ms` `watchdog.expired` reason `gateway_silent` safety=`SAFE_STOP` — watchdog expired: gateway_heartbeat
