"""Phase 15A skill authoring CLI tests (rover_ws side).

The platform is **not safety-certified**. These tests exercise the
CLI surface of the workbench tools. They never call a remote API,
never execute generated code, never spawn ROS, and never write
outside ``tmp_path``.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


_REPO_ROOT = Path(__file__).resolve().parents[2]
_TOOLS_DIR = _REPO_ROOT / "rover_ws" / "tools"
_BACKEND_DIR = _REPO_ROOT / "backend"
_SKILL_LIB = _REPO_ROOT / "skill-library"

for p in (_TOOLS_DIR, _BACKEND_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


def _load_cli(name: str):
    path = _TOOLS_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_cli_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


# --- generate_robotics_skill -----------------------------------------


def test_generate_accepted_skill_writes_full_bundle(tmp_path: Path):
    cli = _load_cli("generate_robotics_skill")
    out = tmp_path / "move_forward_6_feet"
    code = cli.main(
        [
            "--text",
            "What code do I need to move my robot 6 feet forward?",
            "--language",
            "python_ros2",
            "--output",
            str(out),
            "--request-id",
            "move_forward_6_feet",
            "--generated-at",
            "2026-05-13T00:00:00+00:00",
            "--json",
        ]
    )
    assert code == 0
    for name in (
        "request.json",
        "generated-skill.json",
        "code.py",
        "safety-review.json",
        "code-card.json",
        "diagnostics.json",
        "skill-report.md",
    ):
        assert (out / name).is_file(), f"missing {out / name}"
    skill_payload = json.loads((out / "generated-skill.json").read_text(encoding="utf-8"))
    assert skill_payload["skill_type"] == "move_forward_distance"
    code_text = (out / "code.py").read_text(encoding="utf-8")
    assert "/cmd_vel_requested" in code_text
    assert "DISTANCE_M = 1.8288" in code_text


def test_generate_rejected_request_writes_rejection_bundle(tmp_path: Path):
    cli = _load_cli("generate_robotics_skill")
    out = tmp_path / "publish_direct_cmd_vel"
    code = cli.main(
        [
            "--text",
            "Publish to /cmd_vel directly",
            "--output",
            str(out),
            "--request-id",
            "publish_direct_cmd_vel",
            "--generated-at",
            "2026-05-13T00:00:00+00:00",
            "--json",
        ]
    )
    # Non-zero because status != generated.
    assert code == 1
    for name in (
        "request.json",
        "diagnostics.json",
        "candidate.json",
        "rejection-report.md",
    ):
        assert (out / name).is_file(), f"missing {out / name}"
    assert not (out / "generated-skill.json").exists()


def test_generate_ambiguous_request_writes_rejection_bundle(tmp_path: Path):
    cli = _load_cli("generate_robotics_skill")
    out = tmp_path / "ambiguous"
    code = cli.main(
        [
            "--text",
            "Move forward",
            "--output",
            str(out),
            "--request-id",
            "ambiguous",
            "--generated-at",
            "2026-05-13T00:00:00+00:00",
        ]
    )
    assert code == 1
    diag = json.loads((out / "diagnostics.json").read_text(encoding="utf-8"))
    assert diag["status"] == "ambiguous"


# --- validate_robotics_skill -----------------------------------------


def test_validate_accepts_committed_generated_skill(tmp_path: Path):
    cli = _load_cli("validate_robotics_skill")
    skill_path = _SKILL_LIB / "audits" / "move_forward_6_feet" / "generated-skill.json"
    assert skill_path.is_file()
    code = cli.main(["--skill", str(skill_path), "--json"])
    assert code == 0


def test_validate_rejects_tampered_skill(tmp_path: Path):
    src = _SKILL_LIB / "audits" / "move_forward_6_feet" / "generated-skill.json"
    payload = json.loads(src.read_text(encoding="utf-8"))
    payload["code"] = payload["code"].replace(
        "/cmd_vel_requested", "/cmd_vel"
    )
    tampered = tmp_path / "tampered.json"
    tampered.write_text(json.dumps(payload), encoding="utf-8")
    cli = _load_cli("validate_robotics_skill")
    code = cli.main(["--skill", str(tampered), "--json"])
    assert code != 0


def test_validate_handles_missing_file(tmp_path: Path):
    cli = _load_cli("validate_robotics_skill")
    code = cli.main(["--skill", str(tmp_path / "nope.json")])
    assert code == 2


# --- generate_skill_examples ----------------------------------------


def test_generate_examples_is_idempotent_for_fixed_timestamp(tmp_path: Path):
    cli = _load_cli("generate_skill_examples")
    args = lambda root: [
        "--examples-dir",
        str(root / "examples"),
        "--audits-dir",
        str(root / "audits"),
        "--rejected-dir",
        str(root / "rejected"),
        "--generated-at",
        "2026-05-13T00:00:00+00:00",
    ]
    a = tmp_path / "a"
    b = tmp_path / "b"
    assert cli.main(args(a)) == 0
    assert cli.main(args(b)) == 0

    for name in ("move_forward_6_feet", "stop_immediately"):
        text_a = (a / "audits" / name / "generated-skill.json").read_text(encoding="utf-8")
        text_b = (b / "audits" / name / "generated-skill.json").read_text(encoding="utf-8")
        assert text_a == text_b
    for name in ("publish_direct_cmd_vel", "ignore_estop"):
        text_a = (a / "rejected" / name / "rejection-report.md").read_text(encoding="utf-8")
        text_b = (b / "rejected" / name / "rejection-report.md").read_text(encoding="utf-8")
        assert text_a == text_b


def test_generate_examples_covers_ten_accepted_and_nine_rejected(tmp_path: Path):
    cli = _load_cli("generate_skill_examples")
    code = cli.main(
        [
            "--examples-dir",
            str(tmp_path / "examples"),
            "--audits-dir",
            str(tmp_path / "audits"),
            "--rejected-dir",
            str(tmp_path / "rejected"),
            "--generated-at",
            "2026-05-13T00:00:00+00:00",
            "--json",
        ]
    )
    assert code == 0
    accepted = sorted(p.name for p in (tmp_path / "audits").iterdir())
    rejected = sorted(p.name for p in (tmp_path / "rejected").iterdir())
    assert len(accepted) == 10
    assert len(rejected) == 9


def test_generate_skill_examples_committed_audit_uses_requested_motion(tmp_path: Path):
    code_path = _SKILL_LIB / "audits" / "move_forward_6_feet" / "code.py"
    assert code_path.is_file()
    code_text = code_path.read_text(encoding="utf-8")
    assert "/cmd_vel_requested" in code_text
    non_comment = "\n".join(line.split("#", 1)[0] for line in code_text.splitlines())
    non_comment = non_comment.replace("/cmd_vel_requested", "")
    assert "/cmd_vel" not in non_comment
