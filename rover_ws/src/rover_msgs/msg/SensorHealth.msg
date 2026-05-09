# SensorHealth — per-sensor health summary published by adapter nodes.
#
# One message per sensor stream. Adapter nodes are responsible for
# normalizing freshness, evaluating warn / safe-stop thresholds, and
# producing a stable reason_code consistent with docs/EVENT_MODEL.md.

builtin_interfaces/Time stamp
string run_id
string scenario_id

# Controlled vocabulary: "lidar", "imu", "wheel_encoder", "contact".
string sensor_type

# Stable identifier for the physical/logical sensor.
string sensor_id

# Controlled vocabulary: "healthy", "stale", "disagreeing", "biased",
# "disconnected".
string status

# Reason code (e.g. "stale_lidar", "imu_bias"); empty when status is
# "healthy".
string reason_code

# Age of the most recent reading in milliseconds. -1 if absent.
int32 age_ms

# Confidence in [0.0, 1.0]; -1.0 if unknown.
float32 confidence_score

# Sequence number from the source reading; useful for detecting drops
# during replay.
uint64 sequence_number
