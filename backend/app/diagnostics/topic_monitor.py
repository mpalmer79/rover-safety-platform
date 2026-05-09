"""Topic freshness monitor.

The monitor tracks per-topic last-seen timestamps and produces a
:class:`HealthReport` per topic. It is pure logic: it does not subscribe
to topics; the consuming ROS node feeds it observations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from app.diagnostics.runtime_summary import HealthReport, HealthSeverity


@dataclass(frozen=True)
class TopicSpec:
    """Declared expectation for a single topic."""

    name: str
    expected_period_ms: int
    warn_age_ms: int
    error_age_ms: int
    required: bool = True

    def __post_init__(self) -> None:
        if self.expected_period_ms <= 0:
            raise ValueError("expected_period_ms must be positive")
        if self.warn_age_ms < self.expected_period_ms:
            raise ValueError("warn_age_ms must be >= expected_period_ms")
        if self.error_age_ms <= self.warn_age_ms:
            raise ValueError("error_age_ms must be > warn_age_ms")


# Documented-topic expectations. Aligns with rover_sim_gazebo's bridge
# YAML and the safety bridge's publication contract.
DEFAULT_TOPIC_SPECS: tuple[TopicSpec, ...] = (
    TopicSpec(name="/clock", expected_period_ms=10, warn_age_ms=200, error_age_ms=1000),
    TopicSpec(name="/scan", expected_period_ms=100, warn_age_ms=250, error_age_ms=750),
    TopicSpec(name="/imu", expected_period_ms=20, warn_age_ms=200, error_age_ms=600),
    TopicSpec(name="/odom", expected_period_ms=20, warn_age_ms=200, error_age_ms=600),
    TopicSpec(name="/contact", expected_period_ms=50, warn_age_ms=500, error_age_ms=1500),
    TopicSpec(name="/cmd_vel_authorized", expected_period_ms=50, warn_age_ms=200, error_age_ms=600),
    TopicSpec(name="/safety/state", expected_period_ms=100, warn_age_ms=400, error_age_ms=1500, required=True),
    TopicSpec(name="/safety/events", expected_period_ms=1000, warn_age_ms=5000, error_age_ms=15000, required=False),
)


@dataclass
class TopicObservation:
    name: str
    last_observed_ms: Optional[int] = None
    sample_count: int = 0


@dataclass(frozen=True)
class TopicFreshnessReport:
    severity: HealthSeverity
    summary: str
    per_topic: tuple[HealthReport, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity.value,
            "summary": self.summary,
            "per_topic": [r.to_dict() for r in self.per_topic],
        }


class TopicFreshnessMonitor:
    """Tracks per-topic last-seen and produces a freshness report."""

    def __init__(self, specs: tuple[TopicSpec, ...] = DEFAULT_TOPIC_SPECS) -> None:
        self._specs: dict[str, TopicSpec] = {s.name: s for s in specs}
        self._observations: dict[str, TopicObservation] = {
            s.name: TopicObservation(name=s.name) for s in specs
        }
        self._declared_at_ms: int = 0

    @property
    def topic_names(self) -> tuple[str, ...]:
        return tuple(self._specs.keys())

    def declare(self, *, now_ms: int) -> None:
        """Reset the start time so transient missing topics during the
        first ``warn_age_ms`` window do not flap.
        """

        self._declared_at_ms = int(now_ms)

    def observe(self, *, topic: str, now_ms: int) -> None:
        """Record an observation for ``topic`` at simulator/wall time."""

        obs = self._observations.get(topic)
        if obs is None:
            # Unexpected topic: ignored. The bridge validator catches
            # mis-named topics offline; the monitor only tracks declared
            # specs.
            return
        obs.last_observed_ms = int(now_ms)
        obs.sample_count += 1

    def report(self, *, now_ms: int) -> TopicFreshnessReport:
        per_topic: list[HealthReport] = []
        worst = HealthSeverity.OK
        for spec in self._specs.values():
            report = self._evaluate(spec=spec, now_ms=now_ms)
            per_topic.append(report)
            if _rank(report.severity) > _rank(worst):
                worst = report.severity
        return TopicFreshnessReport(
            severity=worst,
            summary=_summary(per_topic, worst),
            per_topic=tuple(per_topic),
        )

    def _evaluate(self, *, spec: TopicSpec, now_ms: int) -> HealthReport:
        obs = self._observations[spec.name]
        if obs.last_observed_ms is None:
            warmup_remaining = max(0, spec.warn_age_ms - (now_ms - self._declared_at_ms))
            if warmup_remaining > 0:
                return HealthReport(
                    component=f"topic:{spec.name}",
                    severity=HealthSeverity.OK,
                    summary=f"awaiting first sample ({warmup_remaining}ms left)",
                    attributes={"warmup": True, "warmup_remaining_ms": warmup_remaining},
                )
            severity = HealthSeverity.ERROR if spec.required else HealthSeverity.WARN
            return HealthReport(
                component=f"topic:{spec.name}",
                severity=severity,
                summary=f"{spec.name} has never published",
                detail=f"expected period {spec.expected_period_ms} ms",
                attributes={"required": spec.required},
            )
        age_ms = max(0, now_ms - obs.last_observed_ms)
        if age_ms > spec.error_age_ms:
            severity = HealthSeverity.ERROR
            summary = f"{spec.name} stale ({age_ms} ms > {spec.error_age_ms} ms)"
        elif age_ms > spec.warn_age_ms:
            severity = HealthSeverity.WARN
            summary = f"{spec.name} stale ({age_ms} ms > {spec.warn_age_ms} ms)"
        else:
            severity = HealthSeverity.OK
            summary = f"{spec.name} fresh ({age_ms} ms)"
        return HealthReport(
            component=f"topic:{spec.name}",
            severity=severity,
            summary=summary,
            attributes={
                "age_ms": age_ms,
                "sample_count": obs.sample_count,
                "expected_period_ms": spec.expected_period_ms,
                "warn_age_ms": spec.warn_age_ms,
                "error_age_ms": spec.error_age_ms,
                "required": spec.required,
            },
        )


def _summary(per_topic: list[HealthReport], severity: HealthSeverity) -> str:
    bad = [r for r in per_topic if r.severity != HealthSeverity.OK]
    if not bad:
        return "all topics fresh"
    return f"{len(bad)} topic(s) unhealthy ({severity.value})"


_RANK = {
    HealthSeverity.OK: 0,
    HealthSeverity.WARN: 1,
    HealthSeverity.ERROR: 2,
    HealthSeverity.CRITICAL: 3,
}


def _rank(s: HealthSeverity) -> int:
    return _RANK[s]
