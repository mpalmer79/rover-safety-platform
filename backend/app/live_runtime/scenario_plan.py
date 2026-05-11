"""Live runtime scenario plan loader.

A scenario plan describes one self-hosted runtime exercise. It pairs
with a qualification scenario (when applicable) but is always
narrower: it captures only what the bag recorder, the launcher, and
the validator need.

Scenario plans are deliberately small. Phase 14 ships a smoke plan
and a core qualification plan; later phases may add more.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional


_REQUIRED_SMOKE_TOPICS: tuple[str, ...] = (
    "/clock",
    "/tf",
    "/tf_static",
    "/odom",
    "/cmd_vel_requested",
    "/cmd_vel_authorized",
    "/safety/state",
    "/safety/events",
    "/system/health",
)


@dataclass(frozen=True)
class LiveScenarioPlan:
    plan_id: str
    description: str
    duration_seconds: float
    launch_files: tuple[str, ...]
    bag_topics: tuple[str, ...]
    required_topics: tuple[str, ...]
    optional_topics: tuple[str, ...] = ()
    expected_safety_state: str = "ACTIVE_NORMAL"
    expected_evidence_mode: str = "bag_backed"
    qualification_scenarios: tuple[str, ...] = field(default_factory=tuple)
    notes: tuple[str, ...] = field(default_factory=tuple)
    smoke: bool = False

    def as_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "description": self.description,
            "duration_seconds": self.duration_seconds,
            "launch_files": list(self.launch_files),
            "bag_topics": list(self.bag_topics),
            "required_topics": list(self.required_topics),
            "optional_topics": list(self.optional_topics),
            "expected_safety_state": self.expected_safety_state,
            "expected_evidence_mode": self.expected_evidence_mode,
            "qualification_scenarios": list(self.qualification_scenarios),
            "notes": list(self.notes),
            "smoke": self.smoke,
        }


def _str_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, (list, tuple)):
        return tuple(str(v) for v in value)
    raise ValueError(f"expected list of strings, got {type(value).__name__}")


def parse_scenario_plan(data: dict) -> LiveScenarioPlan:
    if not isinstance(data, dict):
        raise ValueError("scenario plan must be a mapping")
    plan_id = str(data.get("plan_id", "")).strip()
    if not plan_id:
        raise ValueError("plan_id is required")

    duration = data.get("duration_seconds", 0)
    try:
        duration_value = float(duration)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"duration_seconds must be numeric: {exc}") from exc

    return LiveScenarioPlan(
        plan_id=plan_id,
        description=str(data.get("description", "")).strip(),
        duration_seconds=duration_value,
        launch_files=_str_tuple(data.get("launch_files")),
        bag_topics=_str_tuple(data.get("bag_topics")),
        required_topics=_str_tuple(data.get("required_topics")),
        optional_topics=_str_tuple(data.get("optional_topics")),
        expected_safety_state=str(
            data.get("expected_safety_state", "ACTIVE_NORMAL")
        ),
        expected_evidence_mode=str(
            data.get("expected_evidence_mode", "bag_backed")
        ),
        qualification_scenarios=_str_tuple(data.get("qualification_scenarios")),
        notes=_str_tuple(data.get("notes")),
        smoke=bool(data.get("smoke", False)),
    )


def load_scenario_plan(path: Path) -> LiveScenarioPlan:
    import yaml  # type: ignore[import-untyped]

    raw = Path(path).read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    return parse_scenario_plan(data)


def validate_scenario_plan(
    plan: LiveScenarioPlan, *, require_smoke_topics: Optional[bool] = None
) -> list[str]:
    """Return validation errors. Empty list means valid."""

    errors: list[str] = []
    if not plan.plan_id:
        errors.append("plan_id is required")
    if plan.duration_seconds <= 0:
        errors.append("duration_seconds must be > 0")
    if plan.duration_seconds > 1800:
        errors.append("duration_seconds must be <= 1800 (30 minutes)")
    if not plan.launch_files:
        errors.append("at least one launch_file is required")
    if not plan.bag_topics:
        errors.append("at least one bag_topic is required")
    if not plan.required_topics:
        errors.append("at least one required_topic is required")
    if plan.expected_evidence_mode not in {
        "bag_backed",
        "live_runtime_no_bag",
        "dry_run",
    }:
        errors.append(
            f"expected_evidence_mode must be one of "
            f"'bag_backed', 'live_runtime_no_bag', 'dry_run'; "
            f"got '{plan.expected_evidence_mode}'"
        )

    bag_set = set(plan.bag_topics)
    for required in plan.required_topics:
        if required not in bag_set and required not in plan.optional_topics:
            errors.append(
                f"required_topic '{required}' is not in bag_topics"
            )

    smoke = plan.smoke if require_smoke_topics is None else require_smoke_topics
    if smoke:
        bag_set_smoke = set(plan.bag_topics)
        for required in _REQUIRED_SMOKE_TOPICS:
            if required not in bag_set_smoke:
                errors.append(
                    f"smoke scenario plan must record topic '{required}'"
                )
    return errors


def required_smoke_topics() -> tuple[str, ...]:
    return _REQUIRED_SMOKE_TOPICS
