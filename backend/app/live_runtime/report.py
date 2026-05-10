"""Render the live-runtime maturity report as JSON + Markdown.

The platform is **not safety-certified**.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .models import LIVE_RUNTIME_DISCLAIMER, LiveRuntimeMaturityReport


def maturity_report_to_dict(report: LiveRuntimeMaturityReport) -> dict:
    out = asdict(report)
    out["bag_counters"] = asdict(report.bag_counters)
    out["runs_by_status"] = dict(report.runs_by_status)
    out["required_topic_coverage"] = dict(report.required_topic_coverage)
    out["scenario_coverage"] = dict(report.scenario_coverage)
    out["known_limitations"] = list(report.known_limitations)
    out["next_actions"] = list(report.next_actions)
    out["disclaimer"] = LIVE_RUNTIME_DISCLAIMER
    return out


def write_maturity_json(report: LiveRuntimeMaturityReport, path: Path) -> None:
    Path(path).write_text(
        json.dumps(maturity_report_to_dict(report), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def render_maturity_markdown(report: LiveRuntimeMaturityReport) -> str:
    lines = [
        "# Live Runtime Maturity Report",
        "",
        f"_{LIVE_RUNTIME_DISCLAIMER}_",
        "",
        f"- **Generated (UTC):** {report.generated_at_utc}",
        f"- **Evidence root:** `{report.evidence_root}`",
        f"- **Runs total:** {report.runs_total}",
        f"- **Latest run id:** `{report.latest_run_id or '-'}`",
        f"- **Latest run status:** `{report.latest_run_status or '-'}`",
        f"- **Runner status:** `{report.runner_status}`",
        "",
        "## Run-status counts",
        "",
        "| Status | Count |",
        "| --- | --- |",
    ]
    if not report.runs_by_status:
        lines.append("| - | 0 |")
    else:
        for k in sorted(report.runs_by_status):
            lines.append(f"| `{k}` | {report.runs_by_status[k]} |")

    lines += [
        "",
        "## Bag counters",
        "",
        "| Bag status | Count |",
        "| --- | --- |",
        f"| `bag_backed` | {report.bag_counters.bag_backed} |",
        f"| `missing_bag` | {report.bag_counters.missing_bag} |",
        f"| `partial` | {report.bag_counters.partial} |",
        f"| `not_executed` | {report.bag_counters.not_executed} |",
        f"| `invalid` | {report.bag_counters.invalid} |",
        "",
        "## Downstream integration status",
        "",
        "| Pipeline | Status |",
        "| --- | --- |",
        f"| Replay review | `{report.replay_review_integration}` |",
        f"| Replay analytics | `{report.analytics_integration}` |",
        f"| Programme review | `{report.programme_review_integration}` |",
        "",
    ]

    if report.scenario_coverage:
        lines += ["## Scenario coverage", "", "| Scenario id | Run count |", "| --- | --- |"]
        for sid in sorted(report.scenario_coverage):
            lines.append(f"| `{sid}` | {report.scenario_coverage[sid]} |")
        lines.append("")

    if report.required_topic_coverage:
        lines += ["## Topic coverage (across all bag manifests)", "", "| Topic | Bag count |", "| --- | --- |"]
        for t in sorted(report.required_topic_coverage):
            lines.append(f"| `{t}` | {report.required_topic_coverage[t]} |")
        lines.append("")

    if report.known_limitations:
        lines.append("## Known limitations")
        lines.append("")
        for lim in report.known_limitations:
            lines.append(f"- {lim}")
        lines.append("")

    if report.next_actions:
        lines.append("## Next actions")
        lines.append("")
        for action in report.next_actions:
            lines.append(f"- {action}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_maturity_markdown(report: LiveRuntimeMaturityReport, path: Path) -> None:
    Path(path).write_text(render_maturity_markdown(report), encoding="utf-8")


__all__ = [
    "maturity_report_to_dict",
    "write_maturity_json",
    "render_maturity_markdown",
    "write_maturity_markdown",
]
