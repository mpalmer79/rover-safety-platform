# SystemHealth — aggregate health of the supervisor and its watchdogs.

builtin_interfaces/Time stamp
string run_id
string scenario_id

# Aggregate severity; one of
# "DEBUG", "INFO", "NOTICE", "WARNING", "ERROR", "CRITICAL".
string severity

# True if any required input is missing or stale.
bool any_input_unhealthy

# True if any watchdog has expired.
bool any_watchdog_expired

# Names of expired watchdogs, if any.
string[] expired_watchdogs

# Per-stream age in milliseconds. Use -1 for "absent".
int32 lidar_age_ms
int32 imu_age_ms
int32 encoder_age_ms
int32 contact_age_ms

# Confidence in [0.0, 1.0]; -1.0 if unknown.
float32 confidence_score

# Free-form summary suitable for dashboards. Not parsed by tools.
string summary
