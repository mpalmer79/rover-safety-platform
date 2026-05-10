"""Qualification report and live-runtime status renderers.

Phase 5 produces three Markdown reports per qualification run:

* ``qualification-summary.md`` (per run) — captures the host-qualification
  result, the runtime-validation result, the regression detector
  output, the baseline comparison (when applicable), and the
  per-scenario summaries.
* ``RUNTIME_QUALIFICATION_REPORT.md`` (canonical, in ``docs/``) —
  the most-recent qualification snapshot, suitable for code review.
* ``LIVE_RUNTIME_STATUS.md`` (canonical, in ``docs/``) — a
  short-form status page that **labels every check as
  ``static-source``, ``static-workspace``, or ``live-runtime``** so a
  reviewer cannot mistake static evidence for live evidence.

Each renderer is pure and deterministic. None of them invent data;
they consume a :class:`QualificationReport` value object that the
orchestrator constructs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable, Optional

from app.runtime_validation.baselines import BaselineComparison, DeltaSeverity
from app.runtime_validation.host_qualification import HostQualificationResult
from app.runtime_validation.regression import RegressionReport
from app.runtime_validation.report_renderer import RuntimeReport
from app.verification.acceptance import AcceptanceStatus, aggregate_status


_VALID_ORIGINS: frozenset[str] = frozenset(
    {"static-source", "static-workspace", "live-runtime"}
)


@dataclass
class QualificationCheck:
    name: str
    origin: str
    """One of ``static-source``, ``static-workspace``, ``live-runtime``."""

    status: AcceptanceStatus
    detail: str = ""
    reason: str = ""
    evidence_paths: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.origin not in _VALID_ORIGINS:
            raise ValueError(
                f"origin must be one of {sorted(_VALID_ORIGINS)}; got {self.origin!r}"
            )

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "origin": self.origin,
            "status": self.status.value,
            "detail": self.detail,
            "reason": self.reason,
            "evidence_paths": list(self.evidence_paths),
        }


@dataclass
class ScenarioOutcome:
    scenario_id: str
    expected_outcome: str
    observed_status: AcceptanceStatus
    detail: str = ""
    findings: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {
            "scenario_id": self.scenario_id,
            "expected_outcome": self.expected_outcome,
            "observed_status": self.observed_status.value,
            "detail": self.detail,
            "findings": list(self.findings),
        }


@dataclass
class QualificationReport:
    run_id: str
    mode: str
    """One of ``static-only``, ``live``, ``mixed``."""

    generated_at_utc: str = ""
    host_result: Optional[HostQualificationResult] = None
    runtime_report: Optional[RuntimeReport] = None
    regression_report: Optional[RegressionReport] = None
    baseline_comparison: Optional[BaselineComparison] = None
    scenarios: list[ScenarioOutcome] = field(default_factory=list)
    qualification_checks: list[QualificationCheck] = field(default_factory=list)
    known_limitations: tuple[str, ...] = (
        "The platform is **not** safety-certified. This report "
        "demonstrates engineering qualification discipline.",
        "Live ROS 2 / Gazebo qualification requires a Jazzy host with "
        "Gazebo Harmonic. Runs without those dependencies surface their "
        "live checks as `not_executed` with a reason; never as `passed`.",
        "Static-only mode validates the workspace artefacts and the "
        "deterministic engine. It does not exercise the safety bridge "
        "against a live actuator stream.",
    )

    def __post_init__(self) -> None:
        if not self.generated_at_utc:
            self.generated_at_utc = datetime.now(tz=timezone.utc).isoformat(
                timespec="seconds"
            )

    @property
    def overall_status(self) -> AcceptanceStatus:
        statuses: list[AcceptanceStatus] = []
        if self.host_result is not None:
            statuses.append(self.host_result.status)
        if self.runtime_report is not None:
            statuses.append(self.runtime_report.status)
        if self.regression_report is not None and self.regression_report.has_regression():
            statuses.append(AcceptanceStatus.FAILED)
        if self.baseline_comparison is not None and self.baseline_comparison.has_regression():
            statuses.append(AcceptanceStatus.FAILED)
        for check in self.qualification_checks:
            statuses.append(check.status)
        for outcome in self.scenarios:
            statuses.append(outcome.observed_status)
        return aggregate_status(statuses) if statuses else AcceptanceStatus.NOT_EXECUTED

    def status_counts(self) -> dict[str, int]:
        out = {s.value: 0 for s in AcceptanceStatus}
        for check in self.qualification_checks:
            out[check.status.value] += 1
        for outcome in self.scenarios:
            out[outcome.observed_status.value] += 1
        return out

    def as_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "mode": self.mode,
            "generated_at_utc": self.generated_at_utc,
            "overall_status": self.overall_status.value,
            "status_counts": self.status_counts(),
            "host_result": (
                self.host_result.as_dict() if self.host_result is not None else None
            ),
            "runtime_report": (
                self.runtime_report.as_dict() if self.runtime_report is not None else None
            ),
            "regression_report": (
                self.regression_report.as_dict()
                if self.regression_report is not None
                else None
            ),
            "baseline_comparison": (
                self.baseline_comparison.as_dict()
                if self.baseline_comparison is not None
                else None
            ),
            "scenarios": [s.as_dict() for s in self.scenarios],
            "qualification_checks": [c.as_dict() for c in self.qualification_checks],
            "known_limitations": list(self.known_limitations),
        }


# ---------------------------------------------------------------------------
# Renderers.
# ---------------------------------------------------------------------------


def render_qualification_summary_md(report: QualificationReport) -> str:
    lines: list[str] = []
    lines.append("# Qualification Summary")
    lines.append("")
    lines.append(
        "_Generated by `rover_ws/tools/qualified_runtime_run.py`. The "
        "platform is **not safety-certified**; this report demonstrates "
        "engineering qualification discipline. Every check is labelled "
        "by its **origin**: `static-source` (greps the source tree), "
        "`static-workspace` (parses workspace artefacts), or "
        "`live-runtime` (requires a Jazzy host)._"
    )
    lines.append("")
    lines.append(f"- **Run id:** `{report.run_id}`")
    lines.append(f"- **Mode:** `{report.mode}`")
    lines.append(f"- **Generated:** {report.generated_at_utc}")
    lines.append(f"- **Overall status:** `{report.overall_status.value}`")
    lines.append("")

    if report.host_result is not None:
        lines.append("## Host qualification")
        lines.append("")
        lines.append(
            f"Aggregate: `{report.host_result.status.value}` "
            f"({sum(report.host_result.status_counts().values())} check(s))"
        )
        lines.append("")
        lines.append("| Check | Status | Detail |")
        lines.append("|---|---|---|")
        for c in report.host_result.checks:
            lines.append(
                f"| `{c.name}` | `{c.status.value}` | {c.detail or '-'} |"
            )
        lines.append("")

    if report.runtime_report is not None:
        rr = report.runtime_report
        lines.append("## Runtime validation")
        lines.append("")
        lines.append(
            f"Aggregate: `{rr.status.value}` "
            f"({sum(rr.status_counts().values())} check(s))"
        )
        lines.append("")

    if report.qualification_checks:
        lines.append("## Qualification checks")
        lines.append("")
        lines.append("| Check | Origin | Status | Detail |")
        lines.append("|---|---|---|---|")
        for c in report.qualification_checks:
            lines.append(
                f"| `{c.name}` | `{c.origin}` | `{c.status.value}` | {c.detail or '-'} |"
            )
            if c.reason:
                lines.append(f"|   |   | _reason_ | {c.reason} |")
        lines.append("")

    if report.scenarios:
        lines.append("## Scenarios")
        lines.append("")
        lines.append(
            "| Scenario | Expected | Observed | Detail |"
        )
        lines.append("|---|---|---|---|")
        for s in report.scenarios:
            lines.append(
                f"| `{s.scenario_id}` | `{s.expected_outcome}` | "
                f"`{s.observed_status.value}` | {s.detail or '-'} |"
            )
        lines.append("")

    if report.regression_report is not None:
        lines.append("## Regression detection")
        lines.append("")
        counts = report.regression_report.summary_counts()
        lines.append(
            f"Severity: `{report.regression_report.severity.value}` "
            f"(findings: {sum(counts.values())})"
        )
        lines.append("")
        if report.regression_report.findings:
            lines.append("| Finding | Severity | Detail |")
            lines.append("|---|---|---|")
            for f in report.regression_report.findings:
                lines.append(
                    f"| `{f.name}` | `{f.severity.value}` | {f.detail} |"
                )
            lines.append("")

    if report.baseline_comparison is not None:
        bc = report.baseline_comparison
        lines.append("## Baseline comparison")
        lines.append("")
        lines.append(f"- **Baseline:** `{bc.baseline_path}`")
        lines.append(f"- **Severity:** `{bc.severity.value}`")
        lines.append("")
        if bc.deltas:
            lines.append("| Category | Key | Severity | Detail |")
            lines.append("|---|---|---|---|")
            for d in bc.deltas:
                lines.append(
                    f"| `{d.category}` | `{d.key}` | `{d.severity.value}` | {d.detail} |"
                )
            lines.append("")

    lines.append("## Known limitations")
    lines.append("")
    for line in report.known_limitations:
        lines.append(f"- {line}")
    lines.append("")
    return "\n".join(lines)


def render_live_runtime_status_md(report: QualificationReport) -> str:
    """Short-form status that distinguishes static vs live evidence."""

    lines: list[str] = []
    lines.append("# Live Runtime Status")
    lines.append("")
    lines.append(
        "_Short-form status page distinguishing static-source, "
        "static-workspace, and live-runtime checks. The platform is "
        "**not safety-certified**._"
    )
    lines.append("")
    lines.append(f"- **Run id:** `{report.run_id}`")
    lines.append(f"- **Mode:** `{report.mode}`")
    lines.append(f"- **Generated:** {report.generated_at_utc}")
    lines.append(f"- **Overall status:** `{report.overall_status.value}`")
    lines.append("")

    by_origin: dict[str, list[QualificationCheck]] = {
        "static-source": [],
        "static-workspace": [],
        "live-runtime": [],
    }
    for check in report.qualification_checks:
        by_origin[check.origin].append(check)

    for origin in ("static-source", "static-workspace", "live-runtime"):
        checks = by_origin[origin]
        lines.append(f"## {origin}")
        lines.append("")
        if not checks:
            lines.append(f"_No `{origin}` checks recorded for this run._")
            lines.append("")
            continue
        lines.append("| Check | Status | Detail |")
        lines.append("|---|---|---|")
        for c in checks:
            lines.append(
                f"| `{c.name}` | `{c.status.value}` | {c.detail or '-'} |"
            )
            if c.reason:
                lines.append(f"|   _reason_ |   | {c.reason} |")
        lines.append("")

    not_executed_live = [
        c for c in by_origin["live-runtime"]
        if c.status == AcceptanceStatus.NOT_EXECUTED
    ]
    if not_executed_live:
        lines.append("## Live-runtime checks not executed")
        lines.append("")
        lines.append(
            "The following live-runtime checks were not executed in this "
            "run; they are reported as `not_executed`, never as `passed`:"
        )
        lines.append("")
        for c in not_executed_live:
            lines.append(f"- `{c.name}` — {c.reason or 'no reason recorded'}")
        lines.append("")

    return "\n".join(lines)
