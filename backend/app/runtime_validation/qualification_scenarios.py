"""Qualification-scenario format and loader.

Phase 5 introduces a YAML pack format that pins, per scenario:

* the scenario id and purpose;
* the topics that **must** be advertised;
* the nodes that **must** be alive;
* the safety state the run must reach (terminal state);
* the events that **must** be present;
* the events that **must not** be present;
* the replay artefacts that **must** be present;
* the qualification rules to apply (zero-motion, command-path,
  replay-integrity, etc.);
* the expected outcome ("passed", "failed", "partial").

Loading a pack returns a :class:`QualificationScenario` plus a
validation result so a malformed scenario fails loudly instead of
silently passing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional

from app.verification.acceptance import AcceptanceStatus


_VALID_RULES: frozenset[str] = frozenset(
    {
        "command_path_invariants",
        "replay_integrity",
        "safety_transitions",
        "zero_motion_in_safe_stop",
        "no_authorized_motion_in_estop",
        "topic_freshness",
        "tf_tree_complete",
    }
)

_VALID_OUTCOMES: frozenset[str] = frozenset(
    {"passed", "failed", "partial"}
)


@dataclass(frozen=True)
class QualificationScenario:
    scenario_id: str
    purpose: str
    required_topics: tuple[str, ...]
    required_nodes: tuple[str, ...]
    required_safety_state: str
    required_events: tuple[str, ...]
    forbidden_events: tuple[str, ...]
    required_replay_artifacts: tuple[str, ...]
    expected_outcome: str
    qualification_rules: tuple[str, ...]
    source_path: Optional[Path] = None
    description: str = ""

    def as_dict(self) -> dict:
        return {
            "scenario_id": self.scenario_id,
            "purpose": self.purpose,
            "required_topics": list(self.required_topics),
            "required_nodes": list(self.required_nodes),
            "required_safety_state": self.required_safety_state,
            "required_events": list(self.required_events),
            "forbidden_events": list(self.forbidden_events),
            "required_replay_artifacts": list(self.required_replay_artifacts),
            "expected_outcome": self.expected_outcome,
            "qualification_rules": list(self.qualification_rules),
            "source_path": str(self.source_path) if self.source_path else "",
            "description": self.description,
        }


@dataclass
class ScenarioValidation:
    scenario_id: str
    status: AcceptanceStatus
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.status == AcceptanceStatus.PASSED

    def as_dict(self) -> dict:
        return {
            "scenario_id": self.scenario_id,
            "status": self.status.value,
            "ok": self.ok,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


def parse_scenario(data: dict, *, source_path: Optional[Path] = None) -> tuple[
    Optional[QualificationScenario], ScenarioValidation
]:
    """Parse + validate a YAML/dict scenario.

    Returns ``(scenario_or_None, validation)``. The validation always
    carries the per-field errors so a caller can surface them in a
    qualification report rather than swallowing them.
    """

    sid = data.get("scenario_id") if isinstance(data, dict) else None
    sid_str = str(sid) if isinstance(sid, str) else "<unknown>"
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(data, dict):
        errors.append("scenario root must be a mapping")
        return (
            None,
            ScenarioValidation(
                scenario_id=sid_str,
                status=AcceptanceStatus.FAILED,
                errors=errors,
            ),
        )

    if not isinstance(sid, str) or not sid:
        errors.append("scenario_id must be a non-empty string")
    purpose = data.get("purpose", "")
    if not isinstance(purpose, str) or not purpose:
        errors.append("purpose must be a non-empty string")

    required_topics = _expect_string_list(data, "required_topics", errors)
    required_nodes = _expect_string_list(data, "required_nodes", errors)
    required_events = _expect_string_list(data, "required_events", errors)
    forbidden_events = _expect_string_list(data, "forbidden_events", errors)
    required_replay_artifacts = _expect_string_list(
        data, "required_replay_artifacts", errors
    )
    qualification_rules = _expect_string_list(data, "qualification_rules", errors)

    safety_state = data.get("required_safety_state", "")
    if not isinstance(safety_state, str) or not safety_state:
        errors.append("required_safety_state must be a non-empty string")

    expected_outcome = data.get("expected_outcome", "")
    if expected_outcome not in _VALID_OUTCOMES:
        errors.append(
            f"expected_outcome must be one of {sorted(_VALID_OUTCOMES)}; "
            f"got {expected_outcome!r}"
        )

    for rule in qualification_rules:
        if rule not in _VALID_RULES:
            errors.append(
                f"qualification rule {rule!r} is not recognised; "
                f"choose from {sorted(_VALID_RULES)}"
            )

    overlap = set(required_events) & set(forbidden_events)
    if overlap:
        errors.append(
            "events appear in both required and forbidden: " + ", ".join(sorted(overlap))
        )

    description = data.get("description", "")
    if not isinstance(description, str):
        warnings.append("description should be a string")
        description = ""

    if errors:
        return (
            None,
            ScenarioValidation(
                scenario_id=sid_str,
                status=AcceptanceStatus.FAILED,
                errors=errors,
                warnings=warnings,
            ),
        )

    scenario = QualificationScenario(
        scenario_id=sid_str,
        purpose=purpose,
        required_topics=tuple(required_topics),
        required_nodes=tuple(required_nodes),
        required_safety_state=safety_state,
        required_events=tuple(required_events),
        forbidden_events=tuple(forbidden_events),
        required_replay_artifacts=tuple(required_replay_artifacts),
        expected_outcome=expected_outcome,
        qualification_rules=tuple(qualification_rules),
        source_path=source_path,
        description=description,
    )
    validation = ScenarioValidation(
        scenario_id=sid_str,
        status=AcceptanceStatus.PASSED,
        warnings=warnings,
    )
    return scenario, validation


def _expect_string_list(data: dict, key: str, errors: list[str]) -> list[str]:
    value = data.get(key, [])
    if not isinstance(value, list):
        errors.append(f"{key!r} must be a list of strings")
        return []
    out: list[str] = []
    for entry in value:
        if not isinstance(entry, str):
            errors.append(f"{key!r}: entries must be strings; got {entry!r}")
            continue
        out.append(entry)
    return out


def load_scenario_pack_from_dir(scenarios_dir: Path) -> tuple[
    list[QualificationScenario], list[ScenarioValidation]
]:
    """Load every ``*.yaml`` file under ``scenarios_dir``.

    Returns ``(scenarios, validations)``. Both lists have one entry
    per file. A file that fails validation contributes to
    ``validations`` only (with status ``failed``); a successful one
    appears in both lists.
    """

    import yaml

    scenarios: list[QualificationScenario] = []
    validations: list[ScenarioValidation] = []
    if not scenarios_dir.exists():
        return scenarios, validations
    for path in sorted(scenarios_dir.glob("*.yaml")):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            validations.append(
                ScenarioValidation(
                    scenario_id=path.stem,
                    status=AcceptanceStatus.FAILED,
                    errors=[f"YAML parse error: {exc}"],
                )
            )
            continue
        scenario, validation = parse_scenario(data, source_path=path)
        validations.append(validation)
        if scenario is not None:
            scenarios.append(scenario)
    return scenarios, validations
