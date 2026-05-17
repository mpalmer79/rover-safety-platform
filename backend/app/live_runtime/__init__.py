"""Live runtime runner profiles, bag manifests, maturity reports."""

from __future__ import annotations

from .bag_manifest import (
    bag_manifest_from_dict,
    bag_manifest_is_bag_backed,
    build_not_executed_manifest,
    degrade_to_partial_if_missing,
    load_bag_manifest,
    validate_bag_manifest,
    write_bag_manifest,
)
from .evidence_capture import (
    build_not_executed_bundle,
    detect_environment_block_reason,
    evidence_bundle_missing_files,
    evidence_bundle_required_files,
    init_run_directory,
    write_evidence_bundle,
)
from .maturity import aggregate_maturity
from .models import (
    BAG_STATUS_BAG_BACKED,
    BAG_STATUS_INVALID,
    BAG_STATUS_MISSING_BAG,
    BAG_STATUS_NOT_EXECUTED,
    BAG_STATUS_PARTIAL,
    BagManifest,
    LIVE_RUNTIME_DISCLAIMER,
    LIVE_RUN_STATUS_NOT_EXECUTED,
    LIVE_RUN_STATUS_PASSED,
    LiveRunSummary,
    REQUIRED_EVIDENCE_FILES,
    RunnerProfile,
)
from .report import (
    maturity_report_to_dict,
    render_maturity_markdown,
    write_maturity_json,
    write_maturity_markdown,
)
from .runner_profile import (
    load_runner_profile,
    runner_profile_from_dict,
    runner_profile_schema,
    runner_profile_to_dict,
    runner_supports_live_execution,
    validate_runner_profile,
    write_runner_profile,
    write_runner_profile_schema,
)
from .scenario_plan import (
    load_scenario_plan,
    scenario_plan_from_dict,
    scenario_plan_to_dict,
    validate_scenario_plan,
)

__all__ = [
    "BAG_STATUS_BAG_BACKED",
    "BAG_STATUS_INVALID",
    "BAG_STATUS_MISSING_BAG",
    "BAG_STATUS_NOT_EXECUTED",
    "BAG_STATUS_PARTIAL",
    "BagManifest",
    "LIVE_RUNTIME_DISCLAIMER",
    "LIVE_RUN_STATUS_NOT_EXECUTED",
    "LIVE_RUN_STATUS_PASSED",
    "LiveRunSummary",
    "REQUIRED_EVIDENCE_FILES",
    "RunnerProfile",
    "aggregate_maturity",
    "bag_manifest_from_dict",
    "bag_manifest_is_bag_backed",
    "build_not_executed_bundle",
    "build_not_executed_manifest",
    "degrade_to_partial_if_missing",
    "detect_environment_block_reason",
    "evidence_bundle_missing_files",
    "evidence_bundle_required_files",
    "init_run_directory",
    "load_bag_manifest",
    "load_runner_profile",
    "load_scenario_plan",
    "maturity_report_to_dict",
    "render_maturity_markdown",
    "runner_profile_from_dict",
    "runner_profile_schema",
    "runner_profile_to_dict",
    "runner_supports_live_execution",
    "scenario_plan_from_dict",
    "scenario_plan_to_dict",
    "validate_bag_manifest",
    "validate_runner_profile",
    "validate_scenario_plan",
    "write_bag_manifest",
    "write_evidence_bundle",
    "write_maturity_json",
    "write_maturity_markdown",
    "write_runner_profile",
    "write_runner_profile_schema",
]
