"""Phase 4 / Phase 5 runtime validation + qualification library.

Pure-logic helpers shared by the ``rover_ws/tools/*_probe.py`` CLIs,
the orchestrator ``live_runtime_validator.py``, and the Phase-5
qualification orchestrator ``qualified_runtime_run.py``. The library
does **not** import :mod:`rclpy`; the tools wrap it with the ROS-side
plumbing.

Responsibilities:

* declare the expected runtime topics, TF frames, and node graph;
* render check results into the canonical Phase-3 status vocabulary
  (``passed`` / ``failed`` / ``partial`` / ``skipped`` /
  ``not_executed``);
* produce the JSON + Markdown evidence shapes documented in
  ``docs/RUNTIME_VALIDATION_RUNBOOK.md``,
  ``docs/RUNTIME_QUALIFICATION_RUNBOOK.md``, and the reports;
* perform the workspace-level static checks the tools fall back on
  when ROS / Gazebo are unavailable;
* host qualification, qualification scenario validation, baseline
  comparison, regression detection, and evidence indexing (Phase 5).

The library is intentionally narrow. Anything that requires a live
ROS graph lives in the per-probe CLI; anything that can be evaluated
from the workspace artefacts lives here so it is testable without
ROS.
"""

from app.runtime_validation.baselines import (
    BaselineComparison,
    BaselineDelta,
    DeltaSeverity,
    baseline_from_evidence,
    compare_baseline,
    load_baseline,
    render_comparison_md,
    write_baseline,
)
from app.runtime_validation.evidence_index import (
    EvidenceIndex,
    EvidenceIndexRow,
    build_evidence_index,
    render_evidence_index_md,
    write_evidence_index,
)
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
from app.runtime_validation.host_qualification import (
    HostCheck,
    HostQualificationResult,
    parse_os_release,
    qualify_host,
    render_host_qualification_md,
)
from app.runtime_validation.qualification_report import (
    QualificationCheck,
    QualificationReport,
    ScenarioOutcome,
    render_live_runtime_status_md,
    render_qualification_summary_md,
)
from app.runtime_validation.qualification_scenarios import (
    QualificationScenario,
    ScenarioValidation,
    load_scenario_pack_from_dir,
    parse_scenario,
)
from app.runtime_validation.regression import (
    RegressionFinding,
    RegressionReport,
    detect_regressions,
    render_regression_md,
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
    "BaselineComparison",
    "BaselineDelta",
    "DeltaSeverity",
    "EXPECTED_FRAMES",
    "EXPECTED_NODES",
    "EXPECTED_OBSERVABILITY_NODES",
    "EXPECTED_ROOT_FRAME",
    "EXPECTED_SAFETY_NODES",
    "EXPECTED_SIMULATION_NODES",
    "EXPECTED_TOPICS",
    "EvidenceIndex",
    "EvidenceIndexRow",
    "EvidenceLayout",
    "FrameExpectation",
    "HostCheck",
    "HostQualificationResult",
    "NodeExpectation",
    "QualificationCheck",
    "QualificationReport",
    "QualificationScenario",
    "RUNTIME_EVIDENCE_FILES",
    "RegressionFinding",
    "RegressionReport",
    "RuntimeCheck",
    "RuntimeReport",
    "ScenarioOutcome",
    "ScenarioValidation",
    "StaticValidationResult",
    "TopicDirection",
    "TopicExpectation",
    "baseline_from_evidence",
    "build_evidence_index",
    "compare_baseline",
    "detect_regressions",
    "load_baseline",
    "load_scenario_pack_from_dir",
    "new_runtime_run_id",
    "parse_os_release",
    "parse_scenario",
    "qualify_host",
    "render_comparison_md",
    "render_evidence_index_md",
    "render_host_qualification_md",
    "render_live_runtime_status_md",
    "render_qualification_summary_md",
    "render_regression_md",
    "render_runtime_report_md",
    "run_static_validation",
    "write_baseline",
    "write_evidence_index",
]
