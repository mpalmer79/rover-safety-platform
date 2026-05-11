"""Tests for the Phase 18 artifact-registry layer.

Honesty rules under test:

* the registry never silently upgrades integrity;
* hash drift between expected + computed produces ``failed``;
* missing files produce ``missing``;
* lifecycle promotion respects the rung order;
* the canonical fixture's committed hashes match the bytes on disk.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.artifact_registry import (
    ARTIFACT_KIND_SPATIAL_REPLAY,
    INTEGRITY_FAILED,
    INTEGRITY_MISSING,
    INTEGRITY_PARTIAL,
    INTEGRITY_PASSED,
    INTEGRITY_UNVERIFIED,
    LIFECYCLE_CANONICAL,
    LIFECYCLE_COMMITTED,
    LIFECYCLE_DEPRECATED,
    LIFECYCLE_GENERATED,
    LIFECYCLE_HYDRATED,
    LIFECYCLE_VERIFIED,
    ArtifactFile,
    ArtifactRecord,
    ArtifactRegistry,
    REGISTRY_RELATIVE_PATH,
    aggregate_integrity,
    can_promote,
    default_registry_path,
    discover_run_files,
    hash_bytes,
    hash_file,
    hashes_match,
    integrity_for_run_id,
    is_authoritative,
    is_deprecated,
    lifecycle_for_integrity,
    list_authoritative_records,
    load_registry,
    load_registry_or_empty,
    registry_from_dict,
    registry_to_dict,
    render_hydration_markdown,
    render_registry_markdown,
    short_hash,
    verify_artifact,
    verify_registry,
    write_registry,
)
from app.artifact_registry.models import HydrationOutcome, HydrationReport


REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------
# Hashing primitives
# ---------------------------------------------------------------------


def test_hash_bytes_is_deterministic() -> None:
    assert hash_bytes(b"abc") == hash_bytes(b"abc")
    assert hash_bytes(b"abc") != hash_bytes(b"abd")


def test_hash_file_returns_empty_on_missing(tmp_path: Path) -> None:
    assert hash_file(tmp_path / "nope") == ""


def test_short_hash_truncates() -> None:
    full = "0" * 64
    assert len(short_hash(full)) == 16
    assert short_hash("") == ""


def test_hashes_match_is_case_insensitive() -> None:
    assert hashes_match("ABCDEF", "abcdef")
    assert not hashes_match("", "abc")


# ---------------------------------------------------------------------
# Registry round-trip
# ---------------------------------------------------------------------


def _sample_record() -> ArtifactRecord:
    return ArtifactRecord(
        run_id="r-1",
        kind=ARTIFACT_KIND_SPATIAL_REPLAY,
        derivation_source="fixture",
        bag_status="missing_manifest",
        lifecycle=LIFECYCLE_CANONICAL,
        integrity=INTEGRITY_PASSED,
        files=(
            ArtifactFile(
                relative_path="spatial-replay/runs/r-1/spatial-replay.json",
                expected_hash="0" * 64,
                size_bytes=10,
            ),
        ),
        related_mission_id="m",
        related_scenario_id="s",
        notes=("note",),
        generated_at_utc="2026-05-11T18:00:00+00:00",
    )


def test_registry_round_trip(tmp_path: Path) -> None:
    record = _sample_record()
    registry = ArtifactRegistry(
        generated_at_utc="2026-05-11T18:00:00+00:00",
        schema_version="phase18-1",
        artefact_root="spatial-replay",
        records=(record,),
    )
    path = tmp_path / "reg.json"
    write_registry(registry, path)
    loaded = load_registry(path)
    assert loaded is not None
    assert loaded.records[0].run_id == "r-1"
    assert loaded.records[0].lifecycle == LIFECYCLE_CANONICAL


def test_load_registry_returns_none_on_missing(tmp_path: Path) -> None:
    assert load_registry(tmp_path / "nope") is None


def test_load_registry_returns_none_on_invalid_json(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text("not json", encoding="utf-8")
    assert load_registry(p) is None


def test_load_registry_or_empty_returns_empty_when_missing(tmp_path: Path) -> None:
    reg = load_registry_or_empty(tmp_path)
    assert reg.records == ()


def test_registry_from_dict_coerces_strings() -> None:
    payload = {
        "schema_version": "x",
        "records": [
            {
                "run_id": "r",
                "kind": "spatial_replay",
                "derivation_source": "fixture",
                "bag_status": "missing_manifest",
                "lifecycle": "canonical",
                "integrity": "passed",
                "files": [
                    {
                        "relative_path": "f",
                        "expected_hash": "h",
                        "size_bytes": 1,
                    }
                ],
            }
        ],
    }
    reg = registry_from_dict(payload)
    assert reg.records[0].files[0].relative_path == "f"


def test_registry_to_dict_preserves_files() -> None:
    record = _sample_record()
    reg = ArtifactRegistry(
        generated_at_utc="x",
        schema_version="phase18-1",
        artefact_root="spatial-replay",
        records=(record,),
    )
    out = registry_to_dict(reg)
    assert out["records"][0]["files"][0]["expected_hash"] == "0" * 64


# ---------------------------------------------------------------------
# Integrity verification
# ---------------------------------------------------------------------


def test_verify_artifact_passes_when_hash_matches(tmp_path: Path) -> None:
    file = tmp_path / "f.txt"
    file.write_text("hello", encoding="utf-8")
    record = ArtifactRecord(
        run_id="r",
        kind=ARTIFACT_KIND_SPATIAL_REPLAY,
        derivation_source="fixture",
        bag_status="missing_manifest",
        lifecycle=LIFECYCLE_CANONICAL,
        integrity=INTEGRITY_UNVERIFIED,
        files=(
            ArtifactFile(
                relative_path="f.txt",
                expected_hash=hash_file(file),
                size_bytes=file.stat().st_size,
            ),
        ),
    )
    integrity, _, drift = verify_artifact(record, artefact_root=tmp_path)
    assert integrity == INTEGRITY_PASSED
    assert drift == []


def test_verify_artifact_failed_on_mismatch(tmp_path: Path) -> None:
    file = tmp_path / "f.txt"
    file.write_text("hello", encoding="utf-8")
    record = ArtifactRecord(
        run_id="r",
        kind=ARTIFACT_KIND_SPATIAL_REPLAY,
        derivation_source="fixture",
        bag_status="missing_manifest",
        lifecycle=LIFECYCLE_CANONICAL,
        integrity=INTEGRITY_UNVERIFIED,
        files=(
            ArtifactFile(
                relative_path="f.txt",
                expected_hash="deadbeef",
                size_bytes=file.stat().st_size,
            ),
        ),
    )
    integrity, _, drift = verify_artifact(record, artefact_root=tmp_path)
    assert integrity == INTEGRITY_FAILED
    assert any("hash mismatch" in d for d in drift)


def test_verify_artifact_missing_when_files_absent(tmp_path: Path) -> None:
    record = ArtifactRecord(
        run_id="r",
        kind=ARTIFACT_KIND_SPATIAL_REPLAY,
        derivation_source="fixture",
        bag_status="missing_manifest",
        lifecycle=LIFECYCLE_CANONICAL,
        integrity=INTEGRITY_UNVERIFIED,
        files=(
            ArtifactFile(
                relative_path="missing.txt",
                expected_hash="abc",
                size_bytes=10,
            ),
        ),
    )
    integrity, _, drift = verify_artifact(record, artefact_root=tmp_path)
    assert integrity == INTEGRITY_MISSING


def test_verify_artifact_partial_when_some_files_missing(tmp_path: Path) -> None:
    file = tmp_path / "f.txt"
    file.write_text("hello", encoding="utf-8")
    record = ArtifactRecord(
        run_id="r",
        kind=ARTIFACT_KIND_SPATIAL_REPLAY,
        derivation_source="fixture",
        bag_status="missing_manifest",
        lifecycle=LIFECYCLE_CANONICAL,
        integrity=INTEGRITY_UNVERIFIED,
        files=(
            ArtifactFile("f.txt", hash_file(file), file.stat().st_size),
            ArtifactFile("missing.txt", "abc", 1),
        ),
    )
    integrity, _, _ = verify_artifact(record, artefact_root=tmp_path)
    assert integrity == INTEGRITY_PARTIAL


def test_aggregate_integrity_rolls_up() -> None:
    assert aggregate_integrity([]) == INTEGRITY_UNVERIFIED
    assert aggregate_integrity([INTEGRITY_PASSED]) == INTEGRITY_PASSED
    assert aggregate_integrity([INTEGRITY_PASSED, INTEGRITY_PARTIAL]) == INTEGRITY_PARTIAL
    assert aggregate_integrity([INTEGRITY_PASSED, INTEGRITY_FAILED]) == INTEGRITY_FAILED
    assert aggregate_integrity([INTEGRITY_MISSING, INTEGRITY_MISSING]) == INTEGRITY_MISSING


# ---------------------------------------------------------------------
# Lifecycle helpers
# ---------------------------------------------------------------------


def test_can_promote_only_moves_up() -> None:
    assert can_promote(LIFECYCLE_GENERATED, LIFECYCLE_HYDRATED)
    assert can_promote(LIFECYCLE_COMMITTED, LIFECYCLE_VERIFIED)
    assert can_promote(LIFECYCLE_VERIFIED, LIFECYCLE_CANONICAL)
    assert not can_promote(LIFECYCLE_CANONICAL, LIFECYCLE_VERIFIED)
    assert not can_promote(LIFECYCLE_HYDRATED, LIFECYCLE_GENERATED)
    assert can_promote(LIFECYCLE_CANONICAL, LIFECYCLE_DEPRECATED)


def test_can_promote_unknown_state_rejected() -> None:
    assert not can_promote("nonsense", LIFECYCLE_CANONICAL)
    assert not can_promote(LIFECYCLE_CANONICAL, "nonsense")


def test_is_authoritative_only_for_committed_or_above() -> None:
    assert is_authoritative(LIFECYCLE_COMMITTED)
    assert is_authoritative(LIFECYCLE_VERIFIED)
    assert is_authoritative(LIFECYCLE_CANONICAL)
    assert not is_authoritative(LIFECYCLE_GENERATED)
    assert not is_authoritative(LIFECYCLE_DEPRECATED)


def test_is_deprecated() -> None:
    assert is_deprecated(LIFECYCLE_DEPRECATED)
    assert not is_deprecated(LIFECYCLE_CANONICAL)


def test_lifecycle_clamped_to_committed_when_integrity_drops() -> None:
    assert (
        lifecycle_for_integrity(INTEGRITY_FAILED, LIFECYCLE_CANONICAL)
        == LIFECYCLE_COMMITTED
    )
    assert (
        lifecycle_for_integrity(INTEGRITY_PASSED, LIFECYCLE_CANONICAL)
        == LIFECYCLE_CANONICAL
    )


# ---------------------------------------------------------------------
# Discovery + selection helpers
# ---------------------------------------------------------------------


def test_discover_run_files_skips_dotfiles(tmp_path: Path) -> None:
    base = tmp_path / "spatial-replay" / "runs" / "r"
    base.mkdir(parents=True)
    (base / "ok.json").write_text("{}", encoding="utf-8")
    (base / ".hidden").write_text("x", encoding="utf-8")
    files = discover_run_files(base)
    paths = [f.relative_path for f in files]
    assert any("ok.json" in p for p in paths)
    assert all(".hidden" not in p for p in paths)


def test_list_authoritative_records_filters() -> None:
    records = (
        ArtifactRecord(
            run_id="canon",
            kind=ARTIFACT_KIND_SPATIAL_REPLAY,
            derivation_source="fixture",
            bag_status="missing_manifest",
            lifecycle=LIFECYCLE_CANONICAL,
            integrity=INTEGRITY_PASSED,
            files=(),
        ),
        ArtifactRecord(
            run_id="dep",
            kind=ARTIFACT_KIND_SPATIAL_REPLAY,
            derivation_source="fixture",
            bag_status="missing_manifest",
            lifecycle=LIFECYCLE_DEPRECATED,
            integrity=INTEGRITY_PASSED,
            files=(),
        ),
        ArtifactRecord(
            run_id="gen",
            kind=ARTIFACT_KIND_SPATIAL_REPLAY,
            derivation_source="fixture",
            bag_status="missing_manifest",
            lifecycle=LIFECYCLE_GENERATED,
            integrity=INTEGRITY_PASSED,
            files=(),
        ),
    )
    reg = ArtifactRegistry(
        generated_at_utc="x",
        schema_version="phase18-1",
        artefact_root="spatial-replay",
        records=records,
    )
    auth = list_authoritative_records(reg)
    ids = [r.run_id for r in auth]
    assert ids == ["canon"]


def test_integrity_for_run_id_returns_missing_for_unknown(tmp_path: Path) -> None:
    reg = ArtifactRegistry(
        generated_at_utc="",
        schema_version="phase18-1",
        artefact_root="spatial-replay",
        records=(),
    )
    assert integrity_for_run_id(reg, "nope", artefact_root=tmp_path) == "missing"


# ---------------------------------------------------------------------
# Reporter
# ---------------------------------------------------------------------


def test_render_registry_markdown_lists_records() -> None:
    reg = ArtifactRegistry(
        generated_at_utc="x",
        schema_version="phase18-1",
        artefact_root="spatial-replay",
        records=(_sample_record(),),
    )
    md = render_registry_markdown(reg)
    assert "Canonical artefact registry" in md
    assert "r-1" in md
    assert "fixture" in md


def test_render_registry_markdown_handles_empty_registry() -> None:
    reg = ArtifactRegistry(
        generated_at_utc="x",
        schema_version="phase18-1",
        artefact_root="spatial-replay",
        records=(),
    )
    md = render_registry_markdown(reg)
    assert "No artefacts" in md


def test_render_hydration_markdown_lists_outcomes() -> None:
    report = HydrationReport(
        generated_at_utc="t",
        registry_path="p",
        artefact_root="r",
        outcomes=(
            HydrationOutcome(
                run_id="r-1",
                rebuilt=True,
                integrity=INTEGRITY_PASSED,
                expected_hashes={},
                computed_hashes={},
            ),
        ),
        overall_integrity=INTEGRITY_PASSED,
    )
    md = render_hydration_markdown(report)
    assert "r-1" in md
    assert "passed" in md.lower()


# ---------------------------------------------------------------------
# Canonical fixture round-trip (committed registry must stay honest)
# ---------------------------------------------------------------------


def test_canonical_registry_loads_and_validates() -> None:
    reg = load_registry(default_registry_path(REPO_ROOT))
    assert reg is not None
    assert any(r.run_id == "canonical-fixture" for r in reg.records)
    record = next(r for r in reg.records if r.run_id == "canonical-fixture")
    # The canonical fixture must NEVER be labelled bag_backed.
    assert record.derivation_source == "fixture"
    assert record.bag_status == "missing_manifest"


def test_canonical_registry_paths_match_disk() -> None:
    reg = load_registry(default_registry_path(REPO_ROOT))
    assert reg is not None
    record = next(r for r in reg.records if r.run_id == "canonical-fixture")
    integrity, _, drift = verify_artifact(record, artefact_root=REPO_ROOT)
    assert integrity == INTEGRITY_PASSED, drift


def test_default_registry_path_uses_canonical_relative_path(tmp_path: Path) -> None:
    p = default_registry_path(tmp_path)
    assert p.as_posix().endswith(REGISTRY_RELATIVE_PATH)
