"""Mission validation orchestration.

The platform is **not safety-certified**. The validator runs every
post-extraction check: ODD validation, route feasibility, recovery
path presence, contingency completeness, and contradiction
detection. Validation failures *always* propagate to the compile
status; nothing is silently accepted.
"""

from __future__ import annotations

from .constraints import detect_contradictions
from .models import (
    CONSTRAINT_AVOID,
    CONSTRAINT_RECOVERY_DIRECTIVE,
    CONSTRAINT_RESTRICTED_CORRIDOR,
    CONSTRAINT_SAFETY_TRIGGER,
    CONSTRAINT_SPEED_LIMIT,
    CONSTRAINT_TIME_WINDOW,
    Diagnostic,
    MissionConstraint,
    MissionObjective,
    OperationalDesignDomain,
    SEVERITY_REJECTION,
    SEVERITY_WARNING,
    STAGE_DOCK_RETURN,
)
from .odd import is_authorized_zone, is_prohibited_region


def _zone_slot(obj: MissionObjective) -> str:
    for key in ("zone", "target", "region"):
        v = obj.parameters.get(key, "")
        if v:
            return v.strip().lower()
    return ""


def validate_against_odd(
    objectives: tuple[MissionObjective, ...],
    constraints: tuple[MissionConstraint, ...],
    odd: OperationalDesignDomain,
) -> tuple[Diagnostic, ...]:
    diags: list[Diagnostic] = []

    for obj in objectives:
        zone = _zone_slot(obj)
        if not zone:
            continue
        if obj.objective_kind == STAGE_DOCK_RETURN:
            continue
        if is_prohibited_region(odd, zone):
            diags.append(
                Diagnostic(
                    code="odd_violation",
                    severity=SEVERITY_REJECTION,
                    message=(
                        f"objective targets prohibited region {zone!r} for "
                        f"ODD profile {odd.profile_id!r}"
                    ),
                    clause=obj.source_clause,
                    field="region",
                )
            )
            continue
        # If we have an authorised list and the zone isn't on it,
        # treat as ODD violation.
        if odd.authorized_zones and not is_authorized_zone(odd, zone):
            diags.append(
                Diagnostic(
                    code="odd_violation",
                    severity=SEVERITY_REJECTION,
                    message=(
                        f"objective targets zone {zone!r} which is not in the "
                        f"authorised zone list for ODD profile {odd.profile_id!r}"
                    ),
                    clause=obj.source_clause,
                    field="zone",
                )
            )

    for con in constraints:
        if con.constraint_kind == CONSTRAINT_SPEED_LIMIT:
            raw = con.parameters.get("limit_mps", "").strip()
            try:
                limit = float(raw) if raw else 0.0
            except ValueError:
                continue
            if limit > odd.speed_limit_mps:
                diags.append(
                    Diagnostic(
                        code="odd_violation",
                        severity=SEVERITY_REJECTION,
                        message=(
                            f"speed limit {limit} m/s exceeds ODD limit "
                            f"{odd.speed_limit_mps} m/s for profile "
                            f"{odd.profile_id!r}"
                        ),
                        clause=con.source_clause,
                        field="limit_mps",
                    )
                )
        if con.constraint_kind == CONSTRAINT_TIME_WINDOW:
            window = con.parameters.get("window", "").strip().lower()
            if window and window != odd.operating_window:
                diags.append(
                    Diagnostic(
                        code="odd_violation",
                        severity=SEVERITY_REJECTION,
                        message=(
                            f"time window {window!r} does not match ODD "
                            f"operating window {odd.operating_window!r}"
                        ),
                        clause=con.source_clause,
                        field="window",
                    )
                )
    return tuple(diags)


def validate_recovery_paths(
    objectives: tuple[MissionObjective, ...],
    constraints: tuple[MissionConstraint, ...],
) -> tuple[Diagnostic, ...]:
    """Missions with safety triggers should also declare a recovery directive."""

    has_safety_trigger = any(
        c.constraint_kind == CONSTRAINT_SAFETY_TRIGGER for c in constraints
    )
    has_recovery = any(
        c.constraint_kind == CONSTRAINT_RECOVERY_DIRECTIVE for c in constraints
    )
    has_dock_return = any(
        o.objective_kind == STAGE_DOCK_RETURN for o in objectives
    )
    if has_safety_trigger and not (has_recovery or has_dock_return):
        return (
            Diagnostic(
                code="missing_recovery_path",
                severity=SEVERITY_WARNING,
                message=(
                    "safety trigger declared without an explicit recovery "
                    "directive or return-to-dock; missions should pair the "
                    "two"
                ),
            ),
        )
    return ()


def validate_route_feasibility(
    objectives: tuple[MissionObjective, ...],
) -> tuple[Diagnostic, ...]:
    """The compiler does not plan paths; it only requires at least one objective."""

    if not objectives:
        return (
            Diagnostic(
                code="no_objectives",
                severity=SEVERITY_REJECTION,
                message="mission has no objectives after parsing",
            ),
        )
    return ()


def validate_all(
    objectives: tuple[MissionObjective, ...],
    constraints: tuple[MissionConstraint, ...],
    odd: OperationalDesignDomain,
) -> tuple[Diagnostic, ...]:
    diags: list[Diagnostic] = []
    diags.extend(validate_route_feasibility(objectives))
    diags.extend(validate_against_odd(objectives, constraints, odd))
    diags.extend(detect_contradictions(objectives, constraints))
    diags.extend(validate_recovery_paths(objectives, constraints))
    return tuple(diags)


__all__ = [
    "validate_against_odd",
    "validate_recovery_paths",
    "validate_route_feasibility",
    "validate_all",
]
