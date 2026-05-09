# HazardReport — a single hazard detected by the world model.
#
# Mirrors world_model.* events. Multiple hazards may be active
# simultaneously; rover_world_model publishes one HazardReport per
# active hazard each tick.

builtin_interfaces/Time stamp
string run_id
string scenario_id

# Stable hazard kind, one of:
#   "keepout_pending", "keepout_violation",
#   "restricted_speed_violation", "operational_boundary_violation",
#   "obstacle_near", "obstacle_blocking".
string kind

# Stable reason code matching the world_model.<kind> event vocabulary.
string reason_code

# Severity from the EVENT_MODEL.md vocabulary.
string severity

string summary

# Optional structured zone / boundary identifier.
string zone_id

# Optional measurement (clearance for obstacle hazards, distance
# outside boundary for boundary hazards). -1.0 when unset.
float32 metric_m
