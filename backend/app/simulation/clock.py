"""Re-export the manual clock for the simulation namespace.

Kept as a thin module so the simulation package has its own
``simulation.clock`` import path even though the implementation lives
in :mod:`app.domain.time`.
"""

from app.domain.time import ManualClock, MonotonicClock, SimulationClock, Timestamp

__all__ = ["ManualClock", "MonotonicClock", "SimulationClock", "Timestamp"]
