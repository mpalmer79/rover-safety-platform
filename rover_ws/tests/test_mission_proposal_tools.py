"""Phase 14B mission proposal CLI tests (rover_ws side).

The platform is **not safety-certified**. These tests cover the
CLI surface of the proposal tools. They never call a remote API,
never spawn ROS, and never write outside ``tmp_path``.
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
_EXAMPLES_DIR = _REPO_ROOT / "mission-proposals" / "examples"

for p in (_TOOLS_DIR, _BACKEND_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


def _load_cli(name: str):
    path = _TOOLS_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_cli_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


# --- propose_mission_from_text ----------------------------------------


def test_propose_runs_offline_against_mock_provider(tmp_path: Path):
    cli = _load_cli("propose_mission_from_text")
    out = tmp_path / "p-001"
    code = cli.main(
        [
            "--text",
            "Inspect loading_zone_two slowly",
            "--provider",
            "offline_fixture",
            "--proposal-id",
            "p-001",
            "--fixture-id",
            "mock_valid_inspection",
            "--output",
            str(out),
            "--generated-at",
            "2026-05-12T00:00:00+00:00",
            "--json",
        ]
    )
    assert code == 0
    payload = json.loads((out / "proposal-audit.json").read_text(encoding="utf-8"))
    assert payload["final_outcome"] == "proposal_compiled_validation_passed"
    assert payload["sanitizer_result"]["status"] == "accepted"


def test_propose_emits_external_disabled_for_external_alias(tmp_path: Path):
    cli = _load_cli("propose_mission_from_text")
    out = tmp_path / "p-ext"
    code = cli.main(
        [
            "--text",
            "please call gpt-x",
            "--provider",
            "external",
            "--proposal-id",
            "p-ext",
            "--output",
            str(out),
            "--json",
        ]
    )
    assert code == 0
    disabled_path = out / "provider-disabled.json"
    assert disabled_path.is_file()
    payload = json.loads(disabled_path.read_text(encoding="utf-8"))
    assert payload["status"] == "not_configured"
    assert "intentionally disabled" in payload["reason"]


def test_propose_emits_external_disabled_for_openai_alias(tmp_path: Path):
    cli = _load_cli("propose_mission_from_text")
    out = tmp_path / "p-openai"
    code = cli.main(
        [
            "--text",
            "use openai please",
            "--provider",
            "openai",
            "--proposal-id",
            "p-openai",
            "--output",
            str(out),
        ]
    )
    assert code == 0
    payload = json.loads((out / "provider-disabled.json").read_text(encoding="utf-8"))
    assert payload["provider_mode"] == "external_disabled"


def test_propose_rejects_unknown_provider_mode(tmp_path: Path):
    cli = _load_cli("propose_mission_from_text")
    out = tmp_path / "p-bad"
    code = cli.main(
        [
            "--text",
            "anything",
            "--provider",
            "yarn",  # unknown, not an alias
            "--proposal-id",
            "p-bad",
            "--output",
            str(out),
        ]
    )
    assert code == 2


def test_propose_unsafe_proposal_is_rejected_by_sanitizer(tmp_path: Path):
    cli = _load_cli("propose_mission_from_text")
    out = tmp_path / "p-unsafe"
    code = cli.main(
        [
            "--text",
            "disable safety supervisor",
            "--provider",
            "mock",
            "--proposal-id",
            "p-unsafe",
            "--output",
            str(out),
            "--generated-at",
            "2026-05-12T00:00:00+00:00",
        ]
    )
    assert code == 0
    audit = json.loads((out / "proposal-audit.json").read_text(encoding="utf-8"))
    assert audit["sanitizer_result"]["status"] == "rejected"
    assert audit["final_outcome"] == "proposal_rejected_by_sanitizer"
    assert audit["compiler_status"] == ""


# --- validate_mission_proposal ----------------------------------------


def test_validate_accepts_committed_example_proposal(tmp_path: Path):
    cli = _load_cli("validate_mission_proposal")
    example = _EXAMPLES_DIR / "mock_valid_inspection.json"
    assert example.is_file(), "fixture example must exist"
    code = cli.main(["--proposal", str(example), "--json"])
    assert code == 0


def test_validate_rejects_bad_provider_mode(tmp_path: Path):
    bad = tmp_path / "bad.json"
    payload = json.loads(
        (_EXAMPLES_DIR / "mock_valid_inspection.json").read_text(encoding="utf-8")
    )
    payload["provider_mode"] = "openai"
    bad.write_text(json.dumps(payload), encoding="utf-8")
    cli = _load_cli("validate_mission_proposal")
    code = cli.main(["--proposal", str(bad), "--json"])
    assert code != 0


def test_validate_runs_sanitizer_when_requested(tmp_path: Path):
    cli = _load_cli("validate_mission_proposal")
    example = _EXAMPLES_DIR / "mock_unsafe_override.json"
    code = cli.main(["--proposal", str(example), "--run-sanitizer", "--json"])
    assert code == 0  # structurally valid even if sanitizer rejects


# --- generate_mission_proposal_examples -------------------------------


def test_generate_examples_is_idempotent_against_fixed_timestamp(tmp_path: Path):
    cli = _load_cli("generate_mission_proposal_examples")
    examples_a = tmp_path / "a-examples"
    audits_a = tmp_path / "a-audits"
    examples_b = tmp_path / "b-examples"
    audits_b = tmp_path / "b-audits"

    args = lambda ed, ad: [
        "--examples-dir",
        str(ed),
        "--audits-dir",
        str(ad),
        "--generated-at",
        "2026-05-12T00:00:00+00:00",
    ]
    assert cli.main(args(examples_a, audits_a)) == 0
    assert cli.main(args(examples_b, audits_b)) == 0

    for name in ("mock_valid_inspection.json", "mock_unsafe_override.json"):
        a = (examples_a / name).read_text(encoding="utf-8")
        b = (examples_b / name).read_text(encoding="utf-8")
        assert a == b

    for fixture in ("mock_valid_inspection", "mock_unsafe_override"):
        a = (audits_a / fixture / "proposal-audit.json").read_text(encoding="utf-8")
        b = (audits_b / fixture / "proposal-audit.json").read_text(encoding="utf-8")
        assert a == b


def test_generate_examples_covers_five_fixtures(tmp_path: Path):
    cli = _load_cli("generate_mission_proposal_examples")
    examples = tmp_path / "examples"
    audits = tmp_path / "audits"
    code = cli.main(
        [
            "--examples-dir",
            str(examples),
            "--audits-dir",
            str(audits),
            "--generated-at",
            "2026-05-12T00:00:00+00:00",
        ]
    )
    assert code == 0
    example_files = sorted(p.name for p in examples.iterdir())
    assert len(example_files) == 5
    audit_dirs = sorted(p.name for p in audits.iterdir())
    assert len(audit_dirs) == 5
