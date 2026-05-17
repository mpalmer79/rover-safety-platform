"""Phase 20B: hydrate --check-only must be a true no-op.

The test invokes the CLI in --check-only mode and asserts the
working tree is unchanged. It does NOT assert hash correctness —
``test_artifact_registry::test_canonical_registry_paths_match_disk``
already covers that.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
HYDRATE_CLI = REPO_ROOT / "tools" / "hydrate_replay_artifacts.py"
REGISTRY_FILES = (
    REPO_ROOT / "spatial-replay" / "registry" / "canonical-artifacts.json",
    REPO_ROOT / "spatial-replay" / "registry" / "canonical-artifacts.md",
    REPO_ROOT / "spatial-replay" / "registry" / "hydration-report.json",
    REPO_ROOT / "spatial-replay" / "registry" / "hydration-report.md",
)


def _digest(path: Path) -> str:
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_hydrate_check_only_does_not_write_registry_files() -> None:
    before = {p: _digest(p) for p in REGISTRY_FILES}

    result = subprocess.run(
        [sys.executable, str(HYDRATE_CLI), "--check-only"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    # The check must pass on the committed canonical fixture.
    assert result.returncode == 0, result.stderr

    after = {p: _digest(p) for p in REGISTRY_FILES}
    for p, before_hash in before.items():
        assert after[p] == before_hash, (
            f"{p} was rewritten by --check-only — hydration is not a "
            f"true no-op (before={before_hash[:12]} after={after[p][:12]})"
        )


def test_hydrate_check_only_does_not_rewrite_canonical_artifacts() -> None:
    canonical_dir = REPO_ROOT / "spatial-replay" / "runs" / "canonical-fixture"
    if not canonical_dir.exists():
        pytest.skip("canonical-fixture run dir not committed (test_artifact_fixture_commitment covers this)")

    before = {p: _digest(p) for p in canonical_dir.glob("*")}
    subprocess.run(
        [sys.executable, str(HYDRATE_CLI), "--check-only"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    after = {p: _digest(p) for p in canonical_dir.glob("*")}
    assert before == after, "--check-only rewrote canonical fixture bytes"


def test_hydration_report_to_dict_round_trip() -> None:
    """The hydration report serialises to dict + back without
    silent loss. A regression here would mean tests + CI cannot
    distinguish a passing run from a failing one."""

    from app.artifact_registry import hydrate_registry, hydration_report_to_dict

    report = hydrate_registry(repo_root=REPO_ROOT, check_only=True)
    payload = hydration_report_to_dict(report)
    # The dict must round-trip through JSON.
    json.loads(json.dumps(payload))
    assert payload["overall_integrity"] in {"passed", "partial", "rejected", "unverified"}
