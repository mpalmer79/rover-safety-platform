"""Safety subsystem.

The supervisor is the only authority that produces ``AuthorizedMotionCommand``
values. Other modules in this package are its collaborators: arbitration
clamps motion to per-state limits, freshness gates enforce input
liveliness, the confidence scorer and the watchdog registry expose
observable signals, and ``transitions`` defines the legal state graph.
"""

from app.safety.arbitration import MotionArbiter
from app.safety.confidence import ConfidenceReport, ConfidenceScorer
from app.safety.freshness import FreshnessEvaluator, FreshnessReport, FreshnessThresholds
from app.safety.supervisor import SafetySupervisor, SupervisorEvaluation, SupervisorInputs
from app.safety.transitions import (
    ALLOWED_TRANSITIONS,
    INVALID_TRANSITION_REASON,
    TransitionRequest,
    TransitionResult,
    is_transition_allowed,
)
from app.safety.watchdog import Watchdog, WatchdogConfig, WatchdogRegistry, WatchdogReport

__all__ = [
    "ALLOWED_TRANSITIONS",
    "ConfidenceReport",
    "ConfidenceScorer",
    "FreshnessEvaluator",
    "FreshnessReport",
    "FreshnessThresholds",
    "INVALID_TRANSITION_REASON",
    "MotionArbiter",
    "SafetySupervisor",
    "SupervisorEvaluation",
    "SupervisorInputs",
    "TransitionRequest",
    "TransitionResult",
    "Watchdog",
    "WatchdogConfig",
    "WatchdogRegistry",
    "WatchdogReport",
    "is_transition_allowed",
]
