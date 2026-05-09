"""Static validation of the rover_runtime_diagnostics package.

Confirms:

* the package manifest, setup.py, resource marker, and node modules exist,
* every node's source parses with :mod:`ast`,
* the ``diagnostic_msgs/DiagnosticStatus`` payload helpers in
  ``_publish.py`` are importable and produce the expected level mapping
  (this is the only test in the suite that runs against the actual
  rover_runtime_diagnostics module code, since the nodes themselves
  import rclpy).
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def diagnostics_pkg(src_root: Path) -> Path:
    return src_root / "rover_runtime_diagnostics"


def test_package_manifest(diagnostics_pkg: Path) -> None:
    assert (diagnostics_pkg / "package.xml").exists()
    assert (diagnostics_pkg / "setup.py").exists()
    assert (diagnostics_pkg / "setup.cfg").exists()
    assert (diagnostics_pkg / "resource" / "rover_runtime_diagnostics").exists()
    assert (
        diagnostics_pkg / "rover_runtime_diagnostics" / "__init__.py"
    ).exists()


@pytest.mark.parametrize(
    "module",
    [
        "topic_freshness_node.py",
        "bridge_health_node.py",
        "tf_validator_node.py",
        "runtime_summary_node.py",
        "_publish.py",
    ],
)
def test_node_modules_parse(diagnostics_pkg: Path, module: str) -> None:
    path = diagnostics_pkg / "rover_runtime_diagnostics" / module
    assert path.exists(), f"missing {path}"
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def test_setup_py_declares_console_scripts(diagnostics_pkg: Path) -> None:
    text = (diagnostics_pkg / "setup.py").read_text()
    for name in (
        "topic_freshness_node",
        "bridge_health_node",
        "tf_validator_node",
        "runtime_summary_node",
    ):
        assert f"{name} = " in text, f"setup.py missing entry point {name}"


def test_publish_helper_severity_mapping(diagnostics_pkg: Path) -> None:
    """Import the pure-logic helper and check the severity -> level mapping.

    The helper does not import rclpy; only diagnostic_msgs payload
    shape, but it returns plain dicts.
    """

    pkg_path = diagnostics_pkg
    if str(pkg_path) not in sys.path:
        sys.path.insert(0, str(pkg_path))
    try:
        from rover_runtime_diagnostics._publish import (
            reports_to_diagnostic_status_payloads,
            severity_to_diagnostic_level,
        )
        from app.diagnostics import HealthReport, HealthSeverity
    finally:
        # Cleanup so we don't leak the import path into other tests.
        if str(pkg_path) in sys.path:
            sys.path.remove(str(pkg_path))

    assert severity_to_diagnostic_level(HealthSeverity.OK) == 0
    assert severity_to_diagnostic_level(HealthSeverity.WARN) == 1
    assert severity_to_diagnostic_level(HealthSeverity.ERROR) == 2
    assert severity_to_diagnostic_level(HealthSeverity.CRITICAL) == 2

    payloads = reports_to_diagnostic_status_payloads(
        hardware_id="rover",
        reports=[
            HealthReport(
                component="topic:/scan",
                severity=HealthSeverity.WARN,
                summary="lidar stale",
                attributes={"age_ms": 300, "required": True},
            )
        ],
    )
    assert len(payloads) == 1
    payload = payloads[0]
    assert payload["level"] == 1
    assert payload["name"] == "topic:/scan"
    assert payload["message"] == "lidar stale"
    assert payload["hardware_id"] == "rover"
    keys = {kv["key"] for kv in payload["values"]}
    assert keys == {"age_ms", "required"}


def test_topic_freshness_node_subscribes_to_runtime_topics(diagnostics_pkg: Path) -> None:
    text = (
        diagnostics_pkg / "rover_runtime_diagnostics" / "topic_freshness_node.py"
    ).read_text()
    for topic in (
        "/clock",
        "/scan",
        "/imu",
        "/odom",
        "/contact",
        "/cmd_vel_authorized",
        "/safety/state",
        "/safety/events",
    ):
        assert topic in text, f"topic_freshness_node does not reference {topic}"


def test_bridge_health_node_uses_topic_registry(diagnostics_pkg: Path) -> None:
    text = (
        diagnostics_pkg / "rover_runtime_diagnostics" / "bridge_health_node.py"
    ).read_text()
    assert "get_topic_names_and_types" in text


def test_runtime_summary_node_publishes_aggregated_topic(diagnostics_pkg: Path) -> None:
    text = (
        diagnostics_pkg / "rover_runtime_diagnostics" / "runtime_summary_node.py"
    ).read_text()
    assert "/diagnostics/runtime_summary" in text
    assert "/system/health" in text
