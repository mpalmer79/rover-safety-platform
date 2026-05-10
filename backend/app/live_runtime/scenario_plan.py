"""Scenario-plan loading + validation.

The platform is **not safety-certified**. Scenario plans live as
YAML for editing convenience; this module loads them via PyYAML if
available and falls back to a tiny tolerant parser for the
constrained subset Project Boundary uses (mappings, scalars, and
lists of scalars / mappings, all 2-space indented).
"""

from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Any

from .models import ScenarioPlan, ScenarioPlanEntry


_REQUIRED_ENTRY_FIELDS: tuple[str, ...] = (
    "scenario_id",
    "purpose",
    "launch_file",
    "expected_topics",
    "expected_safety_states",
    "expected_events",
    "required_bag_topics",
    "timeout_seconds",
    "evidence_required",
    "failure_mode",
)


def _try_pyyaml(text: str) -> dict[str, Any] | None:
    try:
        import yaml  # type: ignore[import-not-found]
    except ImportError:
        return None
    try:
        return yaml.safe_load(text)  # type: ignore[no-any-return]
    except Exception:
        return None


def _fallback_parse(text: str) -> dict[str, Any] | None:
    """Tolerant parser for the YAML subset we actually emit.

    Supports:
      * top-level scalars and lists,
      * 2-space indented mappings,
      * lists of scalars (``- foo``) and lists of mappings
        (``- key: value`` continuations).
    """

    lines = [line.rstrip() for line in text.splitlines()]
    pos = 0

    def parse_scalar(raw: str) -> Any:
        s = raw.strip()
        if s.startswith("\"") and s.endswith("\"") and len(s) >= 2:
            return s[1:-1]
        if s.startswith("'") and s.endswith("'") and len(s) >= 2:
            return s[1:-1]
        if s.lower() in ("true", "false"):
            return s.lower() == "true"
        if s.lower() in ("null", "~"):
            return None
        if re.fullmatch(r"-?\d+", s):
            return int(s)
        if re.fullmatch(r"-?\d+\.\d+", s):
            return float(s)
        return s

    def indent_of(line: str) -> int:
        return len(line) - len(line.lstrip(" "))

    def parse_block(min_indent: int) -> tuple[Any, int]:
        nonlocal pos
        # Skip blanks/comments.
        while pos < len(lines) and (not lines[pos].strip() or lines[pos].lstrip().startswith("#")):
            pos += 1
        if pos >= len(lines):
            return None, pos
        line = lines[pos]
        ind = indent_of(line)
        if ind < min_indent:
            return None, pos
        stripped = line.lstrip()
        # List items.
        if stripped.startswith("- "):
            items: list[Any] = []
            while pos < len(lines):
                if not lines[pos].strip() or lines[pos].lstrip().startswith("#"):
                    pos += 1
                    continue
                cur_ind = indent_of(lines[pos])
                cur = lines[pos].lstrip()
                if cur_ind != ind or not cur.startswith("- "):
                    break
                rest = cur[2:]
                pos += 1
                if ":" in rest and not rest.startswith("\"") and not rest.startswith("'"):
                    # It's a mapping starting on this line.
                    key, _, val = rest.partition(":")
                    val = val.strip()
                    obj: dict[str, Any] = {}
                    if val:
                        obj[key.strip()] = parse_scalar(val)
                    # Read continuation mapping at indent ind+2.
                    while pos < len(lines):
                        if not lines[pos].strip() or lines[pos].lstrip().startswith("#"):
                            pos += 1
                            continue
                        nind = indent_of(lines[pos])
                        if nind <= ind:
                            break
                        if nind != ind + 2:
                            # Could be a nested list/mapping; fall through to recursive parse.
                            child, _ = parse_block(ind + 2)
                            if isinstance(child, dict):
                                obj.update(child)
                            break
                        kline = lines[pos].lstrip()
                        k, _, v = kline.partition(":")
                        v = v.strip()
                        pos += 1
                        if v == "":
                            child, _ = parse_block(nind + 2)
                            obj[k.strip()] = child if child is not None else []
                        else:
                            obj[k.strip()] = parse_scalar(v)
                    items.append(obj)
                else:
                    items.append(parse_scalar(rest))
            return items, pos
        # Mapping at this indent.
        result: dict[str, Any] = {}
        while pos < len(lines):
            if not lines[pos].strip() or lines[pos].lstrip().startswith("#"):
                pos += 1
                continue
            cur_ind = indent_of(lines[pos])
            if cur_ind != ind:
                break
            cur = lines[pos].lstrip()
            if cur.startswith("- "):
                break
            if ":" not in cur:
                pos += 1
                continue
            k, _, v = cur.partition(":")
            v = v.strip()
            pos += 1
            if v == "":
                child, _ = parse_block(ind + 2)
                result[k.strip()] = child if child is not None else []
            else:
                result[k.strip()] = parse_scalar(v)
        return result, pos

    payload, _ = parse_block(0)
    if not isinstance(payload, dict):
        return None
    return payload


def _load_yaml_text(text: str) -> dict[str, Any] | None:
    parsed = _try_pyyaml(text)
    if isinstance(parsed, dict):
        return parsed
    return _fallback_parse(text)


def scenario_plan_from_dict(payload: dict[str, Any]) -> ScenarioPlan:
    plan_id = str(payload.get("plan_id", ""))
    description = str(payload.get("description", ""))
    raw_entries = payload.get("scenarios", []) or []
    if not isinstance(raw_entries, list):
        raw_entries = []
    entries: list[ScenarioPlanEntry] = []
    for raw in raw_entries:
        if not isinstance(raw, dict):
            continue
        entries.append(
            ScenarioPlanEntry(
                scenario_id=str(raw.get("scenario_id", "")),
                purpose=str(raw.get("purpose", "")),
                launch_file=str(raw.get("launch_file", "")),
                expected_topics=tuple(str(x) for x in raw.get("expected_topics", ())),
                expected_safety_states=tuple(
                    str(x) for x in raw.get("expected_safety_states", ())
                ),
                expected_events=tuple(str(x) for x in raw.get("expected_events", ())),
                required_bag_topics=tuple(
                    str(x) for x in raw.get("required_bag_topics", ())
                ),
                timeout_seconds=int(raw.get("timeout_seconds", 0) or 0),
                evidence_required=tuple(
                    str(x) for x in raw.get("evidence_required", ())
                ),
                failure_mode=str(raw.get("failure_mode", "")),
            )
        )
    return ScenarioPlan(
        plan_id=plan_id, description=description, entries=tuple(entries)
    )


def load_scenario_plan(path: Path) -> ScenarioPlan | None:
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError:
        return None
    payload = _load_yaml_text(text)
    if not isinstance(payload, dict):
        return None
    return scenario_plan_from_dict(payload)


def validate_scenario_plan(plan: ScenarioPlan | None) -> tuple[str, ...]:
    if plan is None:
        return ("scenario plan missing or unparseable",)
    warnings: list[str] = []
    if not plan.plan_id:
        warnings.append("scenario plan: missing plan_id")
    if not plan.entries:
        warnings.append("scenario plan: no scenarios declared")
    seen: set[str] = set()
    for idx, entry in enumerate(plan.entries):
        prefix = f"scenario[{idx}] {entry.scenario_id or '<unknown>'}"
        for f in _REQUIRED_ENTRY_FIELDS:
            value = getattr(entry, f)
            if isinstance(value, (str, tuple)) and not value:
                warnings.append(f"{prefix}: missing required field {f}")
            if isinstance(value, int) and value <= 0:
                warnings.append(f"{prefix}: {f} must be positive integer")
        if entry.scenario_id in seen:
            warnings.append(f"{prefix}: duplicate scenario_id")
        if entry.scenario_id:
            seen.add(entry.scenario_id)
    return tuple(warnings)


def scenario_plan_to_dict(plan: ScenarioPlan) -> dict[str, Any]:
    return {
        "plan_id": plan.plan_id,
        "description": plan.description,
        "scenarios": [
            {
                "scenario_id": e.scenario_id,
                "purpose": e.purpose,
                "launch_file": e.launch_file,
                "expected_topics": list(e.expected_topics),
                "expected_safety_states": list(e.expected_safety_states),
                "expected_events": list(e.expected_events),
                "required_bag_topics": list(e.required_bag_topics),
                "timeout_seconds": e.timeout_seconds,
                "evidence_required": list(e.evidence_required),
                "failure_mode": e.failure_mode,
            }
            for e in plan.entries
        ],
    }


__all__ = [
    "scenario_plan_from_dict",
    "scenario_plan_to_dict",
    "load_scenario_plan",
    "validate_scenario_plan",
]
