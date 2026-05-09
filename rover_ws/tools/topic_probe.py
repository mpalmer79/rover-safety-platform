#!/usr/bin/env python3
"""Topic probe: validate the live ROS topic graph.

For each topic in :data:`app.runtime_validation.expected_topics.EXPECTED_TOPICS`,
the probe:

* checks that the topic is advertised (live: via
  ``Node.get_topic_names_and_types``; static-only: via the bridge YAML
  + source-grep);
* checks that the message type matches (live only);
* checks that messages are arriving inside the freshness window (live
  only, per topic ``freshness_window_ms``).

Outputs ``topic-snapshot.json`` under the configured evidence run
directory plus a status payload to stdout.

Usage:
    rover_ws/tools/topic_probe.py [--static-only] [--evidence-root evidence/runtime] [--run-id <id>]
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

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
from app.runtime_validation.expected_topics import (  # noqa: E402
    EXPECTED_TOPICS,
    TopicExpectation,
)


def _bridge_yaml_topics(workspace_root: Path) -> set[str]:
    bridge = (
        workspace_root
        / "rover_ws"
        / "src"
        / "rover_sim_gazebo"
        / "config"
        / "ros_gz_bridge.yaml"
    )
    if not bridge.exists():
        return set()
    try:
        import yaml

        data = yaml.safe_load(bridge.read_text(encoding="utf-8")) or []
    except Exception:
        return set()
    out: set[str] = set()
    for entry in data:
        if isinstance(entry, dict) and isinstance(entry.get("ros_topic_name"), str):
            out.add(entry["ros_topic_name"])
    return out


def _source_declared_topics(workspace_root: Path) -> set[str]:
    """Collect topics declared as Python string literals in the workspace."""

    out: set[str] = set()
    needles = {t.name for t in EXPECTED_TOPICS}
    for root in (
        workspace_root / "rover_ws" / "src",
        workspace_root / "backend" / "app",
    ):
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            for needle in needles:
                if f'"{needle}"' in text or f"'{needle}'" in text:
                    out.add(needle)
    return out


def run_static(*, workspace_root: Path) -> dict:
    bridge_set = _bridge_yaml_topics(workspace_root)
    source_set = _source_declared_topics(workspace_root)
    advertised_static = bridge_set | source_set
    rows: list[dict] = []
    failures: list[str] = []
    for topic in EXPECTED_TOPICS:
        declared = topic.name in advertised_static
        row = {
            "topic": topic.name,
            "msg_type": topic.msg_type,
            "direction": topic.direction.value,
            "required": topic.required,
            "declared_in_workspace": declared,
            "live_advertised": False,
            "live_advertised_status": "not_executed",
            "live_advertised_reason": "live mode unavailable / disabled",
            "type_match": None,
            "type_match_status": "not_executed",
            "freshness_age_ms": None,
            "freshness_status": (
                "not_executed" if topic.freshness_window_ms > 0 else "skipped"
            ),
            "freshness_reason": (
                "live mode unavailable / disabled"
                if topic.freshness_window_ms > 0
                else "topic does not assert freshness"
            ),
        }
        if topic.required and not declared:
            failures.append(topic.name)
        rows.append(row)
    return {
        "rows": rows,
        "advertised_in_bridge_yaml": sorted(bridge_set),
        "advertised_in_source": sorted(source_set),
        "static_failures": failures,
    }


def run_live(*, evidence_layout: EvidenceLayout, settle_seconds: float = 4.0) -> dict:  # pragma: no cover - requires rclpy
    """Live-mode probe.

    Subscribes to every required topic for ``settle_seconds`` and
    records last-seen timestamps. The implementation is deliberately
    narrow: anything more sophisticated belongs in a dedicated probe
    (see ``command_path_probe.py``).
    """

    import time
    import rclpy
    from rclpy.node import Node
    from rclpy.qos import QoSDurabilityPolicy, QoSProfile, QoSReliabilityPolicy

    rclpy.init()
    node = Node("rover_topic_probe")
    advertised: dict[str, list[str]] = {}
    last_seen: dict[str, float] = {}

    def _refresh_advertised() -> None:
        for name, types in node.get_topic_names_and_types():
            advertised[name] = list(types)

    qos = QoSProfile(
        depth=10,
        reliability=QoSReliabilityPolicy.RELIABLE,
        durability=QoSDurabilityPolicy.VOLATILE,
    )
    subscriptions = []
    for topic in EXPECTED_TOPICS:
        try:
            module_name, _, type_name = topic.msg_type.replace("/msg/", "/").partition("/")
            pkg = module_name.split("/")[0]
            klass = type_name or module_name.rsplit("/", 1)[-1]
            module = __import__(f"{pkg}.msg", fromlist=[klass])
            ros_type = getattr(module, klass)
        except Exception as exc:
            node.get_logger().warn(f"cannot resolve type {topic.msg_type}: {exc}")
            continue
        subscriptions.append(
            node.create_subscription(
                ros_type,
                topic.name,
                lambda _msg, name=topic.name: last_seen.__setitem__(name, time.time()),
                qos,
            )
        )

    deadline = time.time() + settle_seconds
    while time.time() < deadline:
        rclpy.spin_once(node, timeout_sec=0.1)
        _refresh_advertised()
    end_time = time.time()

    rows: list[dict] = []
    for topic in EXPECTED_TOPICS:
        types = advertised.get(topic.name, [])
        is_advertised = bool(types)
        type_match = topic.msg_type in types if is_advertised else False
        age_ms: int | None = None
        if topic.name in last_seen:
            age_ms = max(0, int((end_time - last_seen[topic.name]) * 1000))
        rows.append(
            {
                "topic": topic.name,
                "msg_type": topic.msg_type,
                "direction": topic.direction.value,
                "required": topic.required,
                "declared_in_workspace": True,  # live mode trusts the live graph
                "live_advertised": is_advertised,
                "live_advertised_status": "passed" if is_advertised else "failed",
                "live_advertised_reason": "" if is_advertised else "topic not advertised",
                "type_match": type_match,
                "type_match_status": "passed" if type_match else "failed",
                "freshness_age_ms": age_ms,
                "freshness_status": _freshness_status(topic, age_ms),
                "freshness_reason": "" if age_ms is not None else "no message observed",
            }
        )

    node.destroy_node()
    rclpy.shutdown()
    return {
        "rows": rows,
        "advertised_topics": sorted(advertised.keys()),
        "settle_seconds": settle_seconds,
    }


def _freshness_status(topic: TopicExpectation, age_ms: int | None) -> str:
    if topic.freshness_window_ms <= 0:
        return "skipped"
    if age_ms is None:
        return "failed"
    return "passed" if age_ms <= topic.freshness_window_ms else "failed"


def _aggregate_status(payload: dict, *, mode: str) -> tuple[str, str]:
    rows = payload.get("rows", [])
    if mode == "live":
        for row in rows:
            if row.get("required") and row.get("live_advertised_status") != "passed":
                return ("failed", f"required topic {row['topic']} not advertised")
            if row.get("required") and row.get("type_match_status") not in ("passed", "skipped"):
                return ("failed", f"required topic {row['topic']} type mismatch")
            if (
                row.get("required")
                and row.get("freshness_status") not in ("passed", "skipped")
            ):
                return ("failed", f"required topic {row['topic']} stale")
        return ("passed", f"all {sum(1 for r in rows if r.get('required'))} required topics live")
    failures = payload.get("static_failures", [])
    if failures:
        return ("failed", f"{len(failures)} required topic(s) not declared")
    # Live-only checks always not_executed in static mode.
    return ("not_executed", "live topic graph not exercised; ran static-only mode")


def main(argv: list[str] | None = None) -> int:
    parser = common_argparser(description=__doc__)
    args = parser.parse_args(argv)

    available, why = detect_rclpy()
    use_live = available and not args.static_only
    mode = "live" if use_live else "static-only"

    run_id = args.run_id or new_runtime_run_id(prefix="topic-probe")
    layout = EvidenceLayout(root=args.evidence_root, run_id=run_id).ensure()

    static_payload = run_static(workspace_root=args.workspace_root)
    payload = {
        "run_id": run_id,
        "mode": mode,
        "generated_at_utc": datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
        "static": static_payload,
    }
    if use_live:  # pragma: no cover - requires rclpy
        payload["live"] = run_live(evidence_layout=layout)
        status, detail = _aggregate_status(payload["live"], mode="live")
        reason = ""
    else:
        status, detail = _aggregate_status(static_payload, mode="static-only")
        reason = why or "static-only mode requested"

    snapshot_path = layout.path("topic-snapshot.json")
    write_json(snapshot_path, payload)
    outcome = ProbeOutcome(
        name="topic_probe",
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
