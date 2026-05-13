"""Sanity tests for the SROS2 enclave configuration (#14 + #18).

The enclaves themselves are not unit-testable cleanly without a running
DDS layer, so this test asserts the XML files exist, reference the
documented identities, and grant publish access only to the topics
listed in ``rover_ws/sros2/README.md``.
"""

from __future__ import annotations

from pathlib import Path
import re

import pytest


_SROS2_DIR = Path(__file__).resolve().parents[1] / "sros2"
_ENCLAVES_DIR = _SROS2_DIR / "enclaves"


def _read(p: Path) -> str:
    assert p.exists(), f"missing enclave file: {p}"
    return p.read_text(encoding="utf-8")


def test_sros2_readme_present() -> None:
    assert (_SROS2_DIR / "README.md").exists()


@pytest.mark.parametrize(
    "identity",
    ["operator_panel", "rover_safety_bridge", "mission_runtime"],
)
def test_enclave_file_exists(identity: str) -> None:
    path = _ENCLAVES_DIR / identity / "permissions.xml"
    text = _read(path)
    assert f"CN=/{identity}" in text, f"missing CN for {identity}"
    # Default-deny posture.
    assert "<default>DENY</default>" in text


def test_operator_panel_publishes_operator_topics() -> None:
    text = _read(_ENCLAVES_DIR / "operator_panel" / "permissions.xml")
    for topic in [
        "rt/operator/activate",
        "rt/operator/estop",
        "rt/operator/recovery",
        "rt/operator/reset",
        "rt/operator/reset_armed",
    ]:
        assert topic in text, f"operator_panel missing publish topic {topic}"


def test_safety_bridge_publishes_safety_events() -> None:
    text = _read(_ENCLAVES_DIR / "rover_safety_bridge" / "permissions.xml")
    for topic in [
        "rt/safety/events",
        "rt/safety/state",
        "rt/safety/motion_authorization",
        "rt/cmd_vel_authorized",
    ]:
        assert topic in text


def test_mission_runtime_publishes_only_requested_motion() -> None:
    text = _read(_ENCLAVES_DIR / "mission_runtime" / "permissions.xml")
    # Pull the publish block and assert it contains exactly one topic.
    publish_match = re.search(r"<publish>(.*?)</publish>", text, flags=re.DOTALL)
    assert publish_match is not None
    publish_block = publish_match.group(1)
    topics = re.findall(r"<topic>([^<]+)</topic>", publish_block)
    assert topics == ["rt/cmd_vel_requested"], topics


def test_keystore_dir_is_gitignored() -> None:
    gitignore = Path(__file__).resolve().parents[2] / ".gitignore"
    assert gitignore.exists()
    text = gitignore.read_text(encoding="utf-8")
    assert "rover_ws/sros2/keystore/" in text, (
        "private SROS2 keys must be gitignored"
    )
