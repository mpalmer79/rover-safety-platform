"""Static validation of the rover URDF/Xacro tree.

The xacro processor itself requires a Jazzy install; instead, this
test parses the Xacro XML, follows ``xacro:include`` references, and
asserts the resulting graph has the documented links and joints. It
is a structural check, not a full Xacro evaluation.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest


_NS = {"xacro": "http://www.ros.org/wiki/xacro"}


def _load(path: Path) -> ET.ElementTree:
    with path.open("r", encoding="utf-8") as fh:
        return ET.parse(fh)


def _includes(tree: ET.ElementTree, base: Path) -> list[Path]:
    out: list[Path] = []
    for inc in tree.getroot().findall("xacro:include", _NS):
        ref = inc.get("filename") or ""
        # ``$(find rover_description)/urdf/x.xacro`` -> resolve relative
        # to the URDF directory.
        rel = ref.split("/urdf/", 1)[-1]
        candidate = base / rel
        if candidate.exists():
            out.append(candidate)
    return out


@pytest.fixture
def urdf_dir(src_root) -> Path:
    return src_root / "rover_description" / "urdf"


def test_urdf_root_is_robot(urdf_dir: Path) -> None:
    tree = _load(urdf_dir / "rover.urdf.xacro")
    assert tree.getroot().tag == "robot"
    assert tree.getroot().get("name") == "rover"


def test_required_links_present(urdf_dir: Path) -> None:
    tree = _load(urdf_dir / "rover.urdf.xacro")
    links = {el.get("name") for el in tree.getroot().findall("link")}
    for required in (
        "base_footprint",
        "base_link",
        "lidar_link",
        "imu_link",
        "contact_link",
    ):
        assert required in links, f"missing link {required}"


def test_required_joints_present_in_macros(urdf_dir: Path) -> None:
    """drive_wheel macro produces left_wheel_joint / right_wheel_joint."""

    text = (urdf_dir / "rover.urdf.xacro").read_text()
    assert 'prefix="left"' in text
    assert 'prefix="right"' in text
    # The macro must declare the parameterised joint name.
    assert 'name="${prefix}_wheel_joint"' in text
    # Fixed sensor joints are spelled out explicitly.
    for joint in ("lidar_joint", "imu_joint", "contact_joint", "caster_joint"):
        assert joint in text


def test_gazebo_xacro_subscribes_to_authorized_topic(urdf_dir: Path) -> None:
    """The diff_drive plugin must consume /cmd_vel_authorized only.

    Allowing it to subscribe to /cmd_vel or /cmd_vel_requested would
    bypass the safety supervisor. We strip XML comments so prose in
    the file header cannot give a false positive.
    """

    import re

    text = (urdf_dir / "rover.gazebo.xacro").read_text()
    stripped = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    assert "<topic>/cmd_vel_authorized</topic>" in stripped
    assert "<topic>/cmd_vel_requested</topic>" not in stripped
    assert "<topic>/cmd_vel</topic>" not in stripped


def test_includes_resolve(urdf_dir: Path) -> None:
    tree = _load(urdf_dir / "rover.urdf.xacro")
    includes = _includes(tree, urdf_dir)
    assert any("rover.materials.xacro" in str(p) for p in includes)
    assert any("rover.gazebo.xacro" in str(p) for p in includes)
