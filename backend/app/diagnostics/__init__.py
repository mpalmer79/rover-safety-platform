"""Runtime diagnostics core.

Pure-logic monitors used by the ROS ``rover_runtime_diagnostics``
package and by validation tools. Each monitor accepts inputs (topic
observations, bridge presence flags, watchdog state) and produces a
structured :class:`HealthReport` that downstream code (a ROS node,
a Foxglove dashboard, or a test) can consume.

The monitors do not own safety logic; they describe operational
liveliness. A diagnostics monitor reporting "unhealthy" never trips
the safety supervisor — the supervisor reacts to the underlying
inputs, not to the diagnostics.
"""

from app.diagnostics.bridge_health import (
    BridgeHealthMonitor,
    BridgeHealthReport,
    BridgeTopicObservation,
)
from app.diagnostics.runtime_summary import (
    HealthReport,
    HealthSeverity,
    RuntimeSummary,
    aggregate_health,
)
from app.diagnostics.topic_monitor import (
    TopicFreshnessMonitor,
    TopicFreshnessReport,
    TopicObservation,
    TopicSpec,
    DEFAULT_TOPIC_SPECS,
)

__all__ = [
    "BridgeHealthMonitor",
    "BridgeHealthReport",
    "BridgeTopicObservation",
    "DEFAULT_TOPIC_SPECS",
    "HealthReport",
    "HealthSeverity",
    "RuntimeSummary",
    "TopicFreshnessMonitor",
    "TopicFreshnessReport",
    "TopicObservation",
    "TopicSpec",
    "aggregate_health",
]
