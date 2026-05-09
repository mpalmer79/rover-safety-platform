"""Health summary value objects shared by every monitor."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class HealthSeverity(str, Enum):
    OK = "OK"
    WARN = "WARN"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


_SEVERITY_RANK: dict[HealthSeverity, int] = {
    HealthSeverity.OK: 0,
    HealthSeverity.WARN: 1,
    HealthSeverity.ERROR: 2,
    HealthSeverity.CRITICAL: 3,
}


@dataclass(frozen=True)
class HealthReport:
    """A single diagnostic finding.

    Mirrors a ``diagnostic_msgs/DiagnosticStatus`` row, but with stable
    severity vocabulary and an optional structured ``attributes`` dict.
    """

    component: str
    severity: HealthSeverity
    summary: str
    detail: str = ""
    attributes: dict[str, Any] = field(default_factory=dict)

    @property
    def is_healthy(self) -> bool:
        return self.severity == HealthSeverity.OK

    def to_dict(self) -> dict[str, Any]:
        return {
            "component": self.component,
            "severity": self.severity.value,
            "summary": self.summary,
            "detail": self.detail,
            "attributes": dict(self.attributes),
        }


@dataclass(frozen=True)
class RuntimeSummary:
    """Aggregated runtime health across every monitor."""

    severity: HealthSeverity
    reports: tuple[HealthReport, ...]

    @property
    def is_healthy(self) -> bool:
        return self.severity == HealthSeverity.OK

    def to_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity.value,
            "reports": [r.to_dict() for r in self.reports],
        }


def aggregate_health(reports: list[HealthReport]) -> RuntimeSummary:
    if not reports:
        return RuntimeSummary(severity=HealthSeverity.OK, reports=tuple())
    worst = max(reports, key=lambda r: _SEVERITY_RANK[r.severity])
    return RuntimeSummary(severity=worst.severity, reports=tuple(reports))
