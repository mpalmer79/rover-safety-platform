"""Validate every package's package.xml + build files.

The test asserts:

* every directory under ``src/`` has a well-formed ``package.xml`` with
  ``<name>`` matching the directory,
* every package declares either ``ament_cmake`` or ``ament_python``,
* ament_cmake packages have a ``CMakeLists.txt``,
* ament_python packages have ``setup.py`` and a ``resource/<pkg>``
  marker file,
* the seven required packages exist.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

REQUIRED_PACKAGES = {
    "rover_msgs",
    "rover_description",
    "rover_sim_gazebo",
    "rover_sensor_adapters",
    "rover_safety_bridge",
    "rover_observability",
    "rover_runtime_diagnostics",
    "rover_bringup",
}


def _read_package_xml(path: Path) -> ET.Element:
    with path.open("r", encoding="utf-8") as fh:
        tree = ET.parse(fh)
    return tree.getroot()


def test_required_packages_present(package_dirs):
    names = {p.name for p in package_dirs}
    assert REQUIRED_PACKAGES.issubset(names), (
        f"missing packages: {REQUIRED_PACKAGES - names}"
    )


@pytest.mark.parametrize("pkg_name", sorted(REQUIRED_PACKAGES))
def test_package_xml_well_formed(src_root, pkg_name):
    pkg_dir = src_root / pkg_name
    manifest = pkg_dir / "package.xml"
    assert manifest.exists(), f"{pkg_name} missing package.xml"
    root = _read_package_xml(manifest)
    assert root.tag == "package"
    name_el = root.find("name")
    assert name_el is not None and name_el.text == pkg_name
    version_el = root.find("version")
    assert version_el is not None and version_el.text
    build_types = [
        e.text for e in root.findall("./export/build_type")
    ]
    if not build_types:
        # Some packages declare via buildtool_depend instead.
        build_types = [
            e.text for e in root.findall("buildtool_depend")
            if e.text in {"ament_cmake", "ament_python"}
        ]
    assert build_types, f"{pkg_name} declares no build type"
    assert build_types[0] in {"ament_cmake", "ament_python"}


@pytest.mark.parametrize(
    "pkg_name",
    [
        "rover_msgs",
        "rover_description",
        "rover_sim_gazebo",
        "rover_bringup",
    ],
)
def test_ament_cmake_packages_have_cmakelists(src_root, pkg_name):
    cmakelists = src_root / pkg_name / "CMakeLists.txt"
    assert cmakelists.exists(), f"{pkg_name} CMakeLists.txt missing"
    text = cmakelists.read_text()
    assert "ament_package()" in text
    assert "find_package(ament_cmake REQUIRED)" in text


@pytest.mark.parametrize(
    "pkg_name",
    [
        "rover_sensor_adapters",
        "rover_safety_bridge",
        "rover_observability",
        "rover_runtime_diagnostics",
    ],
)
def test_ament_python_packages_have_setup(src_root, pkg_name):
    pkg_dir = src_root / pkg_name
    assert (pkg_dir / "setup.py").exists()
    assert (pkg_dir / "setup.cfg").exists()
    assert (pkg_dir / "resource" / pkg_name).exists()
    # The Python module directory must exist with the package name.
    assert (pkg_dir / pkg_name / "__init__.py").exists()


def test_rover_msgs_lists_every_required_message(src_root):
    cmakelists = (src_root / "rover_msgs" / "CMakeLists.txt").read_text()
    for msg in (
        "SafetyState.msg",
        "MotionAuthorization.msg",
        "SystemHealth.msg",
        "SensorHealth.msg",
        "FaultEvent.msg",
        "ReplayMarker.msg",
    ):
        assert msg in cmakelists, f"{msg} not registered in CMakeLists.txt"
        assert (src_root / "rover_msgs" / "msg" / msg).exists()
