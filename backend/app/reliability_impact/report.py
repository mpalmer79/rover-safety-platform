"""Reliability impact report renderer + orchestration.

Composes a :class:`ImpactReport` from the source change inventory,
subsystem classification, requirement + evidence mapping, analytics
delta, risk assessment, and CI gate decision. Renders Markdown +
JSON. Writes every per-file artefact under ``reliability-impact/``.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

from app.reliability_impact.analytics_delta import compute_analytics_delta
from app.reliability_impact.baseline import resolve_baseline
from app.reliability_impact.ci_gate import decide_gate
from app.reliability_impact.evidence_mapper import map_evidence_for_impacts
from app.reliability_impact.git_changes import collect_source_change
from app.reliability_impact.models import (
    BaselineReference,
    DEFAULT_KNOWN_LIMITATIONS,
    EvidenceImpact,
    GateDecision,
    IMPACT_CERTIFICATION_DISCLAIMER,
    ImpactAssessment,
    ImpactReport,
    ReplayAnalyticsDelta,
    RequirementImpact,
    SourceChange,
    Subsystem,
    SubsystemImpact,
    is_safety_critical,
)
from app.reliability_impact.requirement_mapper import map_impacts
from app.reliability_impact.risk_assessor import assess_impact


def build_report(
    *,
    source_change: SourceChange,
    baseline: BaselineReference,
    current_quality_index: Optional[Path] = None,
    current_analytics_report: Optional[Path] = None,
    traceability_passed: Optional[bool] = None,
    tests_passed: Optional[bool] = None,
    is_github_hosted: Optional[bool] = None,
    fixture_mode: bool = False,
) -> ImpactReport:
    subsystem_impacts = _build_subsystem_impacts(source_change)
    requirement_impacts = tuple(map_impacts(list(subsystem_impacts)))
    evidence_impacts = tuple(
        map_evidence_for_impacts(
            list(subsystem_impacts),
            list(requirement_impacts),
        )
    )
    analytics_delta = compute_analytics_delta(
        current_quality_index=current_quality_index,
        current_analytics_report=current_analytics_report,
        baseline=baseline,
    )
    assessment = assess_impact(
        source_change=source_change,
        subsystem_impacts=subsystem_impacts,
        requirement_impacts=requirement_impacts,
        evidence_impacts=evidence_impacts,
        analytics_delta=analytics_delta,
    )
    gate = decide_gate(
        source_change=source_change,
        subsystem_impacts=subsystem_impacts,
        evidence_impacts=evidence_impacts,
        analytics_delta=analytics_delta,
        assessment=assessment,
        traceability_passed=traceability_passed,
        tests_passed=tests_passed,
        is_github_hosted=is_github_hosted,
    )
    return ImpactReport(
        base_ref=source_change.base_ref,
        head_ref=source_change.head_ref,
        source=source_change.source,
        source_change=source_change,
        subsystem_impacts=subsystem_impacts,
        requirement_impacts=requirement_impacts,
        evidence_impacts=evidence_impacts,
        analytics_delta=analytics_delta,
        assessment=assessment,
        gate_decision=gate,
        baseline=baseline,
        known_limitations=DEFAULT_KNOWN_LIMITATIONS,
        generated_at_utc=datetime.now(tz=timezone.utc).isoformat(
            timespec="seconds"
        ),
        fixture_mode=fixture_mode,
    )


def _build_subsystem_impacts(
    source_change: SourceChange,
) -> tuple[SubsystemImpact, ...]:
    """Group changed files by subsystem.

    The order is fixed by enum-declaration order so the report is
    deterministic regardless of iteration order in the input.
    """

    groups: dict[Subsystem, list] = {}
    for f in source_change.changed_files:
        groups.setdefault(f.subsystem, []).append(f)
    impacts: list[SubsystemImpact] = []
    for subsystem in Subsystem:
        if subsystem not in groups:
            continue
        impacts.append(
            SubsystemImpact(
                subsystem=subsystem,
                changed_files=tuple(groups[subsystem]),
                is_safety_critical=is_safety_critical(subsystem),
            )
        )
    return tuple(impacts)


def write_report_files(report: ImpactReport, *, out_dir: Path) -> None:
    """Persist the report and the per-section JSON files."""

    out_dir.mkdir(parents=True, exist_ok=True)
    _write_json(out_dir / "impact-report.json", report.as_dict())
    (out_dir / "impact-report.md").write_text(
        render_report_md(report), encoding="utf-8"
    )
    _write_json(
        out_dir / "changed-files.json",
        [f.as_dict() for f in report.source_change.changed_files],
    )
    _write_json(
        out_dir / "subsystem-impact.json",
        [s.as_dict() for s in report.subsystem_impacts],
    )
    _write_json(
        out_dir / "requirement-impact.json",
        [r.as_dict() for r in report.requirement_impacts],
    )
    _write_json(
        out_dir / "evidence-impact.json",
        [e.as_dict() for e in report.evidence_impacts],
    )
    _write_json(
        out_dir / "analytics-delta.json", report.analytics_delta.as_dict()
    )
    _write_json(
        out_dir / "gate-decision.json", report.gate_decision.as_dict()
    )


def render_report_md(report: ImpactReport) -> str:
    lines: list[str] = []
    lines.append("# Reliability Impact Report")
    lines.append("")
    lines.append(
        "_Generated by `rover_ws/tools/analyze_source_impact.py`. The "
        "platform is **not safety-certified**; this report is "
        "engineering reliability material._"
    )
    lines.append("")
    lines.append(f"- **Base ref:** `{report.base_ref or '-'}`")
    lines.append(f"- **Head ref:** `{report.head_ref or '-'}`")
    lines.append(f"- **Source:** `{report.source}`")
    if report.fixture_mode:
        lines.append(
            "- **Fixture mode:** **yes** — the change list is "
            "synthesised from a fixture, not a real git diff"
        )
    lines.append(
        f"- **Gate status:** `{report.gate_decision.status.value}`"
    )
    lines.append(
        f"- **Overall risk:** `{report.assessment.overall_risk.value}`"
    )
    lines.append(
        f"- **Analytics delta severity:** "
        f"`{report.analytics_delta.severity.value}`"
    )
    lines.append(f"- **Generated:** {report.generated_at_utc}")
    lines.append("")

    # Source change
    lines.append("## Changed files")
    lines.append("")
    if not report.source_change.changed_files:
        lines.append("_No changes detected._")
    else:
        lines.append("| Path | Change | Subsystem |")
        lines.append("|---|---|---|")
        for f in report.source_change.changed_files:
            lines.append(
                f"| `{f.path}` | `{f.change_type.value}` | "
                f"`{f.subsystem.value}` |"
            )
    if report.source_change.warnings:
        lines.append("")
        lines.append("**Collection warnings:**")
        for w in report.source_change.warnings:
            lines.append(f"- {w}")
    lines.append("")

    # Subsystem impacts
    lines.append("## Subsystem impacts")
    lines.append("")
    if not report.subsystem_impacts:
        lines.append("_No subsystems impacted._")
    else:
        lines.append("| Subsystem | Files | Safety-critical |")
        lines.append("|---|---|---|")
        for s in report.subsystem_impacts:
            lines.append(
                f"| `{s.subsystem.value}` | {len(s.changed_files)} | "
                f"{'yes' if s.is_safety_critical else 'no'} |"
            )
    lines.append("")

    # Requirement impacts
    lines.append("## Requirement impacts")
    lines.append("")
    if not report.requirement_impacts:
        lines.append("_No requirements mapped._")
    else:
        lines.append("| Subsystem | Requirement ids | Notes |")
        lines.append("|---|---|---|")
        for r in report.requirement_impacts:
            ids = ", ".join(f"`{i}`" for i in r.requirement_ids) or "-"
            lines.append(
                f"| `{r.subsystem.value}` | {ids} | {r.notes or '-'} |"
            )
    lines.append("")

    # Evidence impacts
    lines.append("## Evidence impacts")
    lines.append("")
    if not report.evidence_impacts:
        lines.append("_No evidence recipes._")
    else:
        for e in report.evidence_impacts:
            lines.append(f"### `{e.subsystem.value}`")
            lines.append("")
            if e.recommended_tools:
                lines.append("**Recommended tools:**")
                for t in e.recommended_tools:
                    lines.append(f"- `{t}`")
            if e.recommended_artifacts:
                lines.append("")
                lines.append("**Recommended artefacts:**")
                for a in e.recommended_artifacts:
                    lines.append(f"- `{a}`")
            if e.notes:
                lines.append("")
                lines.append(f"_{e.notes}_")
            lines.append("")
    lines.append("")

    # Analytics delta
    lines.append("## Analytics delta")
    lines.append("")
    counts = report.analytics_delta.summary_counts()
    lines.append(
        f"- **Severity:** `{report.analytics_delta.severity.value}`"
    )
    lines.append(
        f"- **Baseline:** `{report.analytics_delta.baseline_path or '-'}`"
    )
    if report.analytics_delta.warnings:
        lines.append("- **Warnings:**")
        for w in report.analytics_delta.warnings:
            lines.append(f"  - {w}")
    lines.append("")
    lines.append("| Severity | Count |")
    lines.append("|---|---|")
    for sev_value, count in counts.items():
        lines.append(f"| `{sev_value}` | {count} |")
    if report.analytics_delta.entries:
        lines.append("")
        lines.append(
            "| Label | Category | Severity | Detail |"
        )
        lines.append("|---|---|---|---|")
        for e in report.analytics_delta.entries:
            lines.append(
                f"| `{e.label}` | `{e.category}` | "
                f"`{e.severity.value}` | {e.detail} |"
            )
    lines.append("")

    # Risk assessment
    lines.append("## Risk assessment")
    lines.append("")
    lines.append(f"- **Overall risk:** `{report.assessment.overall_risk.value}`")
    if not report.assessment.risks:
        lines.append("")
        lines.append("_No risks recorded._")
    else:
        lines.append("")
        lines.append("| Label | Level | Rationale |")
        lines.append("|---|---|---|")
        for r in report.assessment.risks:
            lines.append(
                f"| `{r.label}` | `{r.level.value}` | {r.rationale} |"
            )
    lines.append("")

    # Gate decision
    lines.append("## CI gate decision")
    lines.append("")
    lines.append(f"- **Status:** `{report.gate_decision.status.value}`")
    if report.gate_decision.failures:
        lines.append("- **Failures:**")
        for f in report.gate_decision.failures:
            lines.append(f"  - {f}")
    if report.gate_decision.warnings:
        lines.append("- **Warnings:**")
        for w in report.gate_decision.warnings:
            lines.append(f"  - {w}")
    if report.gate_decision.notes:
        lines.append("- **Notes:**")
        for n in report.gate_decision.notes:
            lines.append(f"  - {n}")
    lines.append("")

    # Known limitations.
    lines.append("## Known limitations")
    lines.append("")
    for line in report.known_limitations:
        lines.append(f"- {line}")
    lines.append("")

    lines.append("## Certification disclaimer")
    lines.append("")
    lines.append(IMPACT_CERTIFICATION_DISCLAIMER)
    lines.append("")
    return "\n".join(lines)


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
