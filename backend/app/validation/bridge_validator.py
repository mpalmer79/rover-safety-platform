"""Validate the ros_gz_bridge YAML.

Performs a yaml-only audit of the bridge configuration. Does not
require ROS to be installed. The validator enforces the architectural
rules from ``docs/SAFETY_MODEL.md`` and ADR-004:

* the bridge must forward at least the documented set of topics,
* exactly one motion topic is bridged ROS_TO_GZ, and it must be
  ``/cmd_vel_authorized``,
* generic ``/cmd_vel`` and ``/cmd_vel_requested`` are NEVER bridged in
  either direction,
* clock is bridged GZ_TO_ROS only,
* every entry declares ``ros_type_name``, ``gz_type_name``, and a
  recognised ``direction`` value.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


REQUIRED_TOPICS: frozenset[str] = frozenset(
    {
        "/clock",
        "/cmd_vel_authorized",
        "/odom",
        "/scan",
        "/imu",
        "/contact",
        "/joint_states",
        "/tf",
    }
)
ALLOWED_DIRECTIONS: frozenset[str] = frozenset(
    {"GZ_TO_ROS", "ROS_TO_GZ", "BIDIRECTIONAL"}
)
FORBIDDEN_BRIDGED_TOPICS: frozenset[str] = frozenset(
    {"/cmd_vel", "/cmd_vel_requested"}
)


@dataclass
class BridgeValidationResult:
    source: str
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    bridged_topics: list[str] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        self.errors.append(message)
        self.ok = False

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "ok": self.ok,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "bridged_topics": list(self.bridged_topics),
        }


def validate_bridge_yaml(path: Path | str) -> BridgeValidationResult:
    path = Path(path)
    result = BridgeValidationResult(source=str(path))
    if not path.exists():
        result.add_error(f"bridge YAML does not exist: {path}")
        return result
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        result.add_error(f"bridge YAML did not parse: {exc}")
        return result
    if not isinstance(data, list):
        result.add_error("bridge YAML must be a list of entries")
        return result

    motion_entries: list[dict[str, Any]] = []
    for index, entry in enumerate(data, start=1):
        if not isinstance(entry, dict):
            result.add_error(f"entry {index}: not a mapping")
            continue
        for key in ("ros_topic_name", "gz_topic_name", "ros_type_name", "gz_type_name", "direction"):
            if key not in entry:
                result.add_error(f"entry {index}: missing field {key!r}")
        topic = entry.get("ros_topic_name")
        if isinstance(topic, str):
            result.bridged_topics.append(topic)
        if topic in FORBIDDEN_BRIDGED_TOPICS:
            result.add_error(
                f"entry {index}: topic {topic!r} must not be bridged "
                "(supervisor would be bypassable)"
            )
        direction = entry.get("direction")
        if direction not in ALLOWED_DIRECTIONS:
            result.add_error(f"entry {index}: unknown direction {direction!r}")
        ros_type = entry.get("ros_type_name", "")
        if isinstance(ros_type, str) and "Twist" in ros_type:
            motion_entries.append(entry)

    bridged = set(result.bridged_topics)
    missing = REQUIRED_TOPICS - bridged
    for missing_topic in sorted(missing):
        result.add_error(f"required topic not bridged: {missing_topic}")

    if len(motion_entries) != 1:
        result.add_error(
            f"expected exactly one bridged motion (Twist) topic; got {len(motion_entries)}"
        )
    elif motion_entries[0].get("ros_topic_name") != "/cmd_vel_authorized":
        result.add_error(
            "the only bridged motion topic must be /cmd_vel_authorized; got "
            f"{motion_entries[0].get('ros_topic_name')!r}"
        )
    elif motion_entries[0].get("direction") != "ROS_TO_GZ":
        result.add_error(
            "/cmd_vel_authorized must be bridged ROS_TO_GZ"
        )

    clock_entries = [e for e in data if isinstance(e, dict) and e.get("ros_topic_name") == "/clock"]
    if len(clock_entries) == 1:
        if clock_entries[0].get("direction") != "GZ_TO_ROS":
            result.add_error("/clock must be bridged GZ_TO_ROS")
    elif len(clock_entries) > 1:
        result.add_error("multiple /clock bridge entries declared")

    return result
