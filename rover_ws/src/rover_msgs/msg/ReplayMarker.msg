# ReplayMarker — replay-significant marker emitted by rover_observability.
#
# Markers are recorded into rosbag2 alongside the regular topic stream.
# They allow replay tooling to align timelines with run lifecycle and
# scenario events.

builtin_interfaces/Time stamp
string run_id
string scenario_id

# Marker kind. Controlled vocabulary:
#   "run_started", "run_finalized",
#   "scenario_loaded", "scenario_completed",
#   "recording_started", "recording_stopped",
#   "checkpoint".
string kind

# Free-form label for dashboards.
string label

# Stable reason code, e.g. "scenario_loaded", "recording_started".
string reason_code

# Optional JSON-serialized payload (run metadata snapshot, etc.).
string payload_json
