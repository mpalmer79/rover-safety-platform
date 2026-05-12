"""Phase 20B: the canonical replay fixture must be committed.

A fresh clone of the repository must carry the canonical fixture
artefacts on disk so backend pytest does NOT depend on running the
hydration tool first. The test fails honestly when a registered
canonical-fixture file is missing.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from app.artifact_registry import default_registry_path, load_registry


REPO_ROOT = Path(__file__).resolve().parents[2]


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_canonical_fixture_files_are_committed() -> None:
    reg = load_registry(default_registry_path(REPO_ROOT))
    assert reg is not None
    record = next(r for r in reg.records if r.run_id == "canonical-fixture")
    for f in record.files:
        path = REPO_ROOT / f.relative_path
        assert path.exists(), (
            f"{f.relative_path} is missing from the working tree. "
            f"A fresh clone must carry the canonical fixture — run "
            f"`python tools/hydrate_replay_artifacts.py` and commit the "
            f"output, then update .gitignore if necessary."
        )


def test_canonical_fixture_hashes_match_registry() -> None:
    reg = load_registry(default_registry_path(REPO_ROOT))
    assert reg is not None
    record = next(r for r in reg.records if r.run_id == "canonical-fixture")
    for f in record.files:
        path = REPO_ROOT / f.relative_path
        if not f.expected_hash:
            continue  # no expected hash recorded
        computed = _digest(path)
        assert computed.lower() == f.expected_hash.lower(), (
            f"hash drift for {f.relative_path}: "
            f"expected={f.expected_hash[:12]} computed={computed[:12]}"
        )


def test_canonical_fixture_is_referenced_by_gitignore_exception() -> None:
    """If ``spatial-replay/runs/`` is gitignored, an exception MUST
    re-include the canonical-fixture path. Otherwise a fresh clone
    will be missing committed bytes."""

    gitignore_path = REPO_ROOT / ".gitignore"
    assert gitignore_path.exists()
    text = gitignore_path.read_text(encoding="utf-8")
    if "runs/" not in text:
        return  # no ignore rule, nothing to assert
    assert "!spatial-replay/runs/canonical-fixture" in text, (
        ".gitignore ignores runs/ but does not re-include the "
        "canonical-fixture path. A fresh clone will fail backend pytest."
    )
