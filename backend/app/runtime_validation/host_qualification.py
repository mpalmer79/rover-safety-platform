"""Host qualification: validate the runtime prerequisites of a Jazzy host.

The qualifier inspects the host environment for the dependencies the
runtime stack needs:

* Ubuntu 24.04 LTS (or compatible);
* ROS 2 Jazzy with ``ros2`` CLI on PATH;
* Gazebo Harmonic with ``gz`` CLI on PATH;
* ``colcon``;
* ``ros_gz_bridge`` package (resolved via ``ros2 pkg list``);
* a few required ROS packages (``rover_safety_bridge``, etc.);
* the Python backend importability;
* the workspace structure (``rover_ws/install/`` exists;
  ``rover_ws/src/`` contains the expected packages);
* the required launch files and bridge configs.

Each check reports one of the Phase-3 status values
(``passed`` / ``failed`` / ``partial`` / ``skipped`` / ``not_executed``)
with a machine-readable reason. The module performs no I/O beyond
``os.environ`` reads and ``subprocess.run`` for resolved CLI calls. It
runs without ROS — checks that require ROS are reported as
``not_executed`` with a reason rather than failing.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

from app.verification.acceptance import AcceptanceStatus, aggregate_status


_REQUIRED_ROS_PACKAGES: tuple[str, ...] = (
    "rclpy",
    "ros_gz_bridge",
    "robot_state_publisher",
    "tf2_ros",
)

_REQUIRED_WORKSPACE_PACKAGES: tuple[str, ...] = (
    "rover_bringup",
    "rover_safety_bridge",
    "rover_sim_gazebo",
    "rover_sensor_adapters",
    "rover_observability",
    "rover_runtime_diagnostics",
    "rover_description",
    "rover_msgs",
    "rover_world_model",
    "rover_mission_runtime",
)

_REQUIRED_LAUNCH_FILES: tuple[tuple[str, str], ...] = (
    ("rover_bringup", "full_system.launch.py"),
    ("rover_bringup", "simulation.launch.py"),
    ("rover_bringup", "safety_runtime.launch.py"),
    ("rover_bringup", "observability.launch.py"),
    ("rover_safety_bridge", "safety_bridge.launch.py"),
    ("rover_sensor_adapters", "sensor_adapters.launch.py"),
    ("rover_runtime_diagnostics", "runtime_diagnostics.launch.py"),
)

_REQUIRED_BRIDGE_CONFIG: str = "rover_ws/src/rover_sim_gazebo/config/ros_gz_bridge.yaml"


@dataclass
class HostCheck:
    name: str
    status: AcceptanceStatus
    detail: str = ""
    reason: str = ""
    observed: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status.value,
            "detail": self.detail,
            "reason": self.reason,
            "observed": dict(self.observed),
        }


@dataclass
class HostQualificationResult:
    workspace_root: Path
    checks: list[HostCheck] = field(default_factory=list)
    generated_at_utc: str = ""

    @property
    def status(self) -> AcceptanceStatus:
        return aggregate_status(c.status for c in self.checks)

    def as_dict(self) -> dict:
        return {
            "workspace_root": str(self.workspace_root),
            "generated_at_utc": self.generated_at_utc,
            "status": self.status.value,
            "checks": [c.as_dict() for c in self.checks],
        }

    def status_counts(self) -> dict[str, int]:
        out = {s.value: 0 for s in AcceptanceStatus}
        for c in self.checks:
            out[c.status.value] += 1
        return out


# ---------------------------------------------------------------------------
# Public entry point.
# ---------------------------------------------------------------------------


def qualify_host(
    *,
    workspace_root: Path | str,
    runner: Optional[callable] = None,
) -> HostQualificationResult:
    """Run every host check and return the aggregate result.

    ``runner`` is an optional callable used to invoke a subprocess. It
    must accept ``(argv, timeout)`` and return ``(returncode, stdout)``.
    Tests inject a stub runner; production code uses the default
    :func:`_default_runner` based on :func:`subprocess.run`.
    """

    from datetime import datetime, timezone

    workspace_root = Path(workspace_root).resolve()
    runner = runner or _default_runner
    result = HostQualificationResult(
        workspace_root=workspace_root,
        generated_at_utc=datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
    )
    result.checks.append(_check_ubuntu_version())
    result.checks.append(_check_ros_distro(runner=runner))
    result.checks.append(_check_gazebo(runner=runner))
    result.checks.append(_check_colcon(runner=runner))
    result.checks.append(_check_ros_packages(runner=runner))
    result.checks.append(_check_python_backend_importable(workspace_root))
    result.checks.append(_check_workspace_structure(workspace_root))
    result.checks.append(_check_required_launch_files(workspace_root))
    result.checks.append(_check_required_bridge_config(workspace_root))
    return result


# ---------------------------------------------------------------------------
# Subprocess runner (overridable for tests).
# ---------------------------------------------------------------------------


def _default_runner(argv: list[str], *, timeout: float = 10.0) -> tuple[int, str]:
    if shutil.which(argv[0]) is None:
        return (127, "")
    try:
        completed = subprocess.run(
            argv,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return (completed.returncode, (completed.stdout or "") + (completed.stderr or ""))
    except Exception as exc:  # pragma: no cover - defensive
        return (255, f"subprocess error: {exc}")


# ---------------------------------------------------------------------------
# Individual checks.
# ---------------------------------------------------------------------------


def _check_ubuntu_version() -> HostCheck:
    info = parse_os_release()
    if not info:
        return HostCheck(
            name="ubuntu_version",
            status=AcceptanceStatus.NOT_EXECUTED,
            detail="/etc/os-release not readable",
            reason="cannot determine host OS",
        )
    name = info.get("NAME", "")
    version_id = info.get("VERSION_ID", "")
    pretty = info.get("PRETTY_NAME", "")
    observed = {"NAME": name, "VERSION_ID": version_id, "PRETTY_NAME": pretty}
    if "Ubuntu" not in name:
        return HostCheck(
            name="ubuntu_version",
            status=AcceptanceStatus.FAILED,
            detail=f"host is not Ubuntu (found {name!r})",
            reason="ROS 2 Jazzy targets Ubuntu 24.04 LTS",
            observed=observed,
        )
    if version_id == "24.04":
        return HostCheck(
            name="ubuntu_version",
            status=AcceptanceStatus.PASSED,
            detail=f"Ubuntu {version_id} detected",
            observed=observed,
        )
    # Other Ubuntu versions are partial: the qualifier still runs but
    # ROS 2 Jazzy is only officially supported on 24.04.
    return HostCheck(
        name="ubuntu_version",
        status=AcceptanceStatus.PARTIAL,
        detail=f"Ubuntu {version_id or 'unknown'} detected; expected 24.04",
        reason="ROS 2 Jazzy is only officially supported on Ubuntu 24.04",
        observed=observed,
    )


def parse_os_release(text: Optional[str] = None) -> dict[str, str]:
    """Parse ``/etc/os-release`` (or an injected text) into key/value dict.

    Exposed for tests so distro parsing is exercised without touching
    the host filesystem.
    """

    if text is None:
        try:
            text = Path("/etc/os-release").read_text(encoding="utf-8")
        except OSError:
            return {}
    out: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip().strip('"')
        out[key.strip()] = value
    return out


def _check_ros_distro(*, runner) -> HostCheck:
    if shutil.which("ros2") is None:
        return HostCheck(
            name="ros2_distro",
            status=AcceptanceStatus.NOT_EXECUTED,
            detail="ros2 CLI not on PATH",
            reason=(
                "source /opt/ros/jazzy/setup.bash before invoking the "
                "qualifier; CI runs without ROS and reports this check "
                "as not_executed"
            ),
        )
    distro = os.environ.get("ROS_DISTRO", "")
    rc, out = runner(["ros2", "--version"], timeout=5.0)
    version_line = out.strip().splitlines()[0] if out else ""
    observed = {
        "ROS_DISTRO": distro,
        "ros2_version": version_line,
        "returncode": rc,
    }
    if rc != 0:
        return HostCheck(
            name="ros2_distro",
            status=AcceptanceStatus.FAILED,
            detail="ros2 --version failed",
            reason=out.strip() or "non-zero exit",
            observed=observed,
        )
    if distro == "jazzy":
        return HostCheck(
            name="ros2_distro",
            status=AcceptanceStatus.PASSED,
            detail=f"ROS 2 Jazzy detected ({version_line})",
            observed=observed,
        )
    if distro:
        return HostCheck(
            name="ros2_distro",
            status=AcceptanceStatus.PARTIAL,
            detail=f"ROS_DISTRO={distro!r}; expected 'jazzy'",
            reason="qualification requires ROS 2 Jazzy",
            observed=observed,
        )
    return HostCheck(
        name="ros2_distro",
        status=AcceptanceStatus.PARTIAL,
        detail="ros2 CLI present but ROS_DISTRO unset",
        reason="source /opt/ros/jazzy/setup.bash to set ROS_DISTRO",
        observed=observed,
    )


def _check_gazebo(*, runner) -> HostCheck:
    if shutil.which("gz") is None:
        return HostCheck(
            name="gazebo_harmonic",
            status=AcceptanceStatus.NOT_EXECUTED,
            detail="`gz` CLI not on PATH",
            reason="install Gazebo Harmonic for Ubuntu 24.04 / Jazzy",
        )
    rc, out = runner(["gz", "sim", "--version"], timeout=5.0)
    version_line = out.strip().splitlines()[0] if out else ""
    observed = {"gz_version": version_line, "returncode": rc}
    if rc != 0:
        return HostCheck(
            name="gazebo_harmonic",
            status=AcceptanceStatus.FAILED,
            detail="gz sim --version failed",
            reason=out.strip() or "non-zero exit",
            observed=observed,
        )
    # Gazebo Harmonic ships as version 8.x. Anything else is partial.
    if version_line.startswith("8.") or "Gazebo Sim, version 8" in version_line:
        status = AcceptanceStatus.PASSED
        detail = f"Gazebo Harmonic detected ({version_line})"
        reason = ""
    else:
        status = AcceptanceStatus.PARTIAL
        detail = f"Gazebo CLI present, version {version_line!r}"
        reason = "qualification targets Gazebo Harmonic (8.x)"
    return HostCheck(
        name="gazebo_harmonic",
        status=status,
        detail=detail,
        reason=reason,
        observed=observed,
    )


def _check_colcon(*, runner) -> HostCheck:
    if shutil.which("colcon") is None:
        return HostCheck(
            name="colcon_available",
            status=AcceptanceStatus.NOT_EXECUTED,
            detail="`colcon` CLI not on PATH",
            reason="install python3-colcon-common-extensions for Jazzy",
        )
    rc, out = runner(["colcon", "version-check"], timeout=10.0)
    version_line = (out.strip().splitlines() or [""])[0]
    observed = {"colcon_version": version_line, "returncode": rc}
    return HostCheck(
        name="colcon_available",
        status=AcceptanceStatus.PASSED,
        detail=f"colcon present ({version_line or 'version unknown'})",
        observed=observed,
    )


def _check_ros_packages(*, runner) -> HostCheck:
    if shutil.which("ros2") is None:
        return HostCheck(
            name="required_ros_packages",
            status=AcceptanceStatus.NOT_EXECUTED,
            detail="ros2 CLI not on PATH",
            reason="source ROS to enumerate available packages",
        )
    rc, out = runner(["ros2", "pkg", "list"], timeout=10.0)
    if rc != 0:
        return HostCheck(
            name="required_ros_packages",
            status=AcceptanceStatus.FAILED,
            detail="ros2 pkg list failed",
            reason=out.strip()[:200] or "non-zero exit",
        )
    available = {line.strip() for line in out.splitlines() if line.strip()}
    missing = [p for p in _REQUIRED_ROS_PACKAGES if p not in available]
    if missing:
        return HostCheck(
            name="required_ros_packages",
            status=AcceptanceStatus.FAILED,
            detail=f"missing ROS package(s): {', '.join(missing)}",
            reason="ensure /opt/ros/jazzy is sourced and the workspace is built",
            observed={"missing": missing},
        )
    return HostCheck(
        name="required_ros_packages",
        status=AcceptanceStatus.PASSED,
        detail=f"{len(_REQUIRED_ROS_PACKAGES)} required package(s) present",
        observed={"required": list(_REQUIRED_ROS_PACKAGES)},
    )


def _check_python_backend_importable(workspace_root: Path) -> HostCheck:
    backend = workspace_root / "backend"
    if not backend.exists():
        return HostCheck(
            name="python_backend_importable",
            status=AcceptanceStatus.FAILED,
            detail=f"backend dir missing: {backend}",
            reason="repository layout drift",
        )
    # Probe importability by spawning a fresh interpreter so the test
    # is meaningful even if the parent already mutated sys.path.
    rc, out = _default_runner(
        [
            sys.executable,
            "-c",
            (
                "import sys, pathlib; "
                f"sys.path.insert(0, r'{backend}'); "
                "import app, app.verification.requirements"
            ),
        ],
        timeout=10.0,
    )
    if rc != 0:
        return HostCheck(
            name="python_backend_importable",
            status=AcceptanceStatus.FAILED,
            detail="backend Python package failed to import",
            reason=out.strip()[:200] or "import error",
        )
    return HostCheck(
        name="python_backend_importable",
        status=AcceptanceStatus.PASSED,
        detail="backend.app imports cleanly under the host interpreter",
    )


def _check_workspace_structure(workspace_root: Path) -> HostCheck:
    src = workspace_root / "rover_ws" / "src"
    if not src.exists():
        return HostCheck(
            name="workspace_structure",
            status=AcceptanceStatus.FAILED,
            detail=f"missing: {src}",
            reason="rover_ws/src not present",
        )
    missing = [p for p in _REQUIRED_WORKSPACE_PACKAGES if not (src / p).is_dir()]
    install = workspace_root / "rover_ws" / "install"
    install_present = install.exists()
    if missing:
        return HostCheck(
            name="workspace_structure",
            status=AcceptanceStatus.FAILED,
            detail=f"missing package(s): {', '.join(missing)}",
            observed={"missing": missing, "install_present": install_present},
        )
    if not install_present:
        return HostCheck(
            name="workspace_structure",
            status=AcceptanceStatus.PARTIAL,
            detail=(
                f"all {len(_REQUIRED_WORKSPACE_PACKAGES)} packages present "
                "but rover_ws/install is missing"
            ),
            reason="run `colcon build --symlink-install` before live qualification",
            observed={"install_present": False},
        )
    return HostCheck(
        name="workspace_structure",
        status=AcceptanceStatus.PASSED,
        detail=(
            f"{len(_REQUIRED_WORKSPACE_PACKAGES)} workspace packages present; "
            "install dir found"
        ),
        observed={"install_present": True},
    )


def _check_required_launch_files(workspace_root: Path) -> HostCheck:
    src = workspace_root / "rover_ws" / "src"
    missing: list[str] = []
    for package, launch_file in _REQUIRED_LAUNCH_FILES:
        if not (src / package / "launch" / launch_file).exists():
            missing.append(f"{package}/{launch_file}")
    if missing:
        return HostCheck(
            name="required_launch_files",
            status=AcceptanceStatus.FAILED,
            detail=f"missing launch file(s): {', '.join(missing)}",
            observed={"missing": missing},
        )
    return HostCheck(
        name="required_launch_files",
        status=AcceptanceStatus.PASSED,
        detail=f"{len(_REQUIRED_LAUNCH_FILES)} required launch file(s) present",
    )


def _check_required_bridge_config(workspace_root: Path) -> HostCheck:
    config = workspace_root / _REQUIRED_BRIDGE_CONFIG
    if not config.exists():
        return HostCheck(
            name="bridge_config_present",
            status=AcceptanceStatus.FAILED,
            detail=f"missing: {config}",
            reason="ros_gz_bridge configuration not in workspace",
        )
    text = config.read_text(encoding="utf-8")
    if "/cmd_vel_authorized" not in text:
        return HostCheck(
            name="bridge_config_present",
            status=AcceptanceStatus.PARTIAL,
            detail="bridge YAML does not declare /cmd_vel_authorized",
            reason="qualification expects /cmd_vel_authorized to be bridged",
        )
    return HostCheck(
        name="bridge_config_present",
        status=AcceptanceStatus.PASSED,
        detail=f"bridge YAML at {config.relative_to(workspace_root)}",
    )


# ---------------------------------------------------------------------------
# Markdown rendering.
# ---------------------------------------------------------------------------


def render_host_qualification_md(result: HostQualificationResult) -> str:
    counts = result.status_counts()
    lines: list[str] = []
    lines.append("# Host Qualification Report")
    lines.append("")
    lines.append(
        "_Generated by `rover_ws/tools/qualify_ros_host.py`. The "
        "platform is **not safety-certified**; this report demonstrates "
        "engineering verification discipline. Checks carry one of "
        "`passed`, `failed`, `partial`, `skipped`, or `not_executed`._"
    )
    lines.append("")
    lines.append(f"- **Workspace root:** `{result.workspace_root}`")
    lines.append(f"- **Generated:** {result.generated_at_utc}")
    lines.append(f"- **Overall status:** `{result.status.value}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Status | Count |")
    lines.append("|---|---|")
    for status in AcceptanceStatus:
        lines.append(f"| `{status.value}` | {counts[status.value]} |")
    lines.append("")
    lines.append("## Checks")
    lines.append("")
    lines.append("| Check | Status | Detail |")
    lines.append("|---|---|---|")
    for check in result.checks:
        lines.append(
            f"| `{check.name}` | `{check.status.value}` | {check.detail or '-'} |"
        )
        if check.reason:
            lines.append(f"|   _reason_ |   | {check.reason} |")
    lines.append("")
    return "\n".join(lines)
