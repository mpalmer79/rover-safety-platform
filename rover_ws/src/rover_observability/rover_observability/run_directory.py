"""Run directory layout helper.

Provides a small wrapper around :class:`app.replay.RecorderFacade` so
that ROS nodes can:

* allocate a ``run_id`` and a run directory at startup,
* write/refresh ``metadata.json``,
* finalise the run on shutdown.

The recorder backing this helper is the same one used by the
deterministic Python engine, which keeps replay artefacts
interchangeable between the two execution paths.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.domain.enums import ReplayStatus
from app.domain.identifiers import RunId, ScenarioId, UuidIdGenerator
from app.domain.replay import RunMetadata
from app.replay.recorder import RecorderFacade


_DEFAULT_RECORDED_TOPICS: tuple[str, ...] = (
    "/scan",
    "/odom",
    "/imu",
    "/tf",
    "/tf_static",
    "/cmd_vel_requested",
    "/cmd_vel_authorized",
    "/safety/state",
    "/safety/events",
    "/safety/motion_authorization",
    "/system/health",
    "/replay/markers",
    "/sensors/lidar/health",
    "/sensors/imu/health",
    "/sensors/wheel_encoder/health",
    "/sensors/contact/health",
)


def open_run(
    *,
    runs_root: Path,
    run_id: Optional[RunId] = None,
    scenario_id: ScenarioId,
    armed_faults: tuple[str, ...] = (),
    recorded_topics: tuple[str, ...] = _DEFAULT_RECORDED_TOPICS,
) -> tuple[RunId, RecorderFacade]:
    """Allocate a run directory and return ``(run_id, recorder)``."""

    runs_root.mkdir(parents=True, exist_ok=True)
    rid = run_id if run_id is not None else UuidIdGenerator().run_id()
    started_wall = (
        datetime.now(tz=timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
    )
    metadata = RunMetadata(
        run_id=rid,
        scenario_id=scenario_id,
        started_wall=started_wall,
        started_sim_ns=0,
        recorded_topics=recorded_topics,
        armed_faults=armed_faults,
    )
    recorder = RecorderFacade(
        runs_root=runs_root,
        run_id=rid,
        scenario_id=scenario_id,
        metadata=metadata,
    )
    return rid, recorder


def finalise_run(
    recorder: RecorderFacade, *, ended_sim_ns: int, status: ReplayStatus = ReplayStatus.FINALIZED
) -> None:
    ended_wall = (
        datetime.now(tz=timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
    )
    recorder.finalize(ended_wall=ended_wall, ended_sim_ns=ended_sim_ns, status=status)
    recorder.close()
