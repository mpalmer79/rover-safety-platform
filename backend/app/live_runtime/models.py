"""Typed models, enums, and constants for the Phase 13 live-runtime layer.

The platform is **not safety-certified**. This module defines the
read-only data model used by the live-runtime evidence pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


LIVE_RUNTIME_DISCLAIMER: str = (
    "This project is not safety-certified. Live runtime evidence "
    "demonstrates engineering qualification discipline; it is not "
    "a regulatory artefact."
)


# Live-run status vocabulary.
LIVE_RUN_STATUS_PASSED: str = "passed"
LIVE_RUN_STATUS_FAILED: str = "failed"
LIVE_RUN_STATUS_PARTIAL: str = "partial"
LIVE_RUN_STATUS_SKIPPED: str = "skipped"
LIVE_RUN_STATUS_NOT_EXECUTED: str = "not_executed"

LIVE_RUN_STATUSES: tuple[str, ...] = (
    LIVE_RUN_STATUS_PASSED,
    LIVE_RUN_STATUS_FAILED,
    LIVE_RUN_STATUS_PARTIAL,
    LIVE_RUN_STATUS_SKIPPED,
    LIVE_RUN_STATUS_NOT_EXECUTED,
)


# Bag-status vocabulary.
BAG_STATUS_BAG_BACKED: str = "bag_backed"
BAG_STATUS_MISSING_BAG: str = "missing_bag"
BAG_STATUS_PARTIAL: str = "partial"
BAG_STATUS_NOT_EXECUTED: str = "not_executed"
BAG_STATUS_INVALID: str = "invalid"

BAG_STATUSES: tuple[str, ...] = (
    BAG_STATUS_BAG_BACKED,
    BAG_STATUS_MISSING_BAG,
    BAG_STATUS_PARTIAL,
    BAG_STATUS_NOT_EXECUTED,
    BAG_STATUS_INVALID,
)


# Runner qualification status vocabulary.
QUALIFICATION_STATUS_QUALIFIED: str = "qualified"
QUALIFICATION_STATUS_PARTIAL: str = "partial"
QUALIFICATION_STATUS_NOT_QUALIFIED: str = "not_qualified"
QUALIFICATION_STATUS_UNKNOWN: str = "unknown"


# Required runtime evidence files.
REQUIRED_EVIDENCE_FILES: tuple[str, ...] = (
    "metadata.json",
    "runner-profile.json",
    "live-run-summary.json",
    "bag-manifest.json",
    "qualification-summary.md",
    "known-limitations.md",
)


@dataclass(frozen=True)
class RunnerProfile:
    """Profile of the host that executes (or would execute) live runs."""

    runner_id: str
    host_os: str
    ros_distro: str
    gazebo_version: str
    colcon_version: str
    workspace_path: str
    supports_gazebo: bool
    supports_rosbag2: bool
    supports_foxglove_optional: bool
    runner_labels: tuple[str, ...] = ()
    last_qualified_at: str = ""
    qualification_status: str = QUALIFICATION_STATUS_UNKNOWN
    known_limitations: tuple[str, ...] = ()


@dataclass(frozen=True)
class ScenarioPlanEntry:
    """One scenario in a live qualification plan."""

    scenario_id: str
    purpose: str
    launch_file: str
    expected_topics: tuple[str, ...]
    expected_safety_states: tuple[str, ...]
    expected_events: tuple[str, ...]
    required_bag_topics: tuple[str, ...]
    timeout_seconds: int
    evidence_required: tuple[str, ...]
    failure_mode: str


@dataclass(frozen=True)
class ScenarioPlan:
    """A named collection of scenario entries."""

    plan_id: str
    description: str
    entries: tuple[ScenarioPlanEntry, ...]


@dataclass(frozen=True)
class BagManifest:
    """Per-run bag-recording manifest.

    For ``bag_status == BAG_STATUS_NOT_EXECUTED`` the bag list and
    metadata path may be empty, but ``not_executed_reason`` must
    explain why. For ``bag_status == BAG_STATUS_BAG_BACKED`` the
    bag list and metadata path must be non-empty (and the validator
    additionally checks they exist on disk).
    """

    run_id: str
    scenario_id: str
    bag_status: str
    bag_format: str
    bag_paths: tuple[str, ...]
    metadata_yaml_path: str
    topic_inventory: tuple[str, ...]
    message_counts: Mapping[str, int]
    start_time: str
    end_time: str
    duration_seconds: float
    missing_required_topics: tuple[str, ...]
    validation_status: str
    known_limitations: tuple[str, ...] = ()
    not_executed_reason: str = ""


@dataclass(frozen=True)
class LiveRunSummary:
    """High-level outcome of a single live qualification run."""

    run_id: str
    runner_id: str
    plan_id: str
    scenario_ids: tuple[str, ...]
    started_at: str
    finished_at: str
    status: str
    bag_status: str
    not_executed_reason: str = ""
    notes: str = ""


@dataclass(frozen=True)
class LiveRuntimeMaturityCounters:
    bag_backed: int = 0
    missing_bag: int = 0
    partial: int = 0
    not_executed: int = 0
    invalid: int = 0


@dataclass(frozen=True)
class LiveRuntimeMaturityReport:
    """Aggregated view of every live run found on disk.

    All numeric fields are derived directly from the on-disk
    evidence; the report itself is read-only.
    """

    generated_at_utc: str
    evidence_root: str
    runs_total: int
    runs_by_status: Mapping[str, int]
    bag_counters: LiveRuntimeMaturityCounters
    required_topic_coverage: Mapping[str, int]
    scenario_coverage: Mapping[str, int]
    runner_status: str
    latest_run_id: str
    latest_run_status: str
    replay_review_integration: str
    analytics_integration: str
    programme_review_integration: str
    known_limitations: tuple[str, ...] = ()
    next_actions: tuple[str, ...] = ()


__all__ = [
    "LIVE_RUNTIME_DISCLAIMER",
    "LIVE_RUN_STATUS_PASSED",
    "LIVE_RUN_STATUS_FAILED",
    "LIVE_RUN_STATUS_PARTIAL",
    "LIVE_RUN_STATUS_SKIPPED",
    "LIVE_RUN_STATUS_NOT_EXECUTED",
    "LIVE_RUN_STATUSES",
    "BAG_STATUS_BAG_BACKED",
    "BAG_STATUS_MISSING_BAG",
    "BAG_STATUS_PARTIAL",
    "BAG_STATUS_NOT_EXECUTED",
    "BAG_STATUS_INVALID",
    "BAG_STATUSES",
    "QUALIFICATION_STATUS_QUALIFIED",
    "QUALIFICATION_STATUS_PARTIAL",
    "QUALIFICATION_STATUS_NOT_QUALIFIED",
    "QUALIFICATION_STATUS_UNKNOWN",
    "REQUIRED_EVIDENCE_FILES",
    "RunnerProfile",
    "ScenarioPlanEntry",
    "ScenarioPlan",
    "BagManifest",
    "LiveRunSummary",
    "LiveRuntimeMaturityCounters",
    "LiveRuntimeMaturityReport",
]
