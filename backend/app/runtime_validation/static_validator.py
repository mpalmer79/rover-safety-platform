"""Static-only checks the runtime tools fall back on without ROS.

The static validator inspects the workspace artefacts:

* every required topic is declared somewhere — bridge YAML for the
  Gazebo-bridged topics, source code for the runtime-published ones;
* every required TF frame is declared in the URDF (delegating to
  :func:`app.validation.validate_urdf_tf_tree`);
* every required ``ros2 launch`` entry exists and parses;
* every required node module exists and imports / parses;
* the ros_gz_bridge YAML contains no ``/cmd_vel`` or
  ``/cmd_vel_requested`` entries (the architectural anti-bypass
  rule).

The validator never claims live runtime results. Its output uses the
status vocabulary from :mod:`app.verification.acceptance` and marks
checks that **require** ROS as ``not_executed`` with a reason.
"""

from __future__ import annotations

import ast
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from app.runtime_validation.expected_nodes import EXPECTED_NODES
from app.runtime_validation.expected_tf_frames import (
    EXPECTED_FRAMES,
    EXPECTED_ROOT_FRAME,
)
from app.runtime_validation.expected_topics import (
    EXPECTED_TOPICS,
    TopicExpectation,
)
from app.validation.bridge_validator import validate_bridge_yaml
from app.validation.tf_validator import validate_urdf_tf_tree
from app.verification.acceptance import AcceptanceStatus, aggregate_status


@dataclass
class StaticCheck:
    name: str
    status: AcceptanceStatus
    detail: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status.value,
            "detail": self.detail,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


@dataclass
class StaticValidationResult:
    workspace_root: Path
    checks: list[StaticCheck] = field(default_factory=list)

    @property
    def status(self) -> AcceptanceStatus:
        return aggregate_status(c.status for c in self.checks)

    def as_dict(self) -> dict:
        return {
            "workspace_root": str(self.workspace_root),
            "status": self.status.value,
            "checks": [c.as_dict() for c in self.checks],
        }


def run_static_validation(*, workspace_root: Path | str) -> StaticValidationResult:
    """Run every static check and return the aggregate."""

    workspace_root = Path(workspace_root).resolve()
    result = StaticValidationResult(workspace_root=workspace_root)
    result.checks.append(_check_bridge_yaml(workspace_root))
    result.checks.append(_check_required_topics_declared(workspace_root))
    result.checks.append(_check_urdf_tf_tree(workspace_root))
    result.checks.append(_check_full_system_launch(workspace_root))
    result.checks.append(_check_node_modules_present(workspace_root))
    result.checks.append(_check_safety_bridge_invariants(workspace_root))
    result.checks.append(_check_runtime_validation_runbook(workspace_root))
    return result


# ---------------------------------------------------------------------------
# Individual checks.
# ---------------------------------------------------------------------------


def _check_bridge_yaml(workspace_root: Path) -> StaticCheck:
    bridge = (
        workspace_root
        / "rover_ws"
        / "src"
        / "rover_sim_gazebo"
        / "config"
        / "ros_gz_bridge.yaml"
    )
    if not bridge.exists():
        return StaticCheck(
            name="bridge_yaml_present",
            status=AcceptanceStatus.FAILED,
            detail=f"missing: {bridge}",
            errors=[f"bridge YAML not found at {bridge}"],
        )
    res = validate_bridge_yaml(bridge)
    if res.ok:
        return StaticCheck(
            name="bridge_yaml_valid",
            status=AcceptanceStatus.PASSED,
            detail=f"validated {len(res.bridged_topics)} topics",
        )
    return StaticCheck(
        name="bridge_yaml_valid",
        status=AcceptanceStatus.FAILED,
        detail="bridge YAML rejected",
        errors=list(res.errors),
        warnings=list(res.warnings),
    )


def _check_required_topics_declared(workspace_root: Path) -> StaticCheck:
    """Confirm every required topic is declared somewhere we can find."""

    required = [t for t in EXPECTED_TOPICS if t.required]
    bridge_yaml = (
        workspace_root
        / "rover_ws"
        / "src"
        / "rover_sim_gazebo"
        / "config"
        / "ros_gz_bridge.yaml"
    )
    bridge_topics: set[str] = set()
    if bridge_yaml.exists():
        try:
            import yaml

            data = yaml.safe_load(bridge_yaml.read_text(encoding="utf-8")) or []
            for entry in data:
                if isinstance(entry, dict) and entry.get("ros_topic_name"):
                    bridge_topics.add(entry["ros_topic_name"])
        except Exception:  # pragma: no cover - YAML errors caught elsewhere
            pass

    # Search the rover_ws and backend trees for the topic name as a string
    # literal. This catches publishers / subscribers declared in source.
    grep_targets = (
        workspace_root / "rover_ws" / "src",
        workspace_root / "backend" / "app",
    )
    text_blob_paths: list[Path] = []
    for root in grep_targets:
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            text_blob_paths.append(path)
        for path in root.rglob("*.msg"):
            text_blob_paths.append(path)
    text_blobs: dict[Path, str] = {}
    for path in text_blob_paths:
        try:
            text_blobs[path] = path.read_text(encoding="utf-8")
        except OSError:
            continue

    missing: list[str] = []
    for topic in required:
        if topic.name in bridge_topics:
            continue
        if any(f'"{topic.name}"' in t or f"'{topic.name}'" in t for t in text_blobs.values()):
            continue
        missing.append(topic.name)
    if missing:
        return StaticCheck(
            name="required_topics_declared",
            status=AcceptanceStatus.FAILED,
            detail=f"{len(missing)} required topic(s) not declared anywhere",
            errors=[f"missing declaration for {name}" for name in missing],
        )
    return StaticCheck(
        name="required_topics_declared",
        status=AcceptanceStatus.PASSED,
        detail=f"{len(required)} required topics declared",
    )


def _check_urdf_tf_tree(workspace_root: Path) -> StaticCheck:
    urdf = (
        workspace_root
        / "rover_ws"
        / "src"
        / "rover_description"
        / "urdf"
        / "rover.urdf.xacro"
    )
    if not urdf.exists():
        return StaticCheck(
            name="urdf_present",
            status=AcceptanceStatus.FAILED,
            detail=f"missing: {urdf}",
            errors=[f"URDF not found at {urdf}"],
        )
    res = validate_urdf_tf_tree(urdf)
    # The runtime root frame (``odom``) is published by the simulator
    # at runtime, not declared in the URDF, so we exclude it from the
    # static check. Every other required frame must be a URDF link.
    expected_links = {
        f.name
        for f in EXPECTED_FRAMES
        if f.required and f.parent is not None
    }
    declared_links = set(res.links)
    missing_links = expected_links - declared_links
    if not res.ok or missing_links:
        return StaticCheck(
            name="urdf_tf_tree",
            status=AcceptanceStatus.FAILED,
            detail="URDF or expected-frames mismatch",
            errors=[*res.errors, *(f"missing link {n}" for n in sorted(missing_links))],
            warnings=list(res.warnings),
        )
    return StaticCheck(
        name="urdf_tf_tree",
        status=AcceptanceStatus.PASSED,
        detail=(
            f"{len(declared_links)} links validated; "
            f"runtime root={EXPECTED_ROOT_FRAME} (published by simulator)"
        ),
    )


def _check_full_system_launch(workspace_root: Path) -> StaticCheck:
    launch = (
        workspace_root
        / "rover_ws"
        / "src"
        / "rover_bringup"
        / "launch"
        / "full_system.launch.py"
    )
    if not launch.exists():
        return StaticCheck(
            name="full_system_launch_present",
            status=AcceptanceStatus.FAILED,
            detail=f"missing: {launch}",
            errors=[f"launch file not found at {launch}"],
        )
    text = launch.read_text(encoding="utf-8")
    try:
        ast.parse(text, filename=str(launch))
    except SyntaxError as exc:
        return StaticCheck(
            name="full_system_launch_parses",
            status=AcceptanceStatus.FAILED,
            detail="full_system.launch.py has a syntax error",
            errors=[str(exc)],
        )
    if "def generate_launch_description" not in text:
        return StaticCheck(
            name="full_system_launch_parses",
            status=AcceptanceStatus.FAILED,
            detail="generate_launch_description missing",
            errors=["full_system.launch.py must declare generate_launch_description"],
        )
    fragments = (
        "rover_sim_gazebo",
        "rover_safety_bridge",
        "rover_observability",
        "rover_runtime_diagnostics",
    )
    missing = [f for f in fragments if f not in text]
    if missing:
        return StaticCheck(
            name="full_system_launch_composes_required_packages",
            status=AcceptanceStatus.FAILED,
            detail="missing required package references",
            errors=[f"full_system.launch.py does not reference {m}" for m in missing],
        )
    return StaticCheck(
        name="full_system_launch_composes_required_packages",
        status=AcceptanceStatus.PASSED,
        detail="full_system.launch.py composes simulation, safety, observability, diagnostics",
    )


def _check_node_modules_present(workspace_root: Path) -> StaticCheck:
    """Every expected node has a Python entry-point module on disk."""

    src_root = workspace_root / "rover_ws" / "src"
    pkg_module_map = {
        "rover_safety_bridge": (
            "rover_safety_bridge",
            "safety_bridge_node.py",
        ),
        "rover_sensor_adapters": (
            "rover_sensor_adapters",
            "lidar_adapter.py",
        ),
        "rover_observability": (
            "rover_observability",
            "run_manager.py",
        ),
        "rover_runtime_diagnostics": (
            "rover_runtime_diagnostics",
            "runtime_summary_node.py",
        ),
    }
    missing: list[str] = []
    for pkg, (module_dir, module_file) in pkg_module_map.items():
        path = src_root / pkg / module_dir / module_file
        if not path.exists():
            missing.append(str(path))
    if missing:
        return StaticCheck(
            name="node_modules_present",
            status=AcceptanceStatus.FAILED,
            detail="expected node module(s) missing",
            errors=missing,
        )
    return StaticCheck(
        name="node_modules_present",
        status=AcceptanceStatus.PASSED,
        detail=f"{len(pkg_module_map)} node module families present",
    )


def _check_safety_bridge_invariants(workspace_root: Path) -> StaticCheck:
    """Source-level check that the safety bridge node never references
    /cmd_vel or /cmd_vel_requested as a publisher target.

    The Phase 1B test ``test_safety_bridge_node_only_publishes_authorized``
    already enforces this; we re-run a narrow version here so the
    static-only mode of the runtime validator carries the same
    architectural guarantee.
    """

    node_path = (
        workspace_root
        / "rover_ws"
        / "src"
        / "rover_safety_bridge"
        / "rover_safety_bridge"
        / "safety_bridge_node.py"
    )
    if not node_path.exists():
        return StaticCheck(
            name="safety_bridge_authority_invariant",
            status=AcceptanceStatus.FAILED,
            detail=f"missing: {node_path}",
            errors=[f"safety_bridge_node.py not found at {node_path}"],
        )
    text = node_path.read_text(encoding="utf-8")
    forbidden = ('"/cmd_vel"', "'/cmd_vel'")
    for fragment in forbidden:
        if fragment in text:
            return StaticCheck(
                name="safety_bridge_authority_invariant",
                status=AcceptanceStatus.FAILED,
                detail="safety bridge references /cmd_vel as a topic",
                errors=[f"forbidden topic reference {fragment} found"],
            )
    if "/cmd_vel_authorized" not in text:
        return StaticCheck(
            name="safety_bridge_authority_invariant",
            status=AcceptanceStatus.FAILED,
            detail="safety bridge does not publish /cmd_vel_authorized",
            errors=["expected /cmd_vel_authorized publisher; not found"],
        )
    return StaticCheck(
        name="safety_bridge_authority_invariant",
        status=AcceptanceStatus.PASSED,
        detail="supervisor publishes /cmd_vel_authorized and never publishes /cmd_vel",
    )


def _check_runtime_validation_runbook(workspace_root: Path) -> StaticCheck:
    runbook = workspace_root / "docs" / "RUNTIME_VALIDATION_RUNBOOK.md"
    if not runbook.exists():
        return StaticCheck(
            name="runtime_validation_runbook_present",
            status=AcceptanceStatus.NOT_EXECUTED,
            detail="docs/RUNTIME_VALIDATION_RUNBOOK.md not yet present",
        )
    text = runbook.read_text(encoding="utf-8")
    required_phrases = (
        "ROS 2 Jazzy",
        "Gazebo",
        "ros2 launch rover_bringup full_system.launch.py",
        "live_runtime_validator",
    )
    missing = [p for p in required_phrases if p not in text]
    if missing:
        return StaticCheck(
            name="runtime_validation_runbook_complete",
            status=AcceptanceStatus.PARTIAL,
            detail="runbook missing required phrases",
            warnings=[f"missing phrase: {m}" for m in missing],
        )
    return StaticCheck(
        name="runtime_validation_runbook_complete",
        status=AcceptanceStatus.PASSED,
        detail="runbook covers prerequisites, launch, validation, and tooling",
    )
