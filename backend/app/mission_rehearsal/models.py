"""Dataclasses, status enums, and the verbatim disclaimer.

The platform is **not safety-certified**. Every status enum and
dataclass is exposed via :mod:`app.mission_rehearsal` so callers do
not have to reach into private modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Optional


MISSION_REHEARSAL_VERSION: str = "phase16-1"

MISSION_REHEARSAL_DISCLAIMER: str = (
    "This rehearsal pipeline is simulation-only and does not "
    "authorize live robot execution or safety certification."
)


# ---------------------------------------------------------------------
# Status vocabularies.
# ---------------------------------------------------------------------


class RehearsalStatus(str, Enum):
    CREATED = "created"
    VALIDATED = "validated"
    APPROVED = "approved"
    REHEARSING = "rehearsing"
    PAUSED = "paused"
    REJECTED = "rejected"
    ABORTED = "aborted"
    COMPLETED = "completed"


REHEARSAL_STATUSES: tuple[str, ...] = tuple(s.value for s in RehearsalStatus)


class RehearsalDecisionStatus(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"


class RehearsalSafetyStatus(str, Enum):
    SAFE = "safe"
    GUARDED = "guarded"
    UNSAFE_REJECTED = "unsafe_rejected"
    REQUIRES_REVIEW = "requires_review"
    NOT_EVALUATED = "not_evaluated"


class RehearsalFailureReason(str, Enum):
    UNSAFE_SPEED = "unsafe_speed"
    RESTRICTED_ZONE = "restricted_zone"
    DIRECT_ACTUATOR_COMMAND = "direct_actuator_command"
    UNBOUNDED_LOOP = "unbounded_loop"
    MISSING_STOP_CONDITION = "missing_stop_condition"
    MISSING_SUPERVISOR_APPROVAL = "missing_supervisor_approval"
    UNSAFE_PROPOSAL_SOURCE = "unsafe_proposal_source"
    UNVALIDATED_LLM_PROPOSAL = "unvalidated_llm_proposal"
    MALFORMED_MISSION_GRAPH = "malformed_mission_graph"
    SAFETY_OVERRIDE = "safety_override"
    ESTOP_OVERRIDE = "estop_override"
    OUT_OF_RANGE_PARAMETER = "out_of_range_parameter"
    INVALID_STATE_TRANSITION = "invalid_state_transition"


REHEARSAL_FAILURE_REASONS: tuple[str, ...] = tuple(
    r.value for r in RehearsalFailureReason
)


class RehearsalEventType(str, Enum):
    MISSION = "mission"
    VALIDATION = "validation"
    SUPERVISOR = "supervisor"
    MOTION = "motion"
    SAFETY = "safety"
    REPLAY = "replay"
    ANALYTICS = "analytics"
    AUDIT = "audit"


REHEARSAL_EVENT_TYPES: tuple[str, ...] = tuple(
    e.value for e in RehearsalEventType
)


class RehearsalEvidenceStatus(str, Enum):
    SIMULATED = "simulated"
    STATIC_ONLY = "static_only"
    NOT_EVALUATED = "not_evaluated"


# ---------------------------------------------------------------------
# Models.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class MissionRehearsalRequest:
    request_id: str
    description: str
    mission_id: str
    proposal_source: str
    requested_at_utc: str
    seed: int = 42
    operator: str = ""
    odd_profile_id: str = "default-warehouse"
    notes: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RehearsalWaypoint:
    waypoint_id: str
    label: str
    stage_kind: str   # "move" | "patrol" | "inspect" | "wait" | "stop" | "dock"
    bounded_distance_m: float = 0.0
    bounded_angle_deg: float = 0.0
    bounded_speed_mps: float = 0.0


@dataclass(frozen=True)
class MissionRehearsalPlan:
    mission_id: str
    request_id: str
    proposal_source: str
    waypoints: tuple[RehearsalWaypoint, ...]
    safety_constraints: tuple[str, ...]
    requested_topics: tuple[str, ...]
    forbidden_topics: tuple[str, ...]
    odd_profile_id: str
    deterministic_hash: str
    risk_band: str  # "low" | "guarded" | "restricted" | "blocked"
    notes: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class MissionRehearsalEvent:
    event_id: str
    mission_id: str
    event_type: str  # RehearsalEventType value
    event_subtype: str
    event_time_ns: int
    source_phase: str
    severity: str  # "info" | "warning" | "rejection"
    description: str
    deterministic_hash: str
    payload: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class MissionRehearsalDecision:
    decision_id: str
    decision_status: str  # RehearsalDecisionStatus value
    safety_status: str  # RehearsalSafetyStatus value
    rationale: tuple[str, ...]
    rejected_reasons: tuple[str, ...]
    allowed_topics: tuple[str, ...]
    forbidden_topics: tuple[str, ...]
    requires_human_review: bool
    decided_at_utc: str


@dataclass(frozen=True)
class MissionRehearsalTimeline:
    mission_id: str
    transitions: tuple[tuple[str, str, str], ...]   # (from, to, reason)
    events: tuple[MissionRehearsalEvent, ...]
    rendered_markdown: str
    rendered_mermaid: str


@dataclass(frozen=True)
class MissionRehearsalRuntime:
    mission_id: str
    final_status: str  # RehearsalStatus value
    final_failure_reason: str
    safety_status: str  # RehearsalSafetyStatus value
    events: tuple[MissionRehearsalEvent, ...]
    timeline: MissionRehearsalTimeline
    deterministic_hash: str
    started_at_utc: str
    finished_at_utc: str


@dataclass(frozen=True)
class MissionRehearsalReplayBundle:
    mission_id: str
    evidence_status: str   # RehearsalEvidenceStatus value
    bag_backed: bool
    replay_markers: tuple[Mapping[str, object], ...]
    review_status: str   # "passed" | "partial" | "rejected" | "not_evaluated"
    rendered_markdown: str
    deterministic_hash: str
    notes: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class MissionRehearsalAnalyticsResult:
    mission_id: str
    rehearsal_count: int
    approved_count: int
    rejected_count: int
    aborted_count: int
    completed_count: int
    supervisor_rejection_count: int
    validator_rejection_count: int
    deterministic_replay_stable: bool
    notes: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class MissionRehearsalAudit:
    request: MissionRehearsalRequest
    plan: Optional[MissionRehearsalPlan]
    validation_diagnostics: tuple[Mapping[str, object], ...]
    decision: MissionRehearsalDecision
    runtime: Optional[MissionRehearsalRuntime]
    replay: Optional[MissionRehearsalReplayBundle]
    analytics: Optional[MissionRehearsalAnalyticsResult]
    final_status: str
    final_failure_reason: str
    safety_status: str
    generated_at_utc: str
    disclaimer: str = MISSION_REHEARSAL_DISCLAIMER
