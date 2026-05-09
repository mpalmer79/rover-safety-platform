"""Shared fixtures for the rover_ws static-validation test suite.

These tests exercise the workspace **without** requiring ROS 2 or
Gazebo Harmonic to be installed. They:

* validate every package's ``package.xml`` manifest,
* parse and check the rover URDF/Xacro structure,
* validate the ros_gz_bridge YAML for forbidden topic forwards,
* exercise the safety bridge core under a stubbed ``rclpy``.

End-to-end tests that require a Jazzy host live in ``tests/manual.md``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


_ROOT = Path(__file__).resolve().parents[1]
_BACKEND = _ROOT.parent / "backend"
_BRIDGE_PKG = _ROOT / "src" / "rover_safety_bridge"

# Inject the backend and the safety bridge package onto sys.path at
# conftest load time. Test modules that import ``app.*`` or
# ``rover_safety_bridge.*`` need these paths during collection, so a
# session-scoped fixture runs too late.
for path in (_BACKEND, _BRIDGE_PKG):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


@pytest.fixture(scope="session")
def workspace_root() -> Path:
    return _ROOT


@pytest.fixture(scope="session")
def src_root() -> Path:
    return _ROOT / "src"


@pytest.fixture(scope="session")
def package_dirs(src_root: Path) -> list[Path]:
    return sorted(p for p in src_root.iterdir() if p.is_dir())
