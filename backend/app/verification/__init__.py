"""Phase 3 verification and evidence layer.

This package operationalises the platform's "engineering evidence"
discipline. It does **not** add new autonomy features. It produces:

* a registry of named requirements (``REQ-*`` IDs) traceable to docs,
  modules, scenarios, tests, and evidence artefacts;
* a scenario verifier that runs each Phase 1C / Phase 2 scenario and
  records expected vs observed outcomes;
* command-path, safety-transition, and replay-integrity audits;
* an evidence generator that writes per-scenario JSON + Markdown
  artefacts;
* a scenario verification report and a traceability matrix.

The verification layer is intentionally honest about its limits. A
scenario that cannot be executed in the current environment is
reported as ``not_executed`` with a reason; a partial evaluation is
reported as ``partial``. The platform is **not safety-certified** —
this layer demonstrates safety-oriented architecture, deterministic
validation, and evidence generation discipline.
"""

from app.verification.acceptance import (
    AcceptanceStatus,
    aggregate_status,
)
from app.verification.command_audit import (
    CommandAuditResult,
    audit_command_path,
)
from app.verification.evidence import (
    EvidenceArtifact,
    ScenarioEvidence,
    write_evidence,
)
from app.verification.replay_integrity import (
    ReplayIntegrityResult,
    verify_replay_integrity,
)
from app.verification.report_generator import (
    VerificationReport,
    render_scenario_verification_report,
)
from app.verification.requirements import (
    REQUIREMENTS,
    Requirement,
    RequirementKind,
    RequirementsRegistry,
    requirement_by_id,
)
from app.verification.safety_audit import (
    SafetyTransitionAuditResult,
    audit_safety_transitions,
)
from app.verification.scenario_verifier import (
    ScenarioCheck,
    ScenarioExpectation,
    ScenarioVerification,
    SCENARIO_EXPECTATIONS,
    verify_scenario,
)
from app.verification.traceability import (
    TraceabilityMatrix,
    TraceabilityRow,
    build_traceability_matrix,
)

__all__ = [
    "AcceptanceStatus",
    "CommandAuditResult",
    "EvidenceArtifact",
    "REQUIREMENTS",
    "ReplayIntegrityResult",
    "Requirement",
    "RequirementKind",
    "RequirementsRegistry",
    "SCENARIO_EXPECTATIONS",
    "SafetyTransitionAuditResult",
    "ScenarioCheck",
    "ScenarioEvidence",
    "ScenarioExpectation",
    "ScenarioVerification",
    "TraceabilityMatrix",
    "TraceabilityRow",
    "VerificationReport",
    "aggregate_status",
    "audit_command_path",
    "audit_safety_transitions",
    "build_traceability_matrix",
    "render_scenario_verification_report",
    "requirement_by_id",
    "verify_replay_integrity",
    "verify_scenario",
    "write_evidence",
]
