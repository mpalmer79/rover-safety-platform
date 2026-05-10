"""Conservative reliability risk assessment.

The assessor walks the source change + analytics delta + evidence
recommendations and emits a list of :class:`ReliabilityRisk`
entries. The overall risk is the maximum across the rules; the
report renders both the per-rule rationale and the overall label.

The assessor never inflates risk to "high" without an explicit
trigger: safety / motion changes paired with absent evidence,
critical regressions, removed static workflows, etc. Documentation-
only and test-only changes stay at ``low`` or ``none``.
"""

from __future__ import annotations

from typing import Iterable

from app.reliability_impact.models import (
    AnalyticsDeltaEntry,
    DeltaSeverity,
    EvidenceImpact,
    ImpactAssessment,
    ReliabilityRisk,
    ReplayAnalyticsDelta,
    RequirementImpact,
    RiskLevel,
    SourceChange,
    Subsystem,
    SubsystemImpact,
    is_safety_critical,
)


_RISK_ORDER: dict[RiskLevel, int] = {
    RiskLevel.NONE: 0,
    RiskLevel.LOW: 1,
    RiskLevel.MODERATE: 2,
    RiskLevel.HIGH: 3,
    RiskLevel.CRITICAL: 4,
}


def assess_impact(
    *,
    source_change: SourceChange,
    subsystem_impacts: Iterable[SubsystemImpact],
    requirement_impacts: Iterable[RequirementImpact],
    evidence_impacts: Iterable[EvidenceImpact],
    analytics_delta: ReplayAnalyticsDelta,
) -> ImpactAssessment:
    """Compose the deterministic risk assessment."""

    subsystem_impacts = list(subsystem_impacts)
    requirement_impacts = list(requirement_impacts)
    evidence_impacts = list(evidence_impacts)
    risks: list[ReliabilityRisk] = []

    impacted_subsystems = {s.subsystem for s in subsystem_impacts}
    safety_path_touched = any(
        is_safety_critical(s.subsystem) for s in subsystem_impacts
    )

    # 1. Critical regression always tops the risk pile.
    if analytics_delta.severity == DeltaSeverity.CRITICAL_REGRESSION:
        critical_entries = [
            e for e in analytics_delta.entries
            if e.severity == DeltaSeverity.CRITICAL_REGRESSION
        ]
        details = "; ".join(e.label for e in critical_entries[:3]) or "<unspecified>"
        risks.append(
            ReliabilityRisk(
                label="critical_analytics_regression",
                level=RiskLevel.CRITICAL,
                rationale=(
                    f"replay analytics delta reported "
                    f"{len(critical_entries)} critical regression(s): "
                    f"{details}"
                ),
            )
        )
    elif analytics_delta.severity == DeltaSeverity.REGRESSION:
        risks.append(
            ReliabilityRisk(
                label="analytics_regression",
                level=RiskLevel.HIGH,
                rationale=(
                    f"replay analytics delta reported a regression "
                    f"({analytics_delta.severity.value})"
                ),
            )
        )
    elif analytics_delta.severity == DeltaSeverity.WARNING:
        risks.append(
            ReliabilityRisk(
                label="analytics_warning",
                level=RiskLevel.MODERATE,
                rationale=(
                    "replay analytics delta surfaced warnings; review "
                    "before merge"
                ),
            )
        )

    # 2. Safety path touched.
    if safety_path_touched:
        evidence_for_safety = [
            e for e in evidence_impacts
            if is_safety_critical(e.subsystem) and e.recommended_tools
        ]
        if not evidence_for_safety:
            risks.append(
                ReliabilityRisk(
                    label="safety_path_no_evidence",
                    level=RiskLevel.HIGH,
                    rationale=(
                        "safety-critical subsystem changed but no "
                        "evidence regeneration recipe was emitted"
                    ),
                )
            )
        else:
            risks.append(
                ReliabilityRisk(
                    label="safety_path_touched",
                    level=RiskLevel.MODERATE,
                    rationale=(
                        "safety-critical subsystem changed; regenerate "
                        "the cited evidence artefacts before merge"
                    ),
                    cited_artifacts=tuple(
                        a for e in evidence_for_safety for a in e.recommended_artifacts
                    ),
                )
            )

    # 3. CI workflow changes — static validation removal is high.
    ci_files = [
        f
        for f in source_change.changed_files
        if f.subsystem == Subsystem.CI
    ]
    static_workflow_removed = any(
        f.path.endswith("runtime-static-validation.yml")
        and f.change_type.value in {"deleted", "renamed"}
        for f in ci_files
    )
    if static_workflow_removed:
        risks.append(
            ReliabilityRisk(
                label="static_validation_workflow_removed",
                level=RiskLevel.HIGH,
                rationale=(
                    "the runtime-static-validation workflow was removed "
                    "or renamed; the CI safety net for live-mode probes "
                    "is gone"
                ),
                cited_artifacts=tuple(f.path for f in ci_files),
            )
        )
    elif ci_files:
        risks.append(
            ReliabilityRisk(
                label="ci_workflow_changed",
                level=RiskLevel.MODERATE,
                rationale=(
                    f"{len(ci_files)} CI workflow file(s) changed; "
                    "review whether existing gates are preserved"
                ),
                cited_artifacts=tuple(f.path for f in ci_files),
            )
        )

    # 4. Unknown files.
    unknown = [
        f
        for f in source_change.changed_files
        if f.subsystem == Subsystem.UNKNOWN
    ]
    if unknown:
        risks.append(
            ReliabilityRisk(
                label="unknown_files_touched",
                level=RiskLevel.LOW if len(unknown) < 3 else RiskLevel.MODERATE,
                rationale=(
                    f"{len(unknown)} file(s) outside the documented "
                    "subsystem prefixes were touched; classify them or "
                    "extend the classifier"
                ),
                cited_artifacts=tuple(f.path for f in unknown[:5]),
            )
        )

    # 5. Replay-honesty violations (carried from analytics delta).
    honesty_entries = [
        e
        for e in analytics_delta.entries
        if e.category == "honesty"
        and e.severity in {DeltaSeverity.CRITICAL_REGRESSION, DeltaSeverity.REGRESSION}
    ]
    if honesty_entries:
        risks.append(
            ReliabilityRisk(
                label="replay_honesty_violation",
                level=RiskLevel.CRITICAL,
                rationale=(
                    f"{len(honesty_entries)} replay honesty violation(s) "
                    "(e.g. static-only flagged as bag-backed)"
                ),
            )
        )

    # 6. Documentation-only.
    if (
        impacted_subsystems
        and impacted_subsystems.issubset({Subsystem.DOCS, Subsystem.TESTS})
        and not analytics_delta.entries
    ):
        risks.append(
            ReliabilityRisk(
                label="docs_or_tests_only",
                level=RiskLevel.LOW,
                rationale=(
                    "change touches only documentation / test paths; no "
                    "evidence regeneration required"
                ),
            )
        )

    # Compose the overall risk.
    if not risks:
        return ImpactAssessment(overall_risk=RiskLevel.NONE)
    overall = max(risks, key=lambda r: _RISK_ORDER[r.level]).level
    return ImpactAssessment(risks=risks, overall_risk=overall)
