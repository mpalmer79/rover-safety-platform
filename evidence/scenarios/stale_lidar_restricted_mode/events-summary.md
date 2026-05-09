# Events summary

Source: `runs/verify/verify-stale_lidar_restricted_mode/events.jsonl`

## Safety transitions
- `t=0ms` `safety_transition.entered` reason `boot_complete` safety=`INACTIVE` — BOOT -> INACTIVE: boot complete; awaiting activation
- `t=200ms` `safety_transition.entered` reason `operator_activate` safety=`ACTIVE_NORMAL` — INACTIVE -> ACTIVE_NORMAL: operator activation accepted
- `t=2200ms` `safety_transition.entered` reason `stale_lidar` safety=`ACTIVE_DEGRADED` — ACTIVE_NORMAL -> ACTIVE_DEGRADED: degraded inputs detected
- `t=2700ms` `safety_transition.entered` reason `stale_lidar` safety=`SAFE_STOP` — ACTIVE_DEGRADED -> SAFE_STOP: stale or missing required input

## Mission lifecycle
_None._

## Mission waypoint events
_None._

## Mission recovery events
_None._

## World model events
_None._

## Fault lifecycle
- `t=0ms` `fault_injection.armed` reason `fault_armed` safety=`BOOT` — fault armed: f-stale-lidar (stale_lidar)
- `t=2000ms` `fault_injection.fired` reason `fault_fired` safety=`BOOT` — fault fired: f-stale-lidar (stale_lidar)

## Watchdogs
- `t=3400ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=3500ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=3600ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=3700ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=3800ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=3900ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=4000ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=4100ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=4200ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=4300ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=4400ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=4500ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=4600ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=4700ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=4800ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=4900ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=5000ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=5100ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=5200ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=5300ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=5400ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=5500ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=5600ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=5700ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=5800ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=5900ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=6000ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=6100ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=6200ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=6300ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=6400ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=6500ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=6600ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=6700ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=6800ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=6900ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=7000ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=7100ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=7200ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=7300ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=7400ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=7500ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=7600ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=7700ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=7800ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
- `t=7900ms` `watchdog.expired` reason `stale_lidar` safety=`SAFE_STOP` — watchdog expired: lidar_freshness
