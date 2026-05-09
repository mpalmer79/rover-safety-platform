# Events summary

Source: `/tmp/p3-final-runs/verify-estop_latched_manual_reset_required/events.jsonl`

## Safety transitions
- `t=0ms` `safety_transition.entered` reason `boot_complete` safety=`INACTIVE` — BOOT -> INACTIVE: boot complete; awaiting activation
- `t=200ms` `safety_transition.entered` reason `operator_activate` safety=`ACTIVE_NORMAL` — INACTIVE -> ACTIVE_NORMAL: operator activation accepted
- `t=1500ms` `safety_transition.entered` reason `operator_estop` safety=`E_STOP_LATCHED` — ACTIVE_NORMAL -> E_STOP_LATCHED: E-stop asserted by operator

## Mission lifecycle
_None._

## Mission waypoint events
_None._

## Mission recovery events
_None._

## World model events
_None._

## Fault lifecycle
_None._

## Watchdogs
_None._
