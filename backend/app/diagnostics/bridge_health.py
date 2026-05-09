"""Bridge health monitor.

Tracks whether the documented bridged topics have ever been observed
and whether their stream remains alive within configured timeouts.
The monitor does not parse the YAML — :func:`validate_bridge_yaml`
does that statically. This monitor focuses on **runtime** evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.diagnostics.runtime_summary import HealthReport, HealthSeverity
from app.diagnostics.topic_monitor import TopicFreshnessMonitor


# Topics that, by ADR-002 + ADR-004, must be present whenever Gazebo is
# running and the bridge is healthy.
_REQUIRED_BRIDGED_TOPICS: tuple[str, ...] = (
    "/clock",
    "/scan",
    "/imu",
    "/odom",
    "/contact",
    "/cmd_vel_authorized",
)


@dataclass(frozen=True)
class BridgeTopicObservation:
    topic: str
    is_advertised: bool
    last_observed_ms: int | None
    samples: int


@dataclass(frozen=True)
class BridgeHealthReport:
    severity: HealthSeverity
    summary: str
    per_topic: tuple[HealthReport, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity.value,
            "summary": self.summary,
            "per_topic": [r.to_dict() for r in self.per_topic],
        }


class BridgeHealthMonitor:
    """Aggregates topic-level evidence into bridge-level health.

    The monitor delegates per-topic age tracking to
    :class:`TopicFreshnessMonitor` and adds a coarse "is the bridge
    advertising at all?" check. The latter requires the consuming ROS
    node to call :meth:`set_advertised` after polling
    ``ros2 topic list`` (or ``rclpy.Node.get_topic_names_and_types``).
    """

    def __init__(self, freshness: TopicFreshnessMonitor) -> None:
        self._freshness = freshness
        self._advertised: dict[str, bool] = {t: False for t in _REQUIRED_BRIDGED_TOPICS}

    @property
    def required_topics(self) -> tuple[str, ...]:
        return _REQUIRED_BRIDGED_TOPICS

    def set_advertised(self, *, topic: str, advertised: bool) -> None:
        if topic in self._advertised:
            self._advertised[topic] = bool(advertised)

    def report(self, *, now_ms: int) -> BridgeHealthReport:
        per_topic: list[HealthReport] = []
        freshness_report = self._freshness.report(now_ms=now_ms)
        freshness_by_topic = {r.component: r for r in freshness_report.per_topic}
        worst = HealthSeverity.OK
        for topic in _REQUIRED_BRIDGED_TOPICS:
            advertised = self._advertised.get(topic, False)
            freshness = freshness_by_topic.get(f"topic:{topic}")
            if not advertised:
                rep = HealthReport(
                    component=f"bridge:{topic}",
                    severity=HealthSeverity.ERROR,
                    summary=f"{topic} not advertised by ros_gz_bridge",
                    detail="check launch ordering and bridge YAML",
                    attributes={"advertised": False},
                )
            elif freshness is None:
                rep = HealthReport(
                    component=f"bridge:{topic}",
                    severity=HealthSeverity.WARN,
                    summary=f"{topic} freshness unknown",
                    detail="freshness monitor has no observations",
                )
            else:
                # Inherit freshness severity but rebrand component as bridge.
                rep = HealthReport(
                    component=f"bridge:{topic}",
                    severity=freshness.severity,
                    summary=freshness.summary,
                    detail=freshness.detail,
                    attributes={**freshness.attributes, "advertised": True},
                )
            per_topic.append(rep)
            if _rank(rep.severity) > _rank(worst):
                worst = rep.severity
        return BridgeHealthReport(
            severity=worst,
            summary=_summary(per_topic, worst),
            per_topic=tuple(per_topic),
        )


def _summary(per_topic: list[HealthReport], severity: HealthSeverity) -> str:
    bad = [r for r in per_topic if r.severity != HealthSeverity.OK]
    if not bad:
        return "ros_gz_bridge healthy"
    return f"ros_gz_bridge unhealthy ({severity.value}; {len(bad)} topic(s))"


_RANK = {
    HealthSeverity.OK: 0,
    HealthSeverity.WARN: 1,
    HealthSeverity.ERROR: 2,
    HealthSeverity.CRITICAL: 3,
}


def _rank(s: HealthSeverity) -> int:
    return _RANK[s]
