"""Thin facade over :class:`app.telemetry.run_recorder.RunRecorder`.

Kept separate so the replay namespace owns the public-facing recorder
API even though the implementation lives under ``telemetry``. Future
rosbag2 / MCAP support will be added here.
"""

from __future__ import annotations

from app.telemetry.run_recorder import RunRecorder


class RecorderFacade(RunRecorder):
    """Public alias of :class:`RunRecorder`.

    Future rosbag2 / MCAP-aware recorders should subclass
    :class:`RunRecorder` and be exposed under this name so callers do not
    need to know which implementation is in use.
    """
