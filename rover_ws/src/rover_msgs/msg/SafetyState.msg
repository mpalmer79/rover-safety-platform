# SafetyState — the supervisor's authoritative current state.
#
# Mirrors docs/SAFETY_MODEL.md section 5.1. Producers must publish only
# values from the controlled vocabulary below; consumers must reject
# unknown values rather than coerce them.

builtin_interfaces/Time stamp
string run_id
string scenario_id

# Controlled vocabulary — must equal one of:
#   "BOOT", "INACTIVE", "ACTIVE_NORMAL", "ACTIVE_RESTRICTED",
#   "ACTIVE_DEGRADED", "SAFE_STOP", "E_STOP_LATCHED", "RECOVERY"
string state

# Stable reason code from docs/EVENT_MODEL.md section 6 (e.g.
# "operator_activate", "stale_lidar", "operator_estop").
string reason_code

# Confidence score in [0.0, 1.0]; -1.0 if unknown.
float32 confidence_score

# True if the supervisor's E-stop latch is engaged.
bool estop_latched

# Lifecycle state of the supervisor node, one of
# "unconfigured", "inactive", "active", "finalized", "error".
string lifecycle_state
