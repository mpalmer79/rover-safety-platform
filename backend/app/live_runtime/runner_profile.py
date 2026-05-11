"""Self-hosted runner profile loader and validator.

A runner profile is a JSON document that describes one self-hosted
GitHub Actions runner attached to this repository. It records:

* the runner identity and labels;
* the host's OS / ROS / Gazebo / Python versions;
* the workspace path on the runner;
* the bag format the runner is configured to capture;
* the most recent qualification outcome (or ``not_executed`` when
  no run has occurred);
* known limitations.

The committed profile must be honest: an attached self-hosted runner
is the only way to legally claim qualification. The validator is the
single chokepoint that prevents a profile from claiming
``runner_status: qualified`` without a corresponding live evidence
record.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Optional


class RunnerStatus(str, Enum):
    QUALIFIED = "qualified"
    PROVISIONAL = "provisional"
    UNQUALIFIED = "unqualified"


class QualificationOutcome(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    PARTIAL = "partial"
    NOT_EXECUTED = "not_executed"


_REQUIRED_LABELS: tuple[str, ...] = ("self-hosted", "ros-jazzy", "gazebo")
_FORBIDDEN_LABELS: tuple[str, ...] = (
    "ubuntu-latest",
    "ubuntu-22.04",
    "ubuntu-24.04",
    "windows-latest",
    "macos-latest",
)
_ALLOWED_BAG_FORMATS: frozenset[str] = frozenset({"mcap", "db3"})


@dataclass(frozen=True)
class RunnerProfile:
    runner_id: str
    runner_status: RunnerStatus
    qualification_status: QualificationOutcome
    labels: tuple[str, ...]
    host_os: str
    ros_distro: str
    gazebo_version: str
    python_version: str
    workspace_path: str
    bag_format: str
    last_qualified_at: Optional[str] = None
    last_qualified_run_id: Optional[str] = None
    last_bag_backed_run_id: Optional[str] = None
    known_limitations: tuple[str, ...] = field(default_factory=tuple)
    notes: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "runner_id": self.runner_id,
            "runner_status": self.runner_status.value,
            "qualification_status": self.qualification_status.value,
            "labels": list(self.labels),
            "host_os": self.host_os,
            "ros_distro": self.ros_distro,
            "gazebo_version": self.gazebo_version,
            "python_version": self.python_version,
            "workspace_path": self.workspace_path,
            "bag_format": self.bag_format,
            "last_qualified_at": self.last_qualified_at,
            "last_qualified_run_id": self.last_qualified_run_id,
            "last_bag_backed_run_id": self.last_bag_backed_run_id,
            "known_limitations": list(self.known_limitations),
            "notes": list(self.notes),
        }


def _coerce_str_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, (list, tuple)):
        return tuple(str(v) for v in value)
    raise ValueError(f"expected list of strings, got {type(value).__name__}")


def parse_runner_profile(data: dict) -> RunnerProfile:
    """Construct a RunnerProfile from a parsed JSON document."""

    if not isinstance(data, dict):
        raise ValueError("runner profile must be a JSON object")

    try:
        runner_status = RunnerStatus(data.get("runner_status", "unqualified"))
    except ValueError as exc:
        raise ValueError(f"invalid runner_status: {exc}") from exc
    try:
        qualification_status = QualificationOutcome(
            data.get("qualification_status", "not_executed")
        )
    except ValueError as exc:
        raise ValueError(f"invalid qualification_status: {exc}") from exc

    return RunnerProfile(
        runner_id=str(data.get("runner_id", "")),
        runner_status=runner_status,
        qualification_status=qualification_status,
        labels=_coerce_str_tuple(data.get("labels")),
        host_os=str(data.get("host_os", "")),
        ros_distro=str(data.get("ros_distro", "")),
        gazebo_version=str(data.get("gazebo_version", "")),
        python_version=str(data.get("python_version", "")),
        workspace_path=str(data.get("workspace_path", "")),
        bag_format=str(data.get("bag_format", "")).lower(),
        last_qualified_at=data.get("last_qualified_at"),
        last_qualified_run_id=data.get("last_qualified_run_id"),
        last_bag_backed_run_id=data.get("last_bag_backed_run_id"),
        known_limitations=_coerce_str_tuple(data.get("known_limitations")),
        notes=_coerce_str_tuple(data.get("notes")),
    )


def load_runner_profile(path: Path) -> RunnerProfile:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return parse_runner_profile(data)


def validate_runner_profile(
    profile: RunnerProfile,
    *,
    require_qualified: bool = False,
    has_bag_backed_evidence: bool = False,
) -> list[str]:
    """Return a list of validation errors. Empty list means valid.

    ``require_qualified`` raises the bar so a CI test can assert that
    a committed profile remains honest: no profile may claim
    qualification without recorded bag-backed evidence.
    """

    errors: list[str] = []
    if not profile.runner_id:
        errors.append("runner_id is required")

    label_set = set(profile.labels)
    for required in _REQUIRED_LABELS:
        if required not in label_set:
            errors.append(f"runner labels must include '{required}'")
    for forbidden in _FORBIDDEN_LABELS:
        if forbidden in label_set:
            errors.append(
                f"runner labels must not include GitHub-hosted label '{forbidden}'"
            )

    if profile.bag_format and profile.bag_format not in _ALLOWED_BAG_FORMATS:
        errors.append(
            f"bag_format must be one of {sorted(_ALLOWED_BAG_FORMATS)}, "
            f"got '{profile.bag_format}'"
        )

    if profile.runner_status is RunnerStatus.QUALIFIED:
        if profile.qualification_status is not QualificationOutcome.PASSED:
            errors.append(
                "runner_status='qualified' requires qualification_status='passed'"
            )
        if not profile.last_qualified_at:
            errors.append(
                "runner_status='qualified' requires last_qualified_at timestamp"
            )
        if not profile.last_qualified_run_id:
            errors.append(
                "runner_status='qualified' requires last_qualified_run_id"
            )
        if not has_bag_backed_evidence and not profile.last_bag_backed_run_id:
            errors.append(
                "runner_status='qualified' requires a recorded bag-backed run id"
            )

    if profile.runner_status is RunnerStatus.PROVISIONAL:
        if profile.qualification_status not in (
            QualificationOutcome.PARTIAL,
            QualificationOutcome.PASSED,
        ):
            errors.append(
                "runner_status='provisional' requires qualification_status "
                "='partial' or 'passed'"
            )

    if profile.runner_status is RunnerStatus.UNQUALIFIED:
        if profile.qualification_status is QualificationOutcome.PASSED:
            errors.append(
                "runner_status='unqualified' cannot have qualification_status"
                "='passed'; promote runner_status or downgrade qualification_status"
            )

    for ts in (profile.last_qualified_at,):
        if ts is None:
            continue
        if not isinstance(ts, str):
            errors.append("timestamps must be ISO-8601 strings")
            continue
        try:
            datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except ValueError:
            errors.append(f"invalid ISO-8601 timestamp: {ts}")

    if require_qualified and profile.runner_status is not RunnerStatus.QUALIFIED:
        errors.append("expected runner_status='qualified'")

    return errors


def new_unqualified_template(
    *,
    runner_id: str = "self-hosted-jazzy-template",
    reason: str = "no self-hosted Jazzy/Gazebo runner attached",
) -> RunnerProfile:
    """Construct the canonical honest template profile."""

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return RunnerProfile(
        runner_id=runner_id,
        runner_status=RunnerStatus.UNQUALIFIED,
        qualification_status=QualificationOutcome.NOT_EXECUTED,
        labels=("self-hosted", "ros-jazzy", "gazebo"),
        host_os="Ubuntu 24.04 LTS",
        ros_distro="jazzy",
        gazebo_version="harmonic",
        python_version="3.12",
        workspace_path="${HOME}/rover_ws",
        bag_format="mcap",
        last_qualified_at=None,
        last_qualified_run_id=None,
        last_bag_backed_run_id=None,
        known_limitations=(
            reason,
            "live runtime evidence has not been captured on this profile",
        ),
        notes=(
            f"template generated {now}; replace runner_id with the local"
            " runner identifier before attaching to GitHub Actions",
        ),
    )
