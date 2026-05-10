"""Subsystem -> recommended evidence artefacts + tooling.

The evidence mapper tells the reviewer which tests, scripts, and
artefacts to regenerate after a change. The recommendations are
deterministic, cite the underlying CLI / artefact paths, and never
recommend a regeneration that the analysis layer cannot itself
verify.
"""

from __future__ import annotations

from app.reliability_impact.models import (
    EvidenceImpact,
    RequirementImpact,
    Subsystem,
    SubsystemImpact,
)


_SUBSYSTEM_TO_TOOLS: dict[Subsystem, tuple[str, ...]] = {
    Subsystem.SAFETY: (
        "tools/audit_command_path.py",
        "tools/audit_safety_transitions.py",
        "tools/generate_evidence.py",
        "tools/generate_traceability.py",
    ),
    Subsystem.MISSION: (
        "tools/generate_evidence.py",
        "tools/audit_safety_transitions.py",
    ),
    Subsystem.MOTION: (
        "tools/audit_command_path.py",
        "tools/generate_evidence.py",
    ),
    Subsystem.REPLAY: (
        "tools/verify_replay_integrity.py",
        "tools/generate_evidence.py",
    ),
    Subsystem.INCIDENT_ANALYSIS: (
        "rover_ws/tools/reconstruct_incident.py",
        "rover_ws/tools/index_incidents.py",
        "rover_ws/tools/compare_incidents.py",
    ),
    Subsystem.REPLAY_REVIEW: (
        "rover_ws/tools/build_replay_review_bundle.py",
        "rover_ws/tools/validate_replay_review.py",
        "rover_ws/tools/list_replay_reviews.py",
    ),
    Subsystem.REPLAY_ANALYTICS: (
        "rover_ws/tools/analyze_replay_coverage.py",
        "rover_ws/tools/generate_replay_analytics.py",
        "rover_ws/tools/compare_replay_reviews.py",
        "rover_ws/tools/audit_replay_reviews.py",
    ),
    Subsystem.RUNTIME_VALIDATION: (
        "rover_ws/tools/qualify_ros_host.py",
        "rover_ws/tools/live_runtime_validator.py",
        "rover_ws/tools/qualified_runtime_run.py",
    ),
    Subsystem.VERIFICATION: (
        "tools/generate_traceability.py",
        "tools/generate_verification_report.py",
        "tools/generate_evidence.py",
    ),
    Subsystem.RELIABILITY_IMPACT: (
        "rover_ws/tools/analyze_source_impact.py",
        "rover_ws/tools/reliability_impact_gate.py",
    ),
    Subsystem.ROS_WORKSPACE: (
        "rover_ws/tools/live_runtime_validator.py",
        "rover_ws/tools/qualified_runtime_run.py",
    ),
    Subsystem.GAZEBO_SIMULATION: (
        "rover_ws/tools/live_runtime_validator.py",
        "rover_ws/tools/qualified_runtime_run.py",
    ),
    Subsystem.OBSERVABILITY: (
        "rover_ws/tools/live_runtime_validator.py",
        "tools/verify_replay_integrity.py",
    ),
    Subsystem.CI: (
        "tools/generate_traceability.py",
    ),
    Subsystem.EVIDENCE: (
        "tools/generate_evidence.py",
        "rover_ws/tools/generate_replay_analytics.py",
    ),
    Subsystem.DOCS: (),
    Subsystem.TESTS: (),
    Subsystem.UNKNOWN: (),
}


_SUBSYSTEM_TO_ARTIFACTS: dict[Subsystem, tuple[str, ...]] = {
    Subsystem.SAFETY: (
        "evidence/scenarios/",
        "incidents/",
        "verification/traceability.json",
    ),
    Subsystem.MISSION: (
        "evidence/scenarios/",
        "verification/traceability.json",
    ),
    Subsystem.MOTION: (
        "evidence/scenarios/",
        "verification/traceability.json",
    ),
    Subsystem.REPLAY: (
        "evidence/scenarios/",
        "verification/traceability.json",
    ),
    Subsystem.INCIDENT_ANALYSIS: (
        "incidents/",
        "docs/INCIDENT_INDEX.md",
    ),
    Subsystem.REPLAY_REVIEW: (
        "incidents/",
        "docs/REPLAY_REVIEW_INDEX.md",
    ),
    Subsystem.REPLAY_ANALYTICS: (
        "incidents/analytics/",
        "docs/REPLAY_ANALYTICS_INDEX.md",
    ),
    Subsystem.RUNTIME_VALIDATION: (
        "evidence/runtime/",
        "docs/RUNTIME_VALIDATION_REPORT.md",
    ),
    Subsystem.VERIFICATION: (
        "verification/",
        "docs/TRACEABILITY_MATRIX.md",
        "docs/SCENARIO_VERIFICATION_REPORT.md",
    ),
    Subsystem.RELIABILITY_IMPACT: (
        "reliability-impact/",
        "reliability-baselines/",
    ),
    Subsystem.ROS_WORKSPACE: (
        "evidence/runtime/",
    ),
    Subsystem.GAZEBO_SIMULATION: (
        "evidence/runtime/",
    ),
    Subsystem.OBSERVABILITY: (
        "evidence/runtime/",
        "evidence/scenarios/",
    ),
    Subsystem.CI: (
        ".github/workflows/",
    ),
    Subsystem.EVIDENCE: (
        "evidence/",
        "incidents/",
    ),
    Subsystem.DOCS: (),
    Subsystem.TESTS: (),
    Subsystem.UNKNOWN: (),
}


def map_evidence(
    subsystem_impact: SubsystemImpact,
    requirement_impact: RequirementImpact,
) -> EvidenceImpact:
    notes = ""
    if subsystem_impact.subsystem == Subsystem.UNKNOWN:
        notes = (
            "unknown subsystem; no automated recommendation. Classify "
            "the path explicitly to enable evidence mapping."
        )
    if subsystem_impact.subsystem == Subsystem.DOCS:
        notes = "documentation-only change; rerun the traceability matrix to refresh links."
    return EvidenceImpact(
        subsystem=subsystem_impact.subsystem,
        requirement_ids=requirement_impact.requirement_ids,
        recommended_tools=_SUBSYSTEM_TO_TOOLS.get(
            subsystem_impact.subsystem, ()
        ),
        recommended_artifacts=_SUBSYSTEM_TO_ARTIFACTS.get(
            subsystem_impact.subsystem, ()
        ),
        notes=notes,
    )


def map_evidence_for_impacts(
    impacts: list[SubsystemImpact],
    requirement_impacts: list[RequirementImpact],
) -> list[EvidenceImpact]:
    out: list[EvidenceImpact] = []
    requirement_by_subsystem = {r.subsystem: r for r in requirement_impacts}
    for impact in impacts:
        req = requirement_by_subsystem.get(
            impact.subsystem,
            RequirementImpact(subsystem=impact.subsystem, requirement_ids=()),
        )
        out.append(map_evidence(impact, req))
    return out
