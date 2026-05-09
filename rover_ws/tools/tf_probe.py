#!/usr/bin/env python3
"""TF probe: validate the live tf2 frame graph.

For each frame in :data:`app.runtime_validation.expected_tf_frames.EXPECTED_FRAMES`,
the probe:

* checks that the frame is reachable from the configured root frame
  (live: via ``tf2_ros.Buffer.lookup_transform``; static-only: via the
  URDF link/joint graph delegated to :mod:`app.validation.tf_validator`);
* checks that the parent / child relationship matches the URDF
  declaration;
* records whether each transform was published as static or dynamic
  (live only).

Outputs ``tf-snapshot.json`` and a human-readable ``tf-tree.txt`` to
the configured evidence run directory plus a status payload to stdout.

Usage:
    rover_ws/tools/tf_probe.py [--static-only] [--evidence-root evidence/runtime] [--run-id <id>]
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
from app.runtime_validation.expected_tf_frames import (  # noqa: E402
    EXPECTED_FRAMES,
    EXPECTED_ROOT_FRAME,
    FrameExpectation,
)
from app.validation.tf_validator import validate_urdf_tf_tree  # noqa: E402


def _urdf_path(workspace_root: Path) -> Path:
    return (
        workspace_root
        / "rover_ws"
        / "src"
        / "rover_description"
        / "urdf"
        / "rover.urdf.xacro"
    )


def run_static(*, workspace_root: Path) -> dict:
    urdf = _urdf_path(workspace_root)
    res = validate_urdf_tf_tree(urdf)
    declared_links = set(res.links)
    joint_parent: dict[str, str] = {child: parent for _, _, parent, child in res.joints}
    rows: list[dict] = []
    failures: list[str] = []
    for frame in EXPECTED_FRAMES:
        is_runtime_root = frame.parent is None
        if is_runtime_root:
            row = _runtime_root_static_row(frame)
        else:
            present = frame.name in declared_links
            actual_parent = joint_parent.get(frame.name)
            # When the expected parent is the runtime root, the parent
            # edge is not declared in URDF (the simulator publishes
            # odom -> base_footprint at runtime). In that case the
            # static check verifies the link exists; the parent-match
            # is skipped with a documented reason.
            parent_is_runtime_root = frame.parent == EXPECTED_ROOT_FRAME
            parent_match = (
                True
                if parent_is_runtime_root
                else actual_parent == frame.parent
            )
            if parent_is_runtime_root:
                parent_match_status = "skipped" if present else (
                    "failed" if frame.required else "skipped"
                )
                parent_match_reason = (
                    "parent edge published by simulator at runtime "
                    "(odom -> base_footprint); URDF declares the link only"
                ) if present else "link not declared in URDF"
            else:
                parent_match_status = (
                    "passed"
                    if (present and parent_match)
                    else ("failed" if frame.required else "skipped")
                )
                parent_match_reason = ""
            row = {
                "frame": frame.name,
                "parent_expected": frame.parent,
                "parent_actual": actual_parent,
                "is_static_expected": frame.is_static,
                "required": frame.required,
                "declared_in_urdf": present,
                "parent_match_status": parent_match_status,
                "parent_match_reason": parent_match_reason,
                "live_resolvable": False,
                "live_resolvable_status": "not_executed",
                "live_resolvable_reason": "live mode unavailable / disabled",
                "transform_kind": None,
                "transform_kind_status": "not_executed",
            }
            if frame.required and not present:
                failures.append(frame.name)
            elif frame.required and not parent_is_runtime_root and not parent_match:
                failures.append(frame.name)
        rows.append(row)
    return {
        "rows": rows,
        "urdf_source": str(urdf),
        "urdf_links": sorted(declared_links),
        "urdf_joints": [list(j) for j in res.joints],
        "urdf_errors": list(res.errors),
        "urdf_warnings": list(res.warnings),
        "static_failures": failures,
    }


def _runtime_root_static_row(frame: FrameExpectation) -> dict:
    return {
        "frame": frame.name,
        "parent_expected": None,
        "parent_actual": None,
        "is_static_expected": frame.is_static,
        "required": frame.required,
        "declared_in_urdf": False,
        "parent_match_status": "skipped",
        "parent_match_reason": (
            "runtime root frame is published by the simulator, not declared in URDF"
        ),
        "live_resolvable": False,
        "live_resolvable_status": "not_executed",
        "live_resolvable_reason": "live mode unavailable / disabled",
        "transform_kind": None,
        "transform_kind_status": "not_executed",
    }


def run_live(*, settle_seconds: float = 4.0) -> dict:  # pragma: no cover - requires rclpy
    """Live-mode TF probe.

    Spins a node that subscribes to ``/tf`` and ``/tf_static`` for
    ``settle_seconds``, then performs ``lookup_transform`` from the
    expected root to every required frame.
    """

    import time
    import rclpy
    from rclpy.duration import Duration
    from rclpy.node import Node
    from tf2_ros import Buffer, TransformException, TransformListener

    rclpy.init()
    node = Node("rover_tf_probe")
    buffer = Buffer()
    TransformListener(buffer, node)

    # Track which transforms arrived on /tf vs /tf_static.
    static_children: set[str] = set()
    dynamic_children: set[str] = set()

    from tf2_msgs.msg import TFMessage  # type: ignore

    def _record(msg: TFMessage, *, store: set[str]) -> None:
        for transform in msg.transforms:
            store.add(transform.child_frame_id)

    node.create_subscription(
        TFMessage,
        "/tf",
        lambda msg: _record(msg, store=dynamic_children),
        10,
    )
    node.create_subscription(
        TFMessage,
        "/tf_static",
        lambda msg: _record(msg, store=static_children),
        10,
    )

    deadline = time.time() + settle_seconds
    while time.time() < deadline:
        rclpy.spin_once(node, timeout_sec=0.1)

    rows: list[dict] = []
    advertised: set[str] = static_children | dynamic_children
    for frame in EXPECTED_FRAMES:
        if frame.parent is None:
            transform_kind = (
                "dynamic" if frame.name in dynamic_children else "absent"
            )
            rows.append(
                {
                    "frame": frame.name,
                    "parent_expected": None,
                    "is_static_expected": frame.is_static,
                    "required": frame.required,
                    "live_resolvable": True,  # root never looks itself up
                    "live_resolvable_status": "passed",
                    "transform_kind": transform_kind,
                    "transform_kind_status": (
                        "skipped"
                        if frame.is_static is False
                        else "failed"
                    ),
                }
            )
            continue

        try:
            buffer.lookup_transform(
                EXPECTED_ROOT_FRAME,
                frame.name,
                rclpy.time.Time(),
                timeout=Duration(seconds=0.5),
            )
            resolvable = True
            err = ""
        except TransformException as exc:
            resolvable = False
            err = str(exc)

        if frame.name in static_children:
            transform_kind: str | None = "static"
        elif frame.name in dynamic_children:
            transform_kind = "dynamic"
        else:
            transform_kind = "absent"

        kind_status = _kind_status(frame, transform_kind)
        rows.append(
            {
                "frame": frame.name,
                "parent_expected": frame.parent,
                "is_static_expected": frame.is_static,
                "required": frame.required,
                "live_resolvable": resolvable,
                "live_resolvable_status": (
                    "passed" if resolvable else ("failed" if frame.required else "skipped")
                ),
                "live_resolvable_reason": err,
                "transform_kind": transform_kind,
                "transform_kind_status": kind_status,
            }
        )

    node.destroy_node()
    rclpy.shutdown()
    return {
        "rows": rows,
        "advertised_frames": sorted(advertised),
        "static_frames": sorted(static_children),
        "dynamic_frames": sorted(dynamic_children),
        "settle_seconds": settle_seconds,
    }


def _kind_status(frame: FrameExpectation, transform_kind: str | None) -> str:
    """Status for the ``static-vs-dynamic`` cell."""

    if transform_kind in (None, "absent"):
        return "failed" if frame.required else "skipped"
    expected = "static" if frame.is_static else "dynamic"
    return "passed" if transform_kind == expected else "failed"


def render_tree_text(*, root: str, rows: list[dict]) -> str:
    """Render a simple ``parent -> child`` tree of the observed graph."""

    children: dict[str, list[dict]] = {}
    for row in rows:
        parent = row.get("parent_expected") or "<root>"
        children.setdefault(parent, []).append(row)

    lines: list[str] = []
    lines.append(f"# tf-tree (root: {root})")
    lines.append("")

    def _walk(parent_label: str, depth: int) -> None:
        for row in sorted(
            children.get(parent_label, []), key=lambda r: r["frame"]
        ):
            indent = "  " * depth
            kind = row.get("transform_kind") or (
                "static" if row.get("is_static_expected") else "dynamic"
            )
            status = row.get("live_resolvable_status", "not_executed")
            lines.append(
                f"{indent}- {row['frame']}  ({kind}, {status})"
            )
            _walk(row["frame"], depth + 1)

    # Print runtime root explicitly first.
    lines.append(f"- {root}  (runtime root)")
    _walk("<root>", 1)
    _walk(root, 1)
    return "\n".join(lines) + "\n"


def _aggregate_status(payload: dict, *, mode: str) -> tuple[str, str]:
    rows = payload.get("rows", [])
    if mode == "live":
        for row in rows:
            if row.get("required") and row.get("live_resolvable_status") not in (
                "passed",
                "skipped",
            ):
                return ("failed", f"required frame {row['frame']} not resolvable")
            if row.get("required") and row.get("transform_kind_status") not in (
                "passed",
                "skipped",
            ):
                return ("failed", f"required frame {row['frame']} transform kind mismatch")
        return ("passed", f"all required frames reachable from {EXPECTED_ROOT_FRAME}")
    failures = payload.get("static_failures", [])
    if failures:
        return ("failed", f"{len(failures)} required frame(s) missing in URDF")
    return (
        "not_executed",
        "live tf graph not exercised; ran static-only mode (URDF link/joint check passed)",
    )


def main(argv: list[str] | None = None) -> int:
    parser = common_argparser(description=__doc__)
    args = parser.parse_args(argv)

    available, why = detect_rclpy()
    use_live = available and not args.static_only
    mode = "live" if use_live else "static-only"

    run_id = args.run_id or new_runtime_run_id(prefix="tf-probe")
    layout = EvidenceLayout(root=args.evidence_root, run_id=run_id).ensure()

    static_payload = run_static(workspace_root=args.workspace_root)
    payload = {
        "run_id": run_id,
        "mode": mode,
        "generated_at_utc": datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
        "expected_root_frame": EXPECTED_ROOT_FRAME,
        "static": static_payload,
    }
    if use_live:  # pragma: no cover - requires rclpy
        payload["live"] = run_live()
        rows_for_tree = payload["live"]["rows"]
        status, detail = _aggregate_status(payload["live"], mode="live")
        reason = ""
    else:
        rows_for_tree = static_payload["rows"]
        status, detail = _aggregate_status(static_payload, mode="static-only")
        reason = why or "static-only mode requested"

    snapshot_path = layout.path("tf-snapshot.json")
    write_json(snapshot_path, payload)
    tree_path = layout.path("tf-tree.txt")
    tree_path.write_text(
        render_tree_text(root=EXPECTED_ROOT_FRAME, rows=rows_for_tree),
        encoding="utf-8",
    )

    outcome = ProbeOutcome(
        name="tf_probe",
        mode=mode,
        status=status,
        detail=detail,
        reason=reason,
        artefact_paths=[str(snapshot_path), str(tree_path)],
        payload=payload,
    )
    return emit(outcome, as_json=args.json)


if __name__ == "__main__":
    sys.exit(main())
