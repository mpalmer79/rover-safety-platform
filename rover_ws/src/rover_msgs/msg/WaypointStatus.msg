# WaypointStatus — per-tick progress toward the active waypoint.
#
# Published on /mission/progress at the orchestrator's evaluation
# rate. Consumers tracking long-running waypoints can compute time-to-
# completion from ``elapsed_ms`` and ``timeout_ms``.

builtin_interfaces/Time stamp
string run_id
string scenario_id
string mission_id

# Active waypoint identifier. Empty when no waypoint is active.
string waypoint_id

# Controlled vocabulary: "pending", "active", "completed", "timed_out", "aborted".
string status

# Distance to the waypoint's pose, in metres.
float32 distance_to_goal_m

# Heading error (signed, wrapped to [-pi, pi]).
float32 heading_error_rad

# Time spent on this waypoint so far, in milliseconds.
uint32 elapsed_ms

# The waypoint's configured timeout, in milliseconds.
uint32 timeout_ms

# Index of this waypoint in the mission queue (0-based).
uint32 waypoint_index

# Total number of waypoints in the mission.
uint32 waypoint_total
