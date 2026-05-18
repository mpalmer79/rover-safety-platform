"""Cross-cutting artefact validators for the rover platform.

This package is the home for validators whose inputs are artefacts
produced or consumed across multiple subsystems: run directories,
``events.jsonl``, the ``ros_gz_bridge`` YAML, the rover URDF, and the
scenario suite. They are pure-logic, ROS-free, and CLI-runnable via
``tools/``.

Feature-specific validators live with their feature package, not
here. A validator over a mission proposal belongs in
``app.mission_proposal``; a validator over generated skill code
belongs in ``app.skill_authoring``. See
``docs/adr/ADR-010-validator-module-co-location.md`` for the
boundary and the reasoning.

Each validator in this package exposes:

* a single dataclass result type (e.g. :class:`ReplayValidationResult`),
* a ``validate_*`` function returning that result,
* a ``main()`` for CLI invocation that prints a summary and exits with
  a non-zero status if the validator found problems.
"""

from app.validation.bridge_validator import (
    BridgeValidationResult,
    validate_bridge_yaml,
)
from app.validation.event_validator import (
    EventValidationResult,
    validate_events_file,
    validate_events_iter,
)
from app.validation.mission_validator import (
    MissionRunValidationResult,
    validate_mission_run,
)
from app.validation.replay_validator import (
    ReplayValidationResult,
    validate_run_directory,
)
from app.validation.scenario_suite import (
    ScenarioCase,
    ScenarioOutcome,
    SuiteResult,
    builtin_scenarios,
    run_scenario_suite,
)
from app.validation.tf_validator import (
    TfValidationResult,
    validate_urdf_tf_tree,
)
from app.validation.safety_pipeline_validator import (
    SafetyPipelineResult,
    validate_safety_pipeline,
)

__all__ = [
    "BridgeValidationResult",
    "EventValidationResult",
    "MissionRunValidationResult",
    "ReplayValidationResult",
    "SafetyPipelineResult",
    "ScenarioCase",
    "ScenarioOutcome",
    "SuiteResult",
    "TfValidationResult",
    "builtin_scenarios",
    "run_scenario_suite",
    "validate_bridge_yaml",
    "validate_events_file",
    "validate_events_iter",
    "validate_mission_run",
    "validate_run_directory",
    "validate_safety_pipeline",
    "validate_urdf_tf_tree",
]
