# MissionState — the mission orchestrator's current lifecycle state.
#
# Mirrors app.mission.enums.MissionState. Producers must publish only
# values from the controlled vocabulary below; consumers must reject
# unknown values.

builtin_interfaces/Time stamp
string run_id
string scenario_id
string mission_id

# Controlled vocabulary — must equal one of:
#   "MISSION_IDLE", "MISSION_PREPARING", "MISSION_ACTIVE",
#   "MISSION_PAUSED", "MISSION_RECOVERY", "MISSION_DEGRADED",
#   "MISSION_ABORTING", "MISSION_ABORTED", "MISSION_COMPLETE".
string state

# Stable reason code for the most recent transition into this state.
string reason_code

# Mirror of /safety/state at the time the mission state was published,
# for replay-side correlation without a join.
string safety_state

# 0.0 - 1.0; -1.0 if unknown.
float32 mission_progress
