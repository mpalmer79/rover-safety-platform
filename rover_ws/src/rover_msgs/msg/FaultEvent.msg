# FaultEvent — fault lifecycle transition emitted by rover_fault_injection.
#
# Mirrors fault_injection.* events from docs/EVENT_MODEL.md.

builtin_interfaces/Time stamp
string run_id
string scenario_id

# Stable identifier for the fault instance within the scenario.
string fault_id

# Controlled vocabulary aligned with docs/FAULT_INJECTION.md section 4:
#   "stale_lidar", "encoder_drift", "imu_bias", "bridge_disconnect",
#   "command_timeout", "watchdog_expiration", "packet_delay",
#   "sensor_disagreement", "wheel_slip".
string fault_type

# What the fault targets (topic, watchdog, subsystem).
string target

# Lifecycle phase: "armed", "fired", "cleared".
string phase

# Reason code: "fault_armed", "fault_fired", "fault_cleared".
string reason_code

# Free-form summary. Structured detail belongs in attributes_json.
string message

# JSON-serialized attribute payload (parameters used, observed effect, etc.).
# Consumers must treat this as opaque text and parse only when needed.
string attributes_json
