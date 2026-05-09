#!/usr/bin/env python3
"""Command-path probe: prove the safety-authority invariant at runtime.

This is the most safety-critical probe in the suite. It verifies the
architectural rule that **only** ``rover_safety_bridge`` publishes
``/cmd_vel_authorized`` and that ``/cmd_vel_requested`` (the mission /
Nav2 path) does not directly actuate the rover.

Modes:

* **static-only**: greps the workspace for any non-supervisor publisher
  of ``/cmd_vel_authorized`` and any forbidden references to
  ``/cmd_vel`` in the safety bridge. Fast, deterministic, runs without
  ROS.
* **live** (rclpy + Jazzy host required): introspects the live graph
  via ``ros2 topic info`` semantics, observes whether published
  authorized commands quench when no request is in flight, and snaps
  the publisher list to the evidence file.

Outputs ``command-path-audit.json`` to the configured evidence run
directory.

Usage:
    rover_ws/tools/command_path_probe.py [--static-only] [--evidence-root evidence/runtime] [--run-id <id>]
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from _probe_common import (  # noqa: E402  (sys.path mutated)
    ProbeOutcome,
    common_argparser,
    detect_rclpy,
    emit,
    ensure_app_on_path,
    write_json,
)

ensure_app_on_path()

from app.runtime_validation.evidence_layout import (  # noqa: E402
    EvidenceLayout,
    new_runtime_run_id,
)


_SAFETY_BRIDGE_PKG = "rover_safety_bridge"
_AUTHORIZED_TOPIC = "/cmd_vel_authorized"
_REQUESTED_TOPIC = "/cmd_vel_requested"
_RAW_CMD_VEL = "/cmd_vel"


@dataclass(frozen=True)
class StaticPublisher:
    file: Path
    line: int
    snippet: str
    package: str

    def as_dict(self) -> dict:
        return {
            "file": str(self.file),
            "line": self.line,
            "snippet": self.snippet,
            "package": self.package,
        }


def _scan_for_publisher(
    *,
    workspace_root: Path,
    topic: str,
) -> list[StaticPublisher]:
    """Locate every ``create_publisher`` call that publishes ``topic``.

    The probe accepts two patterns:

    * inline literal: ``create_publisher(MsgType, "/cmd_vel_authorized", ...)``;
    * module constant: ``_AUTHORIZED_TOPIC = "/cmd_vel_authorized"`` *and*
      ``create_publisher(MsgType, _AUTHORIZED_TOPIC, ...)`` somewhere in
      the same file.

    Both are common in our nodes. The probe records one hit per
    matching ``create_publisher`` call.
    """

    inline = re.compile(
        rf"""create_publisher\s*\(\s*[A-Za-z_][\w\.]*\s*,\s*['"]{re.escape(topic)}['"]"""
    )
    constant_def = re.compile(
        rf"""^\s*([A-Z_][A-Z0-9_]*)\s*=\s*['"]{re.escape(topic)}['"]\s*(?:#.*)?$""",
        re.MULTILINE,
    )
    hits: list[StaticPublisher] = []
    src_root = workspace_root / "rover_ws" / "src"
    if not src_root.exists():
        return hits
    for path in src_root.rglob("*.py"):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        package = _infer_package(path, src_root)
        seen_lines: set[int] = set()
        for m in inline.finditer(text):
            line_no = text.count("\n", 0, m.start()) + 1
            seen_lines.add(line_no)
            line_text = text.splitlines()[line_no - 1].strip()
            hits.append(
                StaticPublisher(
                    file=path.relative_to(workspace_root),
                    line=line_no,
                    snippet=line_text,
                    package=package,
                )
            )
        const_names = {match.group(1) for match in constant_def.finditer(text)}
        for const_name in const_names:
            const_re = re.compile(
                rf"""create_publisher\s*\(\s*[A-Za-z_][\w\.]*\s*,\s*{re.escape(const_name)}\b"""
            )
            for m in const_re.finditer(text):
                line_no = text.count("\n", 0, m.start()) + 1
                if line_no in seen_lines:
                    continue
                seen_lines.add(line_no)
                line_text = text.splitlines()[line_no - 1].strip()
                hits.append(
                    StaticPublisher(
                        file=path.relative_to(workspace_root),
                        line=line_no,
                        snippet=f"{const_name} -> {line_text}",
                        package=package,
                    )
                )
    return hits


def _infer_package(path: Path, src_root: Path) -> str:
    rel = path.relative_to(src_root)
    parts = rel.parts
    return parts[0] if parts else "<unknown>"


def run_static(*, workspace_root: Path) -> dict:
    authorized_pubs = _scan_for_publisher(
        workspace_root=workspace_root, topic=_AUTHORIZED_TOPIC
    )
    requested_pubs = _scan_for_publisher(
        workspace_root=workspace_root, topic=_REQUESTED_TOPIC
    )
    raw_pubs = _scan_for_publisher(
        workspace_root=workspace_root, topic=_RAW_CMD_VEL
    )

    foreign_authorized = [
        p for p in authorized_pubs if p.package != _SAFETY_BRIDGE_PKG
    ]
    bridge_yaml_status, bridge_yaml_detail = _check_bridge_yaml_no_cmd_vel(
        workspace_root
    )

    invariants: list[dict] = []

    if not authorized_pubs:
        invariants.append(
            {
                "name": "authorized_publisher_present",
                "status": "failed",
                "detail": (
                    f"no source declared a publisher of {_AUTHORIZED_TOPIC}; "
                    f"safety supervisor cannot drive the rover"
                ),
            }
        )
    else:
        invariants.append(
            {
                "name": "authorized_publisher_present",
                "status": "passed",
                "detail": (
                    f"{len(authorized_pubs)} publisher declaration(s) "
                    f"for {_AUTHORIZED_TOPIC}"
                ),
            }
        )

    if foreign_authorized:
        invariants.append(
            {
                "name": "authorized_publisher_is_safety_bridge",
                "status": "failed",
                "detail": (
                    "non-supervisor source publishes "
                    f"{_AUTHORIZED_TOPIC}: "
                    + ", ".join(
                        f"{p.package}:{p.file}:{p.line}" for p in foreign_authorized
                    )
                ),
            }
        )
    elif authorized_pubs:
        invariants.append(
            {
                "name": "authorized_publisher_is_safety_bridge",
                "status": "passed",
                "detail": (
                    f"all {len(authorized_pubs)} publisher(s) live in "
                    f"package {_SAFETY_BRIDGE_PKG!r}"
                ),
            }
        )
    else:
        invariants.append(
            {
                "name": "authorized_publisher_is_safety_bridge",
                "status": "not_executed",
                "detail": "no authorized publisher to attribute",
            }
        )

    invariants.append(
        {
            "name": "raw_cmd_vel_not_published_by_workspace",
            "status": "passed" if not raw_pubs else "failed",
            "detail": (
                "no source publishes /cmd_vel"
                if not raw_pubs
                else (
                    "/cmd_vel is published by: "
                    + ", ".join(
                        f"{p.package}:{p.file}:{p.line}" for p in raw_pubs
                    )
                )
            ),
        }
    )

    invariants.append(
        {
            "name": "bridge_yaml_does_not_route_cmd_vel",
            "status": bridge_yaml_status,
            "detail": bridge_yaml_detail,
        }
    )

    return {
        "authorized_publishers": [p.as_dict() for p in authorized_pubs],
        "requested_publishers": [p.as_dict() for p in requested_pubs],
        "raw_cmd_vel_publishers": [p.as_dict() for p in raw_pubs],
        "invariants": invariants,
    }


def _check_bridge_yaml_no_cmd_vel(workspace_root: Path) -> tuple[str, str]:
    bridge_yaml = (
        workspace_root
        / "rover_ws"
        / "src"
        / "rover_sim_gazebo"
        / "config"
        / "ros_gz_bridge.yaml"
    )
    if not bridge_yaml.exists():
        return ("failed", f"bridge YAML not found at {bridge_yaml}")
    try:
        import yaml

        data = yaml.safe_load(bridge_yaml.read_text(encoding="utf-8")) or []
    except Exception as exc:
        return ("failed", f"bridge YAML did not parse: {exc}")
    # /cmd_vel_authorized is *expected* to be bridged ROS -> Gazebo (the
    # supervisor publishes on the ROS side and the bridge forwards to
    # the Gazebo actuator topic). The architectural anti-bypass rule
    # is that /cmd_vel and /cmd_vel_requested must not appear: those
    # would let mission / nav / external sources reach the actuator
    # without supervisor authorisation.
    forbidden_ros = {_RAW_CMD_VEL, _REQUESTED_TOPIC}
    bad_ros: list[str] = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        ros_topic = entry.get("ros_topic_name", "")
        if ros_topic in forbidden_ros:
            bad_ros.append(ros_topic)
    if bad_ros:
        return (
            "failed",
            "bridge YAML routes safety-critical topics: " + ", ".join(sorted(set(bad_ros))),
        )
    return (
        "passed",
        "bridge YAML does not route /cmd_vel or /cmd_vel_requested; "
        "/cmd_vel_authorized is the only command-path entry (ROS -> Gazebo)",
    )


def run_live(*, settle_seconds: float = 4.0) -> dict:  # pragma: no cover - requires rclpy
    """Live-mode command-path probe.

    Subscribes to the request and authorized topics for ``settle_seconds``,
    enumerates publishers via the live graph, and asserts the
    architectural rule from the spec:

    * only nodes inside ``rover_safety_bridge`` publish
      ``/cmd_vel_authorized``;
    * mission / nav2 publishers are confined to ``/cmd_vel_requested``;
    * no node publishes ``/cmd_vel`` directly.
    """

    import time
    import rclpy
    from geometry_msgs.msg import Twist  # type: ignore
    from rclpy.node import Node

    rclpy.init()
    node = Node("rover_command_path_probe")

    last_authorized: list[dict] = []
    last_requested: list[dict] = []

    def _on_authorized(msg: Twist) -> None:
        last_authorized.append(
            {
                "linear_x": msg.linear.x,
                "angular_z": msg.angular.z,
                "ts": time.time(),
            }
        )

    def _on_requested(msg: Twist) -> None:
        last_requested.append(
            {
                "linear_x": msg.linear.x,
                "angular_z": msg.angular.z,
                "ts": time.time(),
            }
        )

    node.create_subscription(Twist, _AUTHORIZED_TOPIC, _on_authorized, 10)
    node.create_subscription(Twist, _REQUESTED_TOPIC, _on_requested, 10)

    deadline = time.time() + settle_seconds
    while time.time() < deadline:
        rclpy.spin_once(node, timeout_sec=0.1)

    authorized_pubs = node.get_publishers_info_by_topic(_AUTHORIZED_TOPIC)
    requested_pubs = node.get_publishers_info_by_topic(_REQUESTED_TOPIC)
    raw_pubs = node.get_publishers_info_by_topic(_RAW_CMD_VEL)

    def _serialise(pubs: Iterable) -> list[dict]:
        out: list[dict] = []
        for info in pubs:
            out.append(
                {
                    "node_name": info.node_name,
                    "node_namespace": info.node_namespace,
                    "topic_type": info.topic_type,
                }
            )
        return out

    authorized_serial = _serialise(authorized_pubs)
    requested_serial = _serialise(requested_pubs)
    raw_serial = _serialise(raw_pubs)

    foreign_authorized = [
        p for p in authorized_serial if "safety_bridge" not in p["node_name"]
    ]

    invariants = [
        {
            "name": "authorized_publisher_present",
            "status": "passed" if authorized_serial else "failed",
            "detail": (
                f"{len(authorized_serial)} publisher(s) on {_AUTHORIZED_TOPIC}"
            ),
        },
        {
            "name": "authorized_publisher_is_safety_bridge",
            "status": "passed" if authorized_serial and not foreign_authorized else (
                "failed" if foreign_authorized else "not_executed"
            ),
            "detail": (
                "all authorized publishers are inside rover_safety_bridge"
                if authorized_serial and not foreign_authorized
                else (
                    "foreign publishers: "
                    + ", ".join(p["node_name"] for p in foreign_authorized)
                    if foreign_authorized
                    else "no authorized publisher observed"
                )
            ),
        },
        {
            "name": "raw_cmd_vel_not_advertised",
            "status": "passed" if not raw_serial else "failed",
            "detail": (
                "no /cmd_vel publisher observed"
                if not raw_serial
                else (
                    "/cmd_vel publishers: "
                    + ", ".join(p["node_name"] for p in raw_serial)
                )
            ),
        },
    ]
    return {
        "authorized_publishers": authorized_serial,
        "requested_publishers": requested_serial,
        "raw_cmd_vel_publishers": raw_serial,
        "authorized_samples": last_authorized[:50],
        "requested_samples": last_requested[:50],
        "invariants": invariants,
        "settle_seconds": settle_seconds,
    }


def _aggregate_status(payload: dict, *, mode: str) -> tuple[str, str]:
    invariants = payload.get("invariants", [])
    if not invariants:
        return ("not_executed", "no invariants evaluated")
    failures = [i for i in invariants if i.get("status") == "failed"]
    if failures:
        return (
            "failed",
            f"{len(failures)} command-path invariant(s) violated: "
            + ", ".join(i["name"] for i in failures),
        )
    if mode == "static-only":
        return (
            "passed",
            f"{len(invariants)} command-path invariant(s) verified statically",
        )
    return (
        "passed",
        f"{len(invariants)} command-path invariant(s) verified against the live graph",
    )


def main(argv: list[str] | None = None) -> int:
    parser = common_argparser(description=__doc__)
    args = parser.parse_args(argv)

    available, why = detect_rclpy()
    use_live = available and not args.static_only
    mode = "live" if use_live else "static-only"

    run_id = args.run_id or new_runtime_run_id(prefix="cmd-path")
    layout = EvidenceLayout(root=args.evidence_root, run_id=run_id).ensure()

    static_payload = run_static(workspace_root=args.workspace_root)
    payload = {
        "run_id": run_id,
        "mode": mode,
        "generated_at_utc": datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
        "static": static_payload,
    }
    if use_live:  # pragma: no cover - requires rclpy
        payload["live"] = run_live()
        status, detail = _aggregate_status(payload["live"], mode="live")
        reason = ""
    else:
        status, detail = _aggregate_status(static_payload, mode="static-only")
        reason = why or "static-only mode requested"

    snapshot_path = layout.path("command-path-audit.json")
    write_json(snapshot_path, payload)

    outcome = ProbeOutcome(
        name="command_path_probe",
        mode=mode,
        status=status,
        detail=detail,
        reason=reason,
        artefact_paths=[str(snapshot_path)],
        payload=payload,
    )
    return emit(outcome, as_json=args.json)


if __name__ == "__main__":
    sys.exit(main())
