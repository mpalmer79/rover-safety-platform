# WaypointEvent — a discrete waypoint lifecycle event.
#
# Mirrors mission_waypoint.* events from the structured event stream.

builtin_interfaces/Time stamp
string run_id
string scenario_id
string mission_id

# Stable phase: "activated", "completed", "timed_out", "aborted".
string phase

# Stable reason code (e.g. "waypoint_completed", "waypoint_timeout").
string reason_code

string waypoint_id
uint32 waypoint_index

# Wall-readable summary; structured details belong in the JSON event
# stream.
string message
