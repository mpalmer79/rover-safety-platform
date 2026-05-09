# WorldModelState — bounded world model snapshot.
#
# Published periodically by rover_world_model. The deterministic
# runtime intentionally stops short of full SLAM / probabilistic
# mapping; this message carries only the operational signals the
# orchestrator and operator dashboards consume.

builtin_interfaces/Time stamp
string run_id
string scenario_id

# Current pose (mirrors odom for replay convenience).
float32 pose_x
float32 pose_y
float32 heading_rad

# Forward-clearance summary derived from the LiDAR.
float32 forward_clearance_m
bool forward_sector_clear

# Lists of zone identifiers the pose is currently inside / near.
string[] inside_keepout
string[] near_keepout
string[] inside_restricted_speed

# Non-empty when an operational boundary has been violated.
string[] boundary_violations

# Effective speed limits implied by zones at this pose. -1.0 if no
# zone-imposed limit applies.
float32 speed_limit_linear
float32 speed_limit_angular
