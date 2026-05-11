"""Deterministic mission risk classification.

The platform is **not safety-certified**. Risk scoring is a pure
function of the compiled mission's structure and the active ODD;
it never claims predictive power.
"""

from __future__ import annotations

from .models import (
    CONSTRAINT_RECOVERY_DIRECTIVE,
    CONSTRAINT_RESTRICTED_CORRIDOR,
    CONSTRAINT_SAFETY_TRIGGER,
    CONSTRAINT_SPEED_LIMIT,
    CONSTRAINT_TIME_WINDOW,
    Diagnostic,
    MissionConstraint,
    MissionObjective,
    MissionRisk,
    OperationalDesignDomain,
    RISK_BANDS,
    RISK_CRITICAL,
    RISK_ELEVATED,
    RISK_HIGH,
    RISK_INFORMATIONAL,
    RISK_LOW,
    RISK_MODERATE,
    STAGE_INSPECT,
    STAGE_PATROL,
)


# Thresholds are inclusive lower bounds.
_BAND_THRESHOLDS: tuple[tuple[int, str], ...] = (
    (90, RISK_CRITICAL),
    (70, RISK_HIGH),
    (50, RISK_ELEVATED),
    (30, RISK_MODERATE),
    (10, RISK_LOW),
    (0, RISK_INFORMATIONAL),
)


def _band_for_score(score: int) -> str:
    for threshold, band in _BAND_THRESHOLDS:
        if score >= threshold:
            return band
    return RISK_INFORMATIONAL


def classify_risk(
    *,
    objectives: tuple[MissionObjective, ...],
    constraints: tuple[MissionConstraint, ...],
    diagnostics: tuple[Diagnostic, ...],
    odd: OperationalDesignDomain,
) -> MissionRisk:
    score = 0
    drivers: list[str] = []

    # +10 per objective beyond the first (mission complexity).
    if len(objectives) > 1:
        complexity = (len(objectives) - 1) * 10
        score += complexity
        drivers.append(f"mission_complexity:{complexity}")

    # +15 per patrol/inspect (extended autonomy time).
    extended = sum(
        1 for o in objectives if o.objective_kind in (STAGE_PATROL, STAGE_INSPECT)
    )
    if extended:
        score += extended * 15
        drivers.append(f"extended_autonomy_stages:{extended}")

    # +20 per restricted-corridor / time-window constraint.
    for con in constraints:
        if con.constraint_kind == CONSTRAINT_RESTRICTED_CORRIDOR:
            score += 20
            drivers.append("restricted_corridor_constraint")
        if con.constraint_kind == CONSTRAINT_TIME_WINDOW:
            score += 10
            drivers.append("time_window_constraint")
        if con.constraint_kind == CONSTRAINT_SAFETY_TRIGGER:
            score += 10
            drivers.append("safety_trigger_present")
        if con.constraint_kind == CONSTRAINT_RECOVERY_DIRECTIVE:
            # Recovery directive lowers risk a touch.
            score -= 5
            drivers.append("recovery_directive_present")
        if con.constraint_kind == CONSTRAINT_SPEED_LIMIT:
            try:
                raw = float(con.parameters.get("limit_mps", "0") or 0)
            except ValueError:
                raw = 0.0
            if raw and raw < odd.speed_limit_mps:
                score -= 5
                drivers.append("speed_limited_below_odd")

    # Diagnostic-driven additions.
    warning_count = sum(1 for d in diagnostics if d.severity == "warning")
    rejection_count = sum(1 for d in diagnostics if d.severity == "rejection")
    if warning_count:
        score += 5 * warning_count
        drivers.append(f"open_warnings:{warning_count}")
    if rejection_count:
        # Any rejection forces the mission into critical.
        score = max(score, 95)
        drivers.append(f"rejections:{rejection_count}")

    score = max(0, min(score, 100))
    band = _band_for_score(score)

    mitigations: list[str] = []
    if band in (RISK_ELEVATED, RISK_HIGH, RISK_CRITICAL):
        mitigations.append("supervised operator review before execution")
    if band in (RISK_HIGH, RISK_CRITICAL):
        mitigations.append("dry-run in simulation before live execution")
    if any(c.constraint_kind == CONSTRAINT_SAFETY_TRIGGER for c in constraints) and not any(
        c.constraint_kind == CONSTRAINT_RECOVERY_DIRECTIVE for c in constraints
    ):
        mitigations.append("attach an explicit recovery directive (e.g. return-to-dock)")

    reviewer_actions: list[str] = []
    if band == RISK_CRITICAL:
        reviewer_actions.append("manual approval required - critical mission cannot auto-pass")
    if rejection_count:
        reviewer_actions.append("resolve compile rejections before submission")

    return MissionRisk(
        band=band,
        score=score,
        drivers=tuple(drivers),
        mitigations=tuple(mitigations),
        required_reviewer_actions=tuple(reviewer_actions),
    )


__all__ = ["classify_risk"]
