# MotionAuthorization — the supervisor's per-cycle motion decision.
#
# This message is published alongside /cmd_vel_authorized for
# observability and replay. The actuator path consumes
# /cmd_vel_authorized (geometry_msgs/Twist), not this message.

builtin_interfaces/Time stamp
string run_id
string scenario_id

# Decision vocabulary (docs/EVENT_MODEL.md): one of
#   "authorized", "authorized_clamped",
#   "rejected_zeroed", "rejected_expired", "rejected_degraded".
string decision

# Stable reason code, e.g. "velocity_clamp", "safe_stop_zero",
# "command_expired".
string reason_code

# Safety state at the time of arbitration.
string safety_state

# What was requested.
geometry_msgs/Twist requested

# What was authorized.
geometry_msgs/Twist authorized

# Was the authorized command clamped relative to the request?
bool was_clamped

# Optional supervisor confidence score in [0.0, 1.0]; -1.0 if unknown.
float32 confidence_score
