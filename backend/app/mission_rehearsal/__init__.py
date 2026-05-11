"""Phase 16: governed mission-to-rehearsal pipeline.

The platform is **not safety-certified**. The mission rehearsal
layer is a simulation-only deterministic pipeline that drives a
mission proposal through the Phase 14A compiler, the Phase 15A/15B
sanitizer / validator gates, an explicit safety supervisor
inspection, a deterministic runtime state machine, and into the
replay + analytics bridge. Nothing here runs on real hardware,
publishes to ROS, opens a network socket, or executes user code.

Public flow::

    MissionRehearsalRequest
      → rehearsal_plan.build_plan       (mission + safety inputs)
      → rehearsal_validator.validate    (mission graph + safety rules)
      → rehearsal_supervisor.review     (authority chokepoint)
      → rehearsal_state_machine         (deterministic transitions)
      → rehearsal_runtime.run           (deterministic event stream)
      → rehearsal_replay_bridge         (replay-review artefacts)
      → rehearsal_analytics_bridge      (analytics artefact)
      → rehearsal_audit.build_audit
      → rehearsal_reporter.write_audit_files
"""

from __future__ import annotations

from .models import (
    MISSION_REHEARSAL_DISCLAIMER,
    MISSION_REHEARSAL_VERSION,
    MissionRehearsalAnalyticsResult,
    MissionRehearsalAudit,
    MissionRehearsalDecision,
    MissionRehearsalEvent,
    MissionRehearsalPlan,
    MissionRehearsalReplayBundle,
    MissionRehearsalRequest,
    MissionRehearsalRuntime,
    MissionRehearsalTimeline,
    REHEARSAL_FAILURE_REASONS,
    REHEARSAL_STATUSES,
    REHEARSAL_EVENT_TYPES,
    RehearsalDecisionStatus,
    RehearsalEventType,
    RehearsalEvidenceStatus,
    RehearsalFailureReason,
    RehearsalSafetyStatus,
    RehearsalStatus,
    RehearsalWaypoint,
)
from .rehearsal_analytics_bridge import build_analytics_result
from .rehearsal_audit import (
    audit_to_dict,
    build_audit_bundle,
    render_rehearsal_report_markdown,
)
from .rehearsal_capture import capture_events
from .rehearsal_events import (
    build_event,
    deterministic_hash,
)
from .rehearsal_plan import (
    BoundedMotionLimits,
    build_plan,
)
from .rehearsal_replay_bridge import (
    build_replay_bundle,
    render_replay_review_markdown,
)
from .rehearsal_reporter import write_audit_files
from .rehearsal_runtime import run_rehearsal
from .rehearsal_safety import (
    REHEARSAL_FORBIDDEN_PATTERNS,
    SAFETY_LIMITS,
    classify_safety_status,
)
from .rehearsal_state_machine import (
    REHEARSAL_TRANSITIONS,
    StateMachineError,
    next_status,
    valid_transitions,
)
from .rehearsal_supervisor import review_plan
from .rehearsal_timeline import (
    build_timeline,
    render_timeline_markdown,
    render_timeline_mermaid,
)
from .rehearsal_validator import (
    validate_plan,
    validate_request,
)


__all__ = [
    "BoundedMotionLimits",
    "MISSION_REHEARSAL_DISCLAIMER",
    "MISSION_REHEARSAL_VERSION",
    "MissionRehearsalAnalyticsResult",
    "MissionRehearsalAudit",
    "MissionRehearsalDecision",
    "MissionRehearsalEvent",
    "MissionRehearsalPlan",
    "MissionRehearsalReplayBundle",
    "MissionRehearsalRequest",
    "MissionRehearsalRuntime",
    "MissionRehearsalTimeline",
    "REHEARSAL_EVENT_TYPES",
    "REHEARSAL_FAILURE_REASONS",
    "REHEARSAL_FORBIDDEN_PATTERNS",
    "REHEARSAL_STATUSES",
    "REHEARSAL_TRANSITIONS",
    "RehearsalDecisionStatus",
    "RehearsalEventType",
    "RehearsalEvidenceStatus",
    "RehearsalFailureReason",
    "RehearsalSafetyStatus",
    "RehearsalStatus",
    "RehearsalWaypoint",
    "SAFETY_LIMITS",
    "StateMachineError",
    "audit_to_dict",
    "build_analytics_result",
    "build_audit_bundle",
    "build_event",
    "build_plan",
    "build_replay_bundle",
    "build_timeline",
    "capture_events",
    "classify_safety_status",
    "deterministic_hash",
    "next_status",
    "render_rehearsal_report_markdown",
    "render_replay_review_markdown",
    "render_timeline_markdown",
    "render_timeline_mermaid",
    "review_plan",
    "run_rehearsal",
    "valid_transitions",
    "validate_plan",
    "validate_request",
    "write_audit_files",
]
