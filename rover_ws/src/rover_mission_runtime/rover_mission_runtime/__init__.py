"""rover_mission_runtime: ROS 2 mission orchestrator + Nav2 boundary.

The mission node (``mission_node.py``) embeds the deterministic
:class:`app.mission.MissionOrchestrator`. The Nav2 velocity-clamp
node (``nav2_velocity_clamp.py``) is the architectural bridge that
lets a Nav2 controller participate without ever bypassing the
:class:`app.safety.SafetySupervisor`: Nav2 publishes onto
``/cmd_vel_nav2``; the clamp clamps to the orchestrator's per-state
limits and republishes onto ``/cmd_vel_requested``; only then does the
safety bridge authorise motion.
"""

__version__ = "0.1.0"
