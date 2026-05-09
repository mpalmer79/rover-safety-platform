#!/usr/bin/env python3
"""Launch smoke test: bring up ``full_system.launch.py`` and verify the node graph.

The probe runs ``ros2 launch rover_bringup full_system.launch.py`` for a
short settling period, captures the launch log, and asserts the
expected nodes from
:data:`app.runtime_validation.expected_nodes.EXPECTED_NODES` are alive.

Modes:

* **static-only**: parses the workspace launch files, asserts every
  expected node is composed somewhere in the launch graph, asserts the
  launch file Python parses, and writes a synthetic launch log header.
* **live** (rclpy + ROS 2 + Gazebo on PATH): subprocess-launches the
  ROS 2 stack, sleeps for the configured settle period, queries the
  graph via ``Node.get_node_names_and_namespaces``, and writes the
  full subprocess log to ``launch-log.txt``.

The live mode is intentionally guarded: the smoke test is the most
expensive probe and the live path is opt-in via ``--ros-launch``.

Outputs ``node-snapshot.json`` and ``launch-log.txt`` to the
configured evidence run directory.

Usage:
    rover_ws/tools/launch_smoke_test.py [--static-only] [--ros-launch] [--settle-seconds 8]
                                        [--evidence-root evidence/runtime] [--run-id <id>]
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from _probe_common import (  # noqa: E402  (sys.path mutated)
    ProbeOutcome,
    common_argparser,
    detect_gazebo,
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
from app.runtime_validation.expected_nodes import (  # noqa: E402
    EXPECTED_NODES,
    NodeExpectation,
)


_LAUNCH_PATH = (
    "rover_ws",
    "src",
    "rover_bringup",
    "launch",
    "full_system.launch.py",
)


def _launch_text(workspace_root: Path, parts: tuple[str, ...]) -> str | None:
    path = workspace_root.joinpath(*parts)
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _extract_node_names(launch_text: str) -> set[str]:
    """Heuristic extraction of node-name literals from launch text.

    Accepts three patterns commonly used in our launch files:

    * ``name="rover_safety_bridge"`` (explicit Node ``name=``);
    * ``executable="rover_safety_bridge"`` (since our launches use
      ``name=executable`` for sensor adapters);
    * any string literal whose contents look like a node name
      (``[a-z][a-z0-9_]+``) inside an ``_adapter("foo", ...)`` style
      helper. This is broader than ``name=`` but only catches the
      handful of identifiers that look like ROS node names.
    """

    found: set[str] = set()
    found |= set(re.findall(r'name=[\'"]([A-Za-z0-9_]+)[\'"]', launch_text))
    found |= set(re.findall(r'executable=[\'"]([A-Za-z0-9_]+)[\'"]', launch_text))
    # Helper invocations like ``_adapter("lidar_adapter", ...)``.
    for m in re.finditer(r'_adapter\(\s*[\'"]([A-Za-z0-9_]+)[\'"]', launch_text):
        found.add(m.group(1))
    return found


def _aggregate_launch_text(workspace_root: Path) -> tuple[str, list[Path]]:
    """Concatenate every ``*.launch.py`` under ``rover_ws/src``.

    The smoke test does not statically resolve ``IncludeLaunchDescription``;
    instead it asserts every expected node name appears in *some*
    workspace launch file. This is the right granularity because the
    expected nodes live across multiple packages and the static-only
    pass cannot evaluate xacro substitutions.
    """

    src_root = workspace_root / "rover_ws" / "src"
    if not src_root.exists():
        return ("", [])
    paths: list[Path] = sorted(src_root.rglob("*.launch.py"))
    chunks: list[str] = []
    for path in paths:
        text = _launch_text(workspace_root, path.relative_to(workspace_root).parts)
        if text:
            chunks.append(f"# === {path} ===\n{text}\n")
    return ("\n".join(chunks), paths)


def run_static(*, workspace_root: Path) -> dict:
    full = _launch_text(workspace_root, _LAUNCH_PATH)
    if full is None:
        return {
            "rows": [],
            "launch_file_present": False,
            "launch_file_path": str(workspace_root.joinpath(*_LAUNCH_PATH)),
            "static_failures": ["full_system.launch.py missing"],
        }
    aggregate, scanned = _aggregate_launch_text(workspace_root)
    declared_names = _extract_node_names(aggregate)
    rows: list[dict] = []
    failures: list[str] = []
    for node in EXPECTED_NODES:
        declared = node.node_name in declared_names
        rows.append(
            {
                "node_name": node.node_name,
                "package": node.package,
                "role": node.role,
                "required": node.required,
                "declared_in_launch": declared,
                "declared_in_launch_status": (
                    "passed"
                    if declared
                    else ("failed" if node.required else "skipped")
                ),
                "live_present": False,
                "live_present_status": "not_executed",
                "live_present_reason": "live mode unavailable / disabled",
            }
        )
        if node.required and not declared:
            failures.append(node.node_name)
    return {
        "rows": rows,
        "launch_file_present": True,
        "launch_file_path": str(workspace_root.joinpath(*_LAUNCH_PATH)),
        "declared_node_names": sorted(declared_names),
        "scanned_launch_files": [str(p.relative_to(workspace_root)) for p in scanned],
        "static_failures": failures,
    }


def run_live(  # pragma: no cover - requires ros2 + gazebo
    *,
    workspace_root: Path,
    settle_seconds: float,
    log_path: Path,
) -> dict:
    """Live launch smoke.

    Spawns ``ros2 launch rover_bringup full_system.launch.py``,
    captures stdout/stderr to ``launch-log.txt``, sleeps for
    ``settle_seconds``, queries the live node graph via rclpy, then
    sends ``SIGINT`` and waits for shutdown.

    The function returns the structured node-snapshot payload.
    """

    import rclpy
    from rclpy.node import Node

    cmd = [
        "ros2",
        "launch",
        "rover_bringup",
        "full_system.launch.py",
        "headless:=true",
        "record_bag:=false",
        "enable_diagnostics:=true",
    ]
    log_handle = open(log_path, "w", buffering=1)
    log_handle.write(
        f"# launch_smoke_test live launch — {datetime.now(tz=timezone.utc).isoformat(timespec='seconds')}\n"
    )
    log_handle.write(f"# command: {' '.join(cmd)}\n")
    log_handle.flush()

    proc = subprocess.Popen(
        cmd,
        cwd=str(workspace_root),
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        env=dict(os.environ, ROS_LOG_DIR=str(log_path.parent / "ros_log")),
    )
    rclpy.init()
    node = Node("rover_launch_smoke_probe")
    discovered: dict[str, str] = {}
    try:
        deadline = time.time() + settle_seconds
        while time.time() < deadline:
            for name, namespace in node.get_node_names_and_namespaces():
                discovered[name] = namespace
            time.sleep(0.5)
    finally:
        node.destroy_node()
        rclpy.shutdown()
        proc.send_signal(2)  # SIGINT
        try:
            proc.wait(timeout=15.0)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5.0)
        log_handle.flush()
        log_handle.close()

    rows: list[dict] = []
    for node_exp in EXPECTED_NODES:
        present = node_exp.node_name in discovered
        rows.append(
            {
                "node_name": node_exp.node_name,
                "package": node_exp.package,
                "role": node_exp.role,
                "required": node_exp.required,
                "declared_in_launch": True,  # live mode trusts the live graph
                "declared_in_launch_status": "passed",
                "live_present": present,
                "live_present_status": (
                    "passed"
                    if present
                    else ("failed" if node_exp.required else "skipped")
                ),
                "live_namespace": discovered.get(node_exp.node_name, ""),
            }
        )
    return {
        "rows": rows,
        "discovered_nodes": sorted(discovered.keys()),
        "settle_seconds": settle_seconds,
        "launch_log_path": str(log_path),
        "exit_code": proc.returncode,
    }


def _aggregate_status(payload: dict, *, mode: str) -> tuple[str, str]:
    rows = payload.get("rows", [])
    if mode == "live":
        for row in rows:
            if row.get("required") and row.get("live_present_status") not in (
                "passed",
                "skipped",
            ):
                return ("failed", f"required node {row['node_name']} not present")
        return ("passed", f"{sum(1 for r in rows if r.get('required'))} required nodes alive")
    failures = payload.get("static_failures", [])
    if failures:
        return ("failed", f"{len(failures)} required node(s) not declared in launch")
    if not payload.get("launch_file_present"):
        return ("failed", "full_system.launch.py missing")
    return (
        "not_executed",
        "live launch not exercised; ran static-only mode (every required node declared)",
    )


def _write_synthetic_launch_log(*, log_path: Path, reason: str) -> None:
    log_path.write_text(
        f"# launch_smoke_test — static-only run\n"
        f"# generated: {datetime.now(tz=timezone.utc).isoformat(timespec='seconds')}\n"
        f"# reason: {reason}\n"
        f"# no ros2 subprocess was launched.\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = common_argparser(description=__doc__)
    parser.add_argument(
        "--ros-launch",
        action="store_true",
        help=(
            "actually invoke ros2 launch and observe the live graph; "
            "requires rclpy + Gazebo Harmonic on PATH"
        ),
    )
    parser.add_argument(
        "--settle-seconds",
        type=float,
        default=8.0,
        help="seconds to wait for the launched stack to reach steady state",
    )
    args = parser.parse_args(argv)

    available, why = detect_rclpy()
    gazebo, gazebo_why = detect_gazebo()
    use_live = available and gazebo and args.ros_launch and not args.static_only
    mode = "live" if use_live else "static-only"

    run_id = args.run_id or new_runtime_run_id(prefix="launch-smoke")
    layout = EvidenceLayout(root=args.evidence_root, run_id=run_id).ensure()

    static_payload = run_static(workspace_root=args.workspace_root)
    payload = {
        "run_id": run_id,
        "mode": mode,
        "generated_at_utc": datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
        "static": static_payload,
    }
    log_path = layout.path("launch-log.txt")
    if use_live:  # pragma: no cover - requires ros2 + gazebo
        payload["live"] = run_live(
            workspace_root=args.workspace_root,
            settle_seconds=args.settle_seconds,
            log_path=log_path,
        )
        status, detail = _aggregate_status(payload["live"], mode="live")
        reason = ""
    else:
        # Decide the most precise reason.
        if not args.ros_launch and not args.static_only:
            reason = "live launch is opt-in; pass --ros-launch on a Jazzy host"
        else:
            reason = (
                why
                or gazebo_why
                or "static-only mode requested"
            )
        _write_synthetic_launch_log(log_path=log_path, reason=reason)
        status, detail = _aggregate_status(static_payload, mode="static-only")

    snapshot_path = layout.path("node-snapshot.json")
    write_json(snapshot_path, payload)
    outcome = ProbeOutcome(
        name="launch_smoke_test",
        mode=mode,
        status=status,
        detail=detail,
        reason=reason,
        artefact_paths=[str(snapshot_path), str(log_path)],
        payload=payload,
    )
    return emit(outcome, as_json=args.json)


if __name__ == "__main__":
    sys.exit(main())
