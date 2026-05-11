"""Phase 15B CLI tests (rover_ws side).

The platform is **not safety-certified**. These tests exercise the
CLI surface of the LLM-provider tools without requiring a real
model, ROS, Gazebo, or network access.
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
_AUDITS_DIR = _REPO_ROOT / "skill-llm-candidates" / "audits"
_CONFIG_DIR = _REPO_ROOT / "skill-llm-candidates" / "config"

for p in (_TOOLS_DIR, _BACKEND_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


def _load_cli(name: str):
    path = _TOOLS_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_cli_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


# --- propose_robotics_skill_with_local_llm --------------------------


def test_disabled_provider_emits_not_configured(tmp_path: Path):
    cli = _load_cli("propose_robotics_skill_with_local_llm")
    out = tmp_path / "disabled_run"
    code = cli.main(
        [
            "--text",
            "Move forward 6 feet",
            "--output",
            str(out),
            "--request-id",
            "disabled_run",
            "--generated-at",
            "2026-05-13T00:00:00+00:00",
            "--json",
        ]
    )
    assert code == 1  # disabled means not accepted
    provider = json.loads(
        (out / "provider-result.json").read_text(encoding="utf-8")
    )
    assert provider["status"] == "not_configured"
    assert provider["provider_mode"] == "disabled"


def test_fixture_provider_generates_accepted_bundle(tmp_path: Path):
    cli = _load_cli("propose_robotics_skill_with_local_llm")
    out = tmp_path / "fixture_run"
    code = cli.main(
        [
            "--text",
            "Move my robot 6 feet forward",
            "--provider",
            "fixture",
            "--fixture-id",
            "fixture_valid_move_forward_6_feet",
            "--output",
            str(out),
            "--request-id",
            "fixture_run",
            "--generated-at",
            "2026-05-13T00:00:00+00:00",
            "--json",
        ]
    )
    assert code == 0
    for name in (
        "request.json",
        "provider-result.json",
        "sanitizer-result.json",
        "validator-result.json",
        "candidate.json",
        "safety-review.json",
        "code-card.json",
        "llm-candidate-report.md",
    ):
        assert (out / name).is_file(), f"missing {out / name}"
    audit = json.loads((out / "validator-result.json").read_text(encoding="utf-8"))
    assert audit["accepted"] is True


def test_local_http_without_allow_flag_returns_not_configured(tmp_path: Path):
    cli = _load_cli("propose_robotics_skill_with_local_llm")
    out = tmp_path / "local_http_run"
    code = cli.main(
        [
            "--text",
            "Move forward 6 feet",
            "--provider",
            "local_http",
            "--config",
            str(_CONFIG_DIR / "provider.local_http.example.json"),
            "--output",
            str(out),
            "--request-id",
            "local_http_run",
            "--generated-at",
            "2026-05-13T00:00:00+00:00",
        ]
    )
    assert code == 1
    provider = json.loads(
        (out / "provider-result.json").read_text(encoding="utf-8")
    )
    assert provider["status"] in {"requires_opt_in", "not_configured"}


def test_cloud_endpoint_is_rejected_by_cli(tmp_path: Path):
    cli = _load_cli("propose_robotics_skill_with_local_llm")
    out = tmp_path / "cloud_run"
    cfg_path = tmp_path / "cloud.json"
    cfg_path.write_text(
        json.dumps(
            {
                "mode": "local_http",
                "enabled": True,
                "provider_name": "test",
                "model_name": "x",
                "endpoint": "https://api.openai.com/v1/proposals",
                "extra": {},
                "notes": [],
            }
        ),
        encoding="utf-8",
    )
    code = cli.main(
        [
            "--text",
            "Move forward",
            "--provider",
            "local_http",
            "--config",
            str(cfg_path),
            "--output",
            str(out),
            "--request-id",
            "cloud_run",
            "--generated-at",
            "2026-05-13T00:00:00+00:00",
            "--allow-local-provider",
        ]
    )
    assert code == 1
    provider = json.loads(
        (out / "provider-result.json").read_text(encoding="utf-8")
    )
    assert provider["status"] == "rejected_endpoint"


def test_sanitizer_rejection_via_fixture(tmp_path: Path):
    cli = _load_cli("propose_robotics_skill_with_local_llm")
    out = tmp_path / "sanitizer_reject"
    code = cli.main(
        [
            "--text",
            "Publish to cmd_vel directly",
            "--provider",
            "fixture",
            "--fixture-id",
            "fixture_direct_cmd_vel",
            "--output",
            str(out),
            "--request-id",
            "sanitizer_reject",
            "--generated-at",
            "2026-05-13T00:00:00+00:00",
        ]
    )
    assert code == 1
    sanitizer = json.loads((out / "sanitizer-result.json").read_text(encoding="utf-8"))
    assert sanitizer["accepted"] is False
    assert "direct_actuator_command" in sanitizer["reason_codes"]
    # No code card on a sanitizer rejection.
    assert not (out / "code-card.json").exists()


# --- validate_skill_llm_candidate ----------------------------------


def test_validate_accepts_committed_valid_candidate(tmp_path: Path):
    cli = _load_cli("validate_skill_llm_candidate")
    candidate_path = _AUDITS_DIR / "fixture_valid_move_forward_6_feet" / "candidate.json"
    assert candidate_path.is_file()
    code = cli.main(["--candidate", str(candidate_path), "--json"])
    assert code == 0


def test_validate_rejects_committed_sanitizer_rejected_candidate():
    cli = _load_cli("validate_skill_llm_candidate")
    candidate_path = _AUDITS_DIR / "fixture_direct_cmd_vel" / "candidate.json"
    assert candidate_path.is_file()
    code = cli.main(["--candidate", str(candidate_path), "--json"])
    assert code != 0


def test_validate_handles_missing_file(tmp_path: Path):
    cli = _load_cli("validate_skill_llm_candidate")
    code = cli.main(["--candidate", str(tmp_path / "missing.json")])
    assert code == 2


# --- generate_skill_llm_examples -----------------------------------


def test_generate_examples_is_idempotent_for_fixed_timestamp(tmp_path: Path):
    cli = _load_cli("generate_skill_llm_examples")

    def args(root: Path) -> list[str]:
        return [
            "--examples-dir",
            str(root / "examples"),
            "--audits-dir",
            str(root / "audits"),
            "--generated-at",
            "2026-05-13T00:00:00+00:00",
        ]

    a = tmp_path / "a"
    b = tmp_path / "b"
    assert cli.main(args(a)) == 0
    assert cli.main(args(b)) == 0

    for name in (
        "fixture_valid_move_forward_6_feet",
        "fixture_direct_cmd_vel",
        "fixture_missing_timeout",
    ):
        for f in (
            "provider-result.json",
            "sanitizer-result.json",
            "validator-result.json",
        ):
            text_a = (a / "audits" / name / f).read_text(encoding="utf-8")
            text_b = (b / "audits" / name / f).read_text(encoding="utf-8")
            assert text_a == text_b, f"{name}/{f} differs across runs"


def test_generate_examples_covers_thirteen_fixtures(tmp_path: Path):
    cli = _load_cli("generate_skill_llm_examples")
    code = cli.main(
        [
            "--examples-dir",
            str(tmp_path / "examples"),
            "--audits-dir",
            str(tmp_path / "audits"),
            "--generated-at",
            "2026-05-13T00:00:00+00:00",
            "--json",
        ]
    )
    assert code == 0
    audits = sorted(p.name for p in (tmp_path / "audits").iterdir())
    assert len(audits) == 13
