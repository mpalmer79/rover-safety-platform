"""Helpers for publishing diagnostics-shaped messages.

The runtime diagnostics nodes share a small amount of plumbing for
turning :class:`HealthReport` records from :mod:`app.diagnostics` into
``diagnostic_msgs/DiagnosticStatus`` payloads. Keeping the shared
helpers here lets the per-component nodes stay short and lets the
helpers be unit tested without a live ROS graph.
"""

from __future__ import annotations

from typing import Iterable

from app.diagnostics import HealthReport, HealthSeverity


_SEVERITY_TO_DIAG_LEVEL = {
    HealthSeverity.OK: 0,
    HealthSeverity.WARN: 1,
    HealthSeverity.ERROR: 2,
    HealthSeverity.CRITICAL: 2,
}


def severity_to_diagnostic_level(severity: HealthSeverity) -> int:
    """Map our severity vocabulary to ``diagnostic_msgs/DiagnosticStatus.level``."""

    return _SEVERITY_TO_DIAG_LEVEL[severity]


def reports_to_diagnostic_status_payloads(
    *,
    hardware_id: str,
    reports: Iterable[HealthReport],
) -> list[dict]:
    """Return a list of dicts shaped like ``DiagnosticStatus`` fields.

    Returning dicts (instead of constructing the ROS messages here) lets
    the function be unit tested without importing ``diagnostic_msgs``.
    The node module turns the dicts into the message at publish time.
    """

    out: list[dict] = []
    for report in reports:
        out.append(
            {
                "level": severity_to_diagnostic_level(report.severity),
                "name": report.component,
                "message": report.summary,
                "hardware_id": hardware_id,
                "values": [
                    {"key": k, "value": str(v)}
                    for k, v in sorted(report.attributes.items())
                ],
            }
        )
    return out
