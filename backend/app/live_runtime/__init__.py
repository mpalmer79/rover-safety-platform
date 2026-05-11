"""Phase 14 live runtime evidence library.

Pure-logic helpers that classify, validate, and process the artefacts
produced by a self-hosted ROS 2 Jazzy + Gazebo Harmonic run. The
library does not import :mod:`rclpy` and runs without ROS so that
honesty guardrails (a static fixture cannot be relabelled as
bag-backed; an unattached runner cannot claim qualification) are
testable on a GitHub-hosted CI runner.

The modules pair with the rover_ws live runtime tools:

* ``bag_manifest`` classifies a candidate bag directory.
* ``runner_profile`` loads and validates self-hosted runner profiles.
* ``scenario_plan`` loads live scenario plans (smoke / qualification).
* ``evidence_processor`` constructs the canonical evidence record and
  refuses to upgrade missing or partial bags into ``bag_backed``.
* ``maturity_baseline`` records whether a bag-backed live run has
  ever been observed.
"""

from app.live_runtime.bag_manifest import (
    BagChunk,
    BagManifest,
    BagStatus,
    inspect_bag_directory,
)
from app.live_runtime.evidence_processor import (
    EvidenceMode,
    LiveRuntimeEvidence,
    process_evidence,
    render_evidence_md,
)
from app.live_runtime.maturity_baseline import (
    MaturityBaseline,
    MaturityStatus,
    assert_baseline_honest,
    load_maturity_baseline,
    new_not_established_baseline,
)
from app.live_runtime.runner_profile import (
    QualificationOutcome,
    RunnerProfile,
    RunnerStatus,
    load_runner_profile,
    validate_runner_profile,
)
from app.live_runtime.scenario_plan import (
    LiveScenarioPlan,
    load_scenario_plan,
    validate_scenario_plan,
)

__all__ = [
    "BagChunk",
    "BagManifest",
    "BagStatus",
    "EvidenceMode",
    "LiveRuntimeEvidence",
    "LiveScenarioPlan",
    "MaturityBaseline",
    "MaturityStatus",
    "QualificationOutcome",
    "RunnerProfile",
    "RunnerStatus",
    "assert_baseline_honest",
    "inspect_bag_directory",
    "load_maturity_baseline",
    "load_runner_profile",
    "load_scenario_plan",
    "new_not_established_baseline",
    "process_evidence",
    "render_evidence_md",
    "validate_runner_profile",
    "validate_scenario_plan",
]
