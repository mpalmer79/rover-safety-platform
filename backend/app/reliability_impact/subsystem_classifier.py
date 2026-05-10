"""Deterministic file-path classification.

Maps a repository-relative file path to exactly one
:class:`Subsystem`. The mapping is ordered: the first matching
prefix wins. Unknown files map to :attr:`Subsystem.UNKNOWN` so the
report can surface them.

The classifier never normalises away leading ``./`` segments
(callers should pass repository-relative paths), and it never
crashes on empty or malformed input.
"""

from __future__ import annotations

from pathlib import PurePosixPath

from app.reliability_impact.models import Subsystem


# Ordered list of (prefix, subsystem). First match wins. Prefixes
# are matched against repository-relative paths converted to
# forward-slash form so the classifier is OS-independent.
_PREFIX_RULES: tuple[tuple[str, Subsystem], ...] = (
    # Backend application packages.
    ("backend/app/safety/", Subsystem.SAFETY),
    ("backend/app/mission/", Subsystem.MISSION),
    ("backend/app/motion/", Subsystem.MOTION),
    ("backend/app/world_model/", Subsystem.MISSION),
    ("backend/app/replay/", Subsystem.REPLAY),
    ("backend/app/incident_analysis/", Subsystem.INCIDENT_ANALYSIS),
    ("backend/app/replay_review/", Subsystem.REPLAY_REVIEW),
    ("backend/app/replay_analytics/", Subsystem.REPLAY_ANALYTICS),
    ("backend/app/runtime_validation/", Subsystem.RUNTIME_VALIDATION),
    ("backend/app/verification/", Subsystem.VERIFICATION),
    ("backend/app/validation/", Subsystem.VERIFICATION),
    ("backend/app/reliability_impact/", Subsystem.RELIABILITY_IMPACT),
    ("backend/app/diagnostics/", Subsystem.OBSERVABILITY),
    ("backend/app/telemetry/", Subsystem.OBSERVABILITY),
    ("backend/app/faults/", Subsystem.SAFETY),
    ("backend/app/simulation/", Subsystem.GAZEBO_SIMULATION),
    ("backend/app/domain/", Subsystem.SAFETY),
    # ROS workspace.
    ("rover_ws/src/rover_safety_bridge/", Subsystem.SAFETY),
    ("rover_ws/src/rover_mission_runtime/", Subsystem.MISSION),
    ("rover_ws/src/rover_observability/", Subsystem.OBSERVABILITY),
    ("rover_ws/src/rover_runtime_diagnostics/", Subsystem.OBSERVABILITY),
    ("rover_ws/src/rover_world_model/", Subsystem.MISSION),
    ("rover_ws/src/rover_mission_diagnostics/", Subsystem.OBSERVABILITY),
    ("rover_ws/src/rover_sim_gazebo/", Subsystem.GAZEBO_SIMULATION),
    ("rover_ws/src/rover_description/", Subsystem.GAZEBO_SIMULATION),
    ("rover_ws/src/rover_sensor_adapters/", Subsystem.OBSERVABILITY),
    ("rover_ws/src/rover_bringup/", Subsystem.ROS_WORKSPACE),
    ("rover_ws/src/rover_msgs/", Subsystem.ROS_WORKSPACE),
    ("rover_ws/src/", Subsystem.ROS_WORKSPACE),
    ("rover_ws/tools/", Subsystem.ROS_WORKSPACE),
    ("rover_ws/install/", Subsystem.ROS_WORKSPACE),
    # Tests.
    ("backend/tests/", Subsystem.TESTS),
    ("rover_ws/tests/", Subsystem.TESTS),
    # Tooling + docs + CI.
    ("docs/", Subsystem.DOCS),
    (".github/workflows/", Subsystem.CI),
    (".github/", Subsystem.CI),
    ("tools/", Subsystem.VERIFICATION),
    ("scripts/", Subsystem.CI),
    # Evidence + analytics outputs.
    ("evidence/scenarios/", Subsystem.EVIDENCE),
    ("evidence/runtime/", Subsystem.EVIDENCE),
    ("incidents/", Subsystem.EVIDENCE),
    ("verification/", Subsystem.EVIDENCE),
    ("foxglove/", Subsystem.REPLAY_REVIEW),
    ("runs/", Subsystem.EVIDENCE),
    ("qualification/", Subsystem.RUNTIME_VALIDATION),
    ("reliability-impact/", Subsystem.RELIABILITY_IMPACT),
    ("reliability-baselines/", Subsystem.RELIABILITY_IMPACT),
)


def classify_path(path: str) -> Subsystem:
    """Return the subsystem that owns ``path``.

    The function is OS-independent (converts to POSIX form) and
    deterministic (first matching prefix wins). Empty / whitespace
    paths map to :attr:`Subsystem.UNKNOWN`.
    """

    if not isinstance(path, str):
        return Subsystem.UNKNOWN
    cleaned = path.strip().replace("\\", "/")
    # Strip ``./`` relative-path prefixes (and stray leading slashes)
    # while preserving leading-dot directories such as ``.github/``.
    while cleaned.startswith("./"):
        cleaned = cleaned[2:]
    while cleaned.startswith("/"):
        cleaned = cleaned[1:]
    if not cleaned:
        return Subsystem.UNKNOWN
    # Use PurePosixPath only to normalise duplicate slashes.
    normalised = str(PurePosixPath(cleaned))
    for prefix, subsystem in _PREFIX_RULES:
        if normalised == prefix.rstrip("/"):
            return subsystem
        if normalised.startswith(prefix):
            return subsystem
    return Subsystem.UNKNOWN
