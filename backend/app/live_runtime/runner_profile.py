"""Runner-profile loading, validation, and JSON Schema.

The platform is **not safety-certified**. The runner profile
describes the host that executes (or would execute) live ROS 2 /
Gazebo runs. Loading and validation never raise on bad input —
problems become structured warnings that the caller can surface as
``not_executed`` reasons.
"""

from __future__ import annotations

import json
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any, Iterable

from .models import (
    QUALIFICATION_STATUS_NOT_QUALIFIED,
    QUALIFICATION_STATUS_PARTIAL,
    QUALIFICATION_STATUS_QUALIFIED,
    QUALIFICATION_STATUS_UNKNOWN,
    RunnerProfile,
)


_REQUIRED_FIELDS: tuple[str, ...] = (
    "runner_id",
    "host_os",
    "ros_distro",
    "gazebo_version",
    "colcon_version",
    "workspace_path",
)


def runner_profile_schema() -> dict[str, Any]:
    """Return the JSON Schema (draft 2020-12) for a runner profile."""

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Live runner profile",
        "type": "object",
        "additionalProperties": False,
        "required": list(_REQUIRED_FIELDS) + [
            "supports_gazebo",
            "supports_rosbag2",
            "supports_foxglove_optional",
        ],
        "properties": {
            "runner_id": {"type": "string", "minLength": 1},
            "host_os": {"type": "string", "minLength": 1},
            "ros_distro": {"type": "string", "minLength": 1},
            "gazebo_version": {"type": "string", "minLength": 1},
            "colcon_version": {"type": "string", "minLength": 1},
            "workspace_path": {"type": "string", "minLength": 1},
            "supports_gazebo": {"type": "boolean"},
            "supports_rosbag2": {"type": "boolean"},
            "supports_foxglove_optional": {"type": "boolean"},
            "runner_labels": {
                "type": "array",
                "items": {"type": "string"},
            },
            "last_qualified_at": {"type": "string"},
            "qualification_status": {
                "type": "string",
                "enum": [
                    QUALIFICATION_STATUS_QUALIFIED,
                    QUALIFICATION_STATUS_PARTIAL,
                    QUALIFICATION_STATUS_NOT_QUALIFIED,
                    QUALIFICATION_STATUS_UNKNOWN,
                ],
            },
            "known_limitations": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
    }


def runner_profile_from_dict(payload: dict[str, Any]) -> RunnerProfile:
    """Build a :class:`RunnerProfile` from a dict (no validation)."""

    return RunnerProfile(
        runner_id=str(payload.get("runner_id", "")),
        host_os=str(payload.get("host_os", "")),
        ros_distro=str(payload.get("ros_distro", "")),
        gazebo_version=str(payload.get("gazebo_version", "")),
        colcon_version=str(payload.get("colcon_version", "")),
        workspace_path=str(payload.get("workspace_path", "")),
        supports_gazebo=bool(payload.get("supports_gazebo", False)),
        supports_rosbag2=bool(payload.get("supports_rosbag2", False)),
        supports_foxglove_optional=bool(
            payload.get("supports_foxglove_optional", False)
        ),
        runner_labels=tuple(str(x) for x in payload.get("runner_labels", ())),
        last_qualified_at=str(payload.get("last_qualified_at", "")),
        qualification_status=str(
            payload.get("qualification_status", QUALIFICATION_STATUS_UNKNOWN)
        ),
        known_limitations=tuple(
            str(x) for x in payload.get("known_limitations", ())
        ),
    )


def runner_profile_to_dict(profile: RunnerProfile) -> dict[str, Any]:
    out = asdict(profile)
    out["runner_labels"] = list(profile.runner_labels)
    out["known_limitations"] = list(profile.known_limitations)
    return out


def load_runner_profile(path: Path) -> RunnerProfile | None:
    """Load a runner profile from a JSON file; return None on failure."""

    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError:
        return None
    if not text.strip():
        return None
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return runner_profile_from_dict(payload)


def validate_runner_profile(profile: RunnerProfile | None) -> tuple[str, ...]:
    """Return a tuple of human-readable warnings; empty if all good."""

    if profile is None:
        return ("runner profile missing or unreadable",)
    warnings: list[str] = []
    for field_name in _REQUIRED_FIELDS:
        value = getattr(profile, field_name)
        if not isinstance(value, str) or not value.strip():
            warnings.append(f"missing required field: {field_name}")
    if not profile.supports_rosbag2:
        warnings.append("runner does not support rosbag2; bag_backed is impossible")
    if not profile.supports_gazebo:
        warnings.append("runner does not support Gazebo; live execution is impossible")
    return tuple(warnings)


def runner_supports_live_execution(profile: RunnerProfile | None) -> bool:
    """True iff the profile is non-empty, supports Gazebo, and rosbag2."""

    if profile is None:
        return False
    if not validate_runner_profile(profile) == ():
        return False
    return profile.supports_gazebo and profile.supports_rosbag2


def write_runner_profile(profile: RunnerProfile, path: Path) -> None:
    """Persist a runner profile as JSON."""

    Path(path).write_text(
        json.dumps(runner_profile_to_dict(profile), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_runner_profile_schema(path: Path) -> None:
    Path(path).write_text(
        json.dumps(runner_profile_schema(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def update_qualification_status(
    profile: RunnerProfile, *, status: str
) -> RunnerProfile:
    return replace(profile, qualification_status=status)


def labels_match(profile: RunnerProfile, required: Iterable[str]) -> bool:
    have = set(profile.runner_labels)
    need = set(required)
    return need.issubset(have)


__all__ = [
    "runner_profile_schema",
    "runner_profile_from_dict",
    "runner_profile_to_dict",
    "load_runner_profile",
    "validate_runner_profile",
    "runner_supports_live_execution",
    "write_runner_profile",
    "write_runner_profile_schema",
    "update_qualification_status",
    "labels_match",
]
