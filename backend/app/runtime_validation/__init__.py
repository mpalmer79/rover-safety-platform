"""Phase 4 live runtime validation library.

Pure-logic helpers shared by the ``rover_ws/tools/*_probe.py`` CLIs
and the orchestrator ``live_runtime_validator.py``. The library does
**not** import :mod:`rclpy`; the tools wrap it with the ROS-side
plumbing.

Responsibilities:

* declare the expected runtime topics, TF frames, and node graph;
* render check results into the canonical Phase-3 status vocabulary
  (``passed`` / ``failed`` / ``partial`` / ``skipped`` /
  ``not_executed``);
* produce the JSON + Markdown evidence shapes documented in
  ``docs/RUNTIME_VALIDATION_RUNBOOK.md`` and the report;
* perform the workspace-level static checks the tools fall back on
  when ROS / Gazebo are unavailable.

The library is intentionally narrow. Anything that requires a live
ROS graph lives in the per-probe CLI; anything that can be evaluated
from the workspace artefacts lives here so it is testable without
ROS.
"""

from app.runtime_validation.evidence_layout import (
    EvidenceLayout,
    RUNTIME_EVIDENCE_FILES,
    new_runtime_run_id,
)
from app.runtime_validation.expected_nodes import (
    EXPECTED_NODES,
    EXPECTED_OBSERVABILITY_NODES,
    EXPECTED_SAFETY_NODES,
    EXPECTED_SIMULATION_NODES,
    NodeExpectation,
)
from app.runtime_validation.expected_tf_frames import (
    EXPECTED_FRAMES,
    EXPECTED_ROOT_FRAME,
    FrameExpectation,
)
from app.runtime_validation.expected_topics import (
    EXPECTED_TOPICS,
    TopicDirection,
    TopicExpectation,
)
from app.runtime_validation.report_renderer import (
    RuntimeCheck,
    RuntimeReport,
    render_runtime_report_md,
)
from app.runtime_validation.static_validator import (
    StaticValidationResult,
    run_static_validation,
)

__all__ = [
    "EXPECTED_FRAMES",
    "EXPECTED_NODES",
    "EXPECTED_OBSERVABILITY_NODES",
    "EXPECTED_ROOT_FRAME",
    "EXPECTED_SAFETY_NODES",
    "EXPECTED_SIMULATION_NODES",
    "EXPECTED_TOPICS",
    "EvidenceLayout",
    "FrameExpectation",
    "NodeExpectation",
    "RUNTIME_EVIDENCE_FILES",
    "RuntimeCheck",
    "RuntimeReport",
    "StaticValidationResult",
    "TopicDirection",
    "TopicExpectation",
    "new_runtime_run_id",
    "render_runtime_report_md",
    "run_static_validation",
]
