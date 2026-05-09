"""rover_mission_diagnostics: live mission health surface.

The diagnostics node aggregates mission-level signals (current state,
active waypoint, recovery engagements, world-model hazards) into a
single ``/diagnostics/mission`` ``DiagnosticArray`` plus a structured
``/diagnostics/mission_summary`` JSON record. It does not own mission
state.
"""

__version__ = "0.1.0"
