"""Phase 16 mission rehearsal CLI tests (rover_ws side).

The platform is **not safety-certified**. Exercises the CLI
surface of the rehearsal tools without requiring ROS, network
access, or a real model.
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
_AUDITS_DIR = _REPO_ROOT / "mission-rehearsals" / "audits"
_EXAMPLES_DIR = _REPO_ROOT / "mission-rehearsals" / "examples"

for p in (_TOOLS_DIR, _BACKEND_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


def _load_cli(name: str):
    path = _TOOLS_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_cli_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


# --- run_mission_rehearsal -------------------------------------------


def test_run_rehearsal_completes_accepted_example(tmp_path: Path):
    cli = _load_cli("run_mission_rehearsal")
    mission = _EXAMPLES_DIR / "warehouse_pickup_route_alpha.json"
    out = tmp_path / "warehouse_pickup_route_alpha"
    code = cli.main(
        [
            "--mission",
            str(mission),
            "--output",
            str(out),
            "--generated-at",
            "2026-05-13T00:00:00+00:00",
            "--json",
        ]
    )
    assert code == 0
    audit = json.loads((out / "rehearsal-audit.json").read_text(encoding="utf-8"))
    assert audit["final_status"] == "completed"
    assert audit["replay"]["bag_backed"] is False


def test_run_rehearsal_rejects_unsafe_speed(tmp_path: Path):
    cli = _load_cli("run_mission_rehearsal")
    mission = _EXAMPLES_DIR / "unsafe_speed_route.json"
    out = tmp_path / "unsafe_speed_route"
    code = cli.main(
        [
            "--mission",
            str(mission),
            "--output",
            str(out),
            "--generated-at",
            "2026-05-13T00:00:00+00:00",
        ]
    )
    assert code == 1
    audit = json.loads((out / "rehearsal-audit.json").read_text(encoding="utf-8"))
    assert audit["final_status"] == "rejected"
    assert audit["final_failure_reason"] == "unsafe_speed"


def test_run_rehearsal_handles_missing_file(tmp_path: Path):
    cli = _load_cli("run_mission_rehearsal")
    code = cli.main(
        [
            "--mission",
            str(tmp_path / "missing.json"),
            "--output",
            str(tmp_path / "out"),
        ]
    )
    assert code == 2


def test_run_rehearsal_handles_invalid_json(tmp_path: Path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not valid", encoding="utf-8")
    cli = _load_cli("run_mission_rehearsal")
    code = cli.main(["--mission", str(bad), "--output", str(tmp_path / "out")])
    assert code == 2


# --- validate_mission_rehearsal --------------------------------------


def test_validate_accepts_committed_accepted_audit():
    cli = _load_cli("validate_mission_rehearsal")
    audit = _AUDITS_DIR / "warehouse_pickup_route_alpha" / "rehearsal-audit.json"
    assert audit.is_file()
    code = cli.main(["--audit", str(audit), "--json"])
    assert code == 0


def test_validate_rejects_committed_rejected_audit():
    cli = _load_cli("validate_mission_rehearsal")
    audit = _AUDITS_DIR / "unsafe_speed_route" / "rehearsal-audit.json"
    assert audit.is_file()
    code = cli.main(["--audit", str(audit), "--json"])
    assert code != 0


def test_validate_detects_tampered_audit(tmp_path: Path):
    src = _AUDITS_DIR / "warehouse_pickup_route_alpha" / "rehearsal-audit.json"
    payload = json.loads(src.read_text(encoding="utf-8"))
    # Tamper: add a forbidden topic to the plan.
    payload["plan"]["requested_topics"].append("/cmd_vel")
    bad = tmp_path / "tampered.json"
    bad.write_text(json.dumps(payload), encoding="utf-8")
    cli = _load_cli("validate_mission_rehearsal")
    code = cli.main(["--audit", str(bad), "--json"])
    assert code != 0


def test_validate_handles_missing_file(tmp_path: Path):
    cli = _load_cli("validate_mission_rehearsal")
    code = cli.main(["--audit", str(tmp_path / "missing.json")])
    assert code == 2


# --- generate_rehearsal_examples -------------------------------------


def test_generate_examples_is_idempotent_for_fixed_timestamp(tmp_path: Path):
    cli = _load_cli("generate_rehearsal_examples")

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

    for fixture_id in (
        "warehouse_pickup_route_alpha",
        "bounded_forward_patrol",
        "unsafe_speed_route",
        "infinite_patrol_loop",
    ):
        for name in (
            "mission-plan.json",
            "rehearsal-audit.json",
            "replay-review.json",
            "analytics.json",
        ):
            text_a = (a / "audits" / fixture_id / name).read_text(encoding="utf-8")
            text_b = (b / "audits" / fixture_id / name).read_text(encoding="utf-8")
            assert text_a == text_b, f"{fixture_id}/{name}"


def test_generate_examples_covers_ten_fixtures(tmp_path: Path):
    cli = _load_cli("generate_rehearsal_examples")
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
    assert len(audits) == 10


# --- generate_rehearsal_replay --------------------------------------


def test_generate_replay_refreshes_artifacts(tmp_path: Path):
    # Copy a committed audit into tmp_path, refresh replay artefacts,
    # confirm the bundle now has replay-review.json / replay-review.md /
    # analytics.json with bag_backed=False.
    import shutil

    src_dir = _AUDITS_DIR / "warehouse_pickup_route_alpha"
    dst_dir = tmp_path / "warehouse_pickup_route_alpha"
    shutil.copytree(src_dir, dst_dir)
    audit_path = dst_dir / "rehearsal-audit.json"

    cli = _load_cli("generate_rehearsal_replay")
    code = cli.main(["--audit", str(audit_path), "--json"])
    assert code == 0
    replay = json.loads((dst_dir / "replay-review.json").read_text(encoding="utf-8"))
    assert replay["bag_backed"] is False
    assert replay["evidence_status"] == "simulated"


def test_generate_replay_handles_missing_file(tmp_path: Path):
    cli = _load_cli("generate_rehearsal_replay")
    code = cli.main(["--audit", str(tmp_path / "missing.json")])
    assert code == 2
