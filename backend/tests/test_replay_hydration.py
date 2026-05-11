"""End-to-end tests for the Phase 18 replay-hydration pipeline.

The committed canonical registry must hydrate cleanly with no drift.
A drift here is the exact failure pattern that broke Phase 17C CI.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from app.artifact_registry import (
    INTEGRITY_FAILED,
    INTEGRITY_PASSED,
    hydrate_registry,
    hydration_report_to_dict,
    load_registry,
    default_registry_path,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _copy_repo_subset(src: Path, dst: Path) -> None:
    """Copy the minimal subset of the repo needed for hydration."""

    for sub in ("backend", "spatial-replay", "mission-rehearsals"):
        s = src / sub
        d = dst / sub
        if s.exists():
            shutil.copytree(s, d)


def test_hydration_passes_on_committed_registry() -> None:
    report = hydrate_registry(repo_root=REPO_ROOT, write_back=False)
    assert report.overall_integrity == INTEGRITY_PASSED, report.outcomes


def test_hydration_is_idempotent(tmp_path: Path) -> None:
    _copy_repo_subset(REPO_ROOT, tmp_path)
    a = hydrate_registry(repo_root=tmp_path, write_back=False)
    b = hydrate_registry(repo_root=tmp_path, write_back=False)
    assert a.overall_integrity == INTEGRITY_PASSED
    assert b.overall_integrity == INTEGRITY_PASSED
    a_hashes = {o.run_id: dict(o.computed_hashes) for o in a.outcomes}
    b_hashes = {o.run_id: dict(o.computed_hashes) for o in b.outcomes}
    assert a_hashes == b_hashes


def test_hydration_fails_when_registry_missing(tmp_path: Path) -> None:
    report = hydrate_registry(repo_root=tmp_path, write_back=False)
    assert report.overall_integrity != INTEGRITY_PASSED
    assert any("registry missing" in n for n in report.notes)


def test_hydration_fails_when_expected_hash_drifts(tmp_path: Path) -> None:
    _copy_repo_subset(REPO_ROOT, tmp_path)
    # Corrupt the registry hash for the canonical fixture.
    reg_path = default_registry_path(tmp_path)
    reg = load_registry(reg_path)
    assert reg is not None
    bad_records = []
    for r in reg.records:
        bad_files = tuple(
            f.__class__(
                relative_path=f.relative_path,
                expected_hash="0" * 64,
                size_bytes=f.size_bytes,
                description=f.description,
            )
            for f in r.files
        )
        bad_records.append(r.__class__(
            run_id=r.run_id,
            kind=r.kind,
            derivation_source=r.derivation_source,
            bag_status=r.bag_status,
            lifecycle=r.lifecycle,
            integrity=r.integrity,
            files=bad_files,
            related_mission_id=r.related_mission_id,
            related_scenario_id=r.related_scenario_id,
            notes=r.notes,
            generated_at_utc=r.generated_at_utc,
        ))
    bad_registry = reg.__class__(
        generated_at_utc=reg.generated_at_utc,
        schema_version=reg.schema_version,
        artefact_root=reg.artefact_root,
        records=tuple(bad_records),
        notes=reg.notes,
    )
    from app.artifact_registry import write_registry
    write_registry(bad_registry, reg_path)

    report = hydrate_registry(repo_root=tmp_path, write_back=False)
    assert report.overall_integrity == INTEGRITY_FAILED
    drift_messages = [d for o in report.outcomes for d in o.drift]
    assert any("hash mismatch" in d for d in drift_messages)


def test_hydration_does_not_rewrite_registry_on_failure(tmp_path: Path) -> None:
    _copy_repo_subset(REPO_ROOT, tmp_path)
    reg_path = default_registry_path(tmp_path)
    bytes_before = reg_path.read_bytes()
    # Corrupt source pose samples so hydration writes a different file
    # than the registry expects.
    poses = (
        tmp_path
        / "spatial-replay"
        / "fixtures"
        / "canonical-fixture"
        / "pose-samples.jsonl"
    )
    poses.write_text(poses.read_text().replace('"high"', '"medium"'), encoding="utf-8")

    report = hydrate_registry(repo_root=tmp_path, write_back=True)
    assert report.overall_integrity != INTEGRITY_PASSED
    # Honesty rule: a failing hydration must NOT rewrite the registry.
    assert reg_path.read_bytes() == bytes_before


def test_hydration_report_to_dict_preserves_drift() -> None:
    from app.artifact_registry.models import HydrationOutcome, HydrationReport

    report = HydrationReport(
        generated_at_utc="t",
        registry_path="p",
        artefact_root="r",
        outcomes=(
            HydrationOutcome(
                run_id="r-1",
                rebuilt=True,
                integrity="failed",
                expected_hashes={"f": "a"},
                computed_hashes={"f": "b"},
                drift=("hash mismatch: f",),
            ),
        ),
        overall_integrity="failed",
    )
    payload = hydration_report_to_dict(report)
    assert payload["overall_integrity"] == "failed"
    assert payload["outcomes"][0]["drift"] == ["hash mismatch: f"]


def test_canonical_fixture_is_never_bag_backed_after_hydration() -> None:
    report = hydrate_registry(repo_root=REPO_ROOT, write_back=False)
    reg = load_registry(default_registry_path(REPO_ROOT))
    assert reg is not None
    record = next(r for r in reg.records if r.run_id == "canonical-fixture")
    # The hydration must preserve the fixture honesty rule.
    assert record.derivation_source == "fixture"
    assert record.bag_status == "missing_manifest"
    # And the canonical-fixture run should pass integrity.
    outcome = next(o for o in report.outcomes if o.run_id == "canonical-fixture")
    assert outcome.integrity == INTEGRITY_PASSED
