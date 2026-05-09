# RecoveryEvent — a discrete recovery lifecycle event.
#
# Mirrors mission_recovery.* events from the structured event stream.

builtin_interfaces/Time stamp
string run_id
string scenario_id
string mission_id

# Stable phase: "engaged", "cleared".
string phase

# Stable reason code (e.g. "waypoint_timeout", "keepout_violation",
# "operator_recovery", "recovery_attempts_exceeded").
string reason_code

# Recovery behaviour name. Controlled vocabulary:
#   "stop_and_reevaluate", "backup_and_retry", "wait_for_sensor_recovery",
#   "mission_abort", "safe_stop_escalation".
string recovery_behavior

# The waypoint that owned the recovery, if any.
string waypoint_id

# Per-waypoint attempt count when the event fired.
uint32 attempt_count

string message
