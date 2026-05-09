"""Static checks on launch files.

We do not import the launch files (importing would require ``launch``
and ``launch_ros``). Instead we parse them as text and assert:

* every required launch file exists,
* each declares ``generate_launch_description``,
* the full_system launch composes the five required sub-launches,
* the safety_runtime launch never references ``simulation.launch.py``
  (it is meant to run against a stubbed sim),
* every entry-point Python file is syntactically valid.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest


_REQUIRED_LAUNCHES = {
    "rover_bringup": [
        "full_system.launch.py",
        "simulation.launch.py",
        "safety_runtime.launch.py",
        "observability.launch.py",
        "rover_spawn.launch.py",
    ],
    "rover_sim_gazebo": [
        "simulation.launch.py",
        "rover_spawn.launch.py",
    ],
    "rover_sensor_adapters": ["sensor_adapters.launch.py"],
    "rover_safety_bridge": ["safety_bridge.launch.py"],
    "rover_observability": ["observability.launch.py"],
    "rover_description": ["rover_description.launch.py"],
}


def _launch_path(src_root: Path, pkg: str, file: str) -> Path:
    return src_root / pkg / "launch" / file


@pytest.mark.parametrize(
    "pkg,launch_file",
    [
        (pkg, lf)
        for pkg, files in _REQUIRED_LAUNCHES.items()
        for lf in files
    ],
)
def test_launch_file_exists(src_root: Path, pkg: str, launch_file: str) -> None:
    path = _launch_path(src_root, pkg, launch_file)
    assert path.exists(), f"missing {path}"


@pytest.mark.parametrize(
    "pkg,launch_file",
    [
        (pkg, lf)
        for pkg, files in _REQUIRED_LAUNCHES.items()
        for lf in files
    ],
)
def test_launch_declares_generate(src_root: Path, pkg: str, launch_file: str) -> None:
    text = _launch_path(src_root, pkg, launch_file).read_text()
    assert "def generate_launch_description" in text


@pytest.mark.parametrize(
    "pkg,launch_file",
    [
        (pkg, lf)
        for pkg, files in _REQUIRED_LAUNCHES.items()
        for lf in files
    ],
)
def test_launch_is_syntactically_valid(src_root: Path, pkg: str, launch_file: str) -> None:
    path = _launch_path(src_root, pkg, launch_file)
    ast.parse(path.read_text(), filename=str(path))


def test_full_system_composes_required_launches(src_root: Path) -> None:
    text = _launch_path(src_root, "rover_bringup", "full_system.launch.py").read_text()
    for fragment in (
        "rover_sim_gazebo",
        "simulation.launch.py",
        "rover_spawn.launch.py",
        "rover_sensor_adapters",
        "sensor_adapters.launch.py",
        "rover_safety_bridge",
        "safety_bridge.launch.py",
        "rover_observability",
        "observability.launch.py",
    ):
        assert fragment in text, f"full_system.launch.py is missing {fragment}"


def test_safety_runtime_does_not_launch_simulation(src_root: Path) -> None:
    text = _launch_path(src_root, "rover_bringup", "safety_runtime.launch.py").read_text()
    assert "simulation.launch.py" not in text


def test_observability_records_required_topics(src_root: Path) -> None:
    text = _launch_path(
        src_root, "rover_observability", "observability.launch.py"
    ).read_text()
    for topic in (
        "/cmd_vel_authorized",
        "/cmd_vel_requested",
        "/safety/state",
        "/safety/events",
        "/replay/markers",
        "/scan",
        "/odom",
        "/imu",
        "/tf",
    ):
        assert topic in text, f"observability launch is not recording {topic}"
