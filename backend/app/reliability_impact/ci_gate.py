"""Deterministic CI gate decision.

The gate fails only on the documented critical conditions. It
warns on moderate signals and never fails for missing live runtime
evidence on a github-hosted runner. The decision is independent of
the risk level (a "high" risk can still pass the gate if it falls
short of the failure criteria — risk is informational, the gate is
the hard signal).
"""

from __future__ import annotations

import os
from typing import Iterable, Optional

from app.reliability_impact.models import (
    AnalyticsDeltaEntry,
    DeltaSeverity,
    EvidenceImpact,
    GateDecision,
    GateStatus,
    ImpactAssessment,
    ReliabilityRisk,
    ReplayAnalyticsDelta,
    RiskLevel,
    SourceChange,
    Subsystem,
    SubsystemImpact,
    is_safety_critical,
)


def decide_gate(
    *,
    source_change: SourceChange,
    subsystem_impacts: Iterable[SubsystemImpact],
    evidence_impacts: Iterable[EvidenceImpact],
    analytics_delta: ReplayAnalyticsDelta,
    assessment: ImpactAssessment,
    traceability_passed: Optional[bool] = None,
    tests_passed: Optional[bool] = None,
    is_github_hosted: Optional[bool] = None,
) -> GateDecision:
    """Return the deterministic gate decision."""

    failures: list[str] = []
    warnings: list[str] = []
    notes: list[str] = []

    if is_github_hosted is None:
        is_github_hosted = _detect_github_hosted_runner()

    subsystem_impacts = list(subsystem_impacts)
    evidence_impacts = list(evidence_impacts)
    impacted_subsystems = {s.subsystem for s in subsystem_impacts}

    # 1. Critical analytics regression fails.
    if analytics_delta.severity == DeltaSeverity.CRITICAL_REGRESSION:
        critical_entries = [
            e for e in analytics_delta.entries
            if e.severity == DeltaSeverity.CRITICAL_REGRESSION
        ]
        failures.append(
            "critical_analytics_regression: "
            + "; ".join(e.label for e in critical_entries[:3])
        )

    # 2. Replay honesty violations fail.
    honesty_failures = [
        e for e in analytics_delta.entries
        if e.category == "honesty"
        and e.severity in {DeltaSeverity.CRITICAL_REGRESSION, DeltaSeverity.REGRESSION}
    ]
    if honesty_failures:
        failures.append(
            "replay_honesty_violation: "
            + "; ".join(e.label for e in honesty_failures[:3])
        )

    # 3. Safety / motion changes with no evidence recipe fail.
    safety_change_paths = [
        f.path for f in source_change.changed_files
        if is_safety_critical(f.subsystem)
    ]
    if safety_change_paths:
        evidence_for_safety = [
            e for e in evidence_impacts
            if is_safety_critical(e.subsystem) and e.recommended_tools
        ]
        if not evidence_for_safety:
            failures.append(
                "safety_path_no_evidence: safety-critical subsystem "
                "changed but no evidence regeneration recipe emitted"
            )

    # 4. Static validation workflow removal fails.
    for f in source_change.changed_files:
        if f.subsystem != Subsystem.CI:
            continue
        if "runtime-static-validation.yml" in f.path and f.change_type.value in {
            "deleted",
            "renamed",
        }:
            failures.append(
                "static_validation_workflow_removed: "
                f"{f.path} was {f.change_type.value}"
            )

    # 5. Traceability failure (only when the caller supplied a result).
    if traceability_passed is False:
        failures.append("traceability_matrix_failed")
    elif traceability_passed is None:
        notes.append("traceability matrix status not supplied")

    # 6. Tests failed (only when explicit).
    if tests_passed is False:
        failures.append("tests_failed")
    elif tests_passed is None:
        notes.append("test status not supplied")

    # Warnings.
    if analytics_delta.severity == DeltaSeverity.REGRESSION:
        warnings.append("analytics_regression")
    if analytics_delta.severity == DeltaSeverity.WARNING:
        warnings.append("analytics_warning")
    if any(w.startswith("baseline ") or "baseline" in w for w in analytics_delta.warnings):
        warnings.append("baseline_unavailable_or_partial")
    if any(f.subsystem == Subsystem.UNKNOWN for f in source_change.changed_files):
        warnings.append("unknown_files_touched")
    for impact in subsystem_impacts:
        if impact.subsystem == Subsystem.UNKNOWN:
            continue
    unmapped_subsystems = [
        i.subsystem.value for i in subsystem_impacts
        if i.subsystem in {Subsystem.UNKNOWN}
    ]
    if unmapped_subsystems:
        warnings.append(
            "unmapped_subsystems: " + ",".join(unmapped_subsystems)
        )

    # Notes: never fail solely because live runtime evidence is missing
    # on github-hosted CI. Surface this explicitly when relevant.
    live_runtime_missing = any(
        e.category in {"bag", "honesty"}
        and e.severity == DeltaSeverity.CRITICAL_REGRESSION
        and ("missing_bag" in str(e.current_value) or e.label.startswith("bag_status"))
        for e in analytics_delta.entries
    )
    if is_github_hosted and live_runtime_missing:
        notes.append(
            "live runtime evidence missing on github-hosted runner; the "
            "gate honours the documented exception and does not fail"
        )

    # Final status.
    if failures:
        status = GateStatus.FAILED
    elif warnings:
        status = GateStatus.WARNING
    else:
        status = GateStatus.PASSED

    # Risk informational note.
    if assessment.overall_risk in {RiskLevel.HIGH, RiskLevel.CRITICAL}:
        notes.append(
            f"risk_assessment={assessment.overall_risk.value}; review "
            "carefully even when the gate passes"
        )

    return GateDecision(
        status=status,
        failures=tuple(failures),
        warnings=tuple(warnings),
        notes=tuple(notes),
    )


def _detect_github_hosted_runner() -> bool:
    """Heuristic: github-hosted runners set ``RUNNER_ENVIRONMENT=github-hosted``.

    Self-hosted runners typically set it to ``self-hosted``. When
    the variable is missing the function defaults to True — the
    safer choice for the honesty rule.
    """

    env = os.environ.get("RUNNER_ENVIRONMENT", "").lower()
    if not env:
        return True
    return env == "github-hosted"
