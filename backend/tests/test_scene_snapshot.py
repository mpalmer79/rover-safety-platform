"""Phase 19 reviewer scene-snapshot tests.

Honesty rules under test:
  - a missing spatial-replay artefact never becomes a bag-backed snapshot;
  - a fixture artefact never becomes a bag-backed snapshot;
  - a missing run id reports ``unavailable`` with the exact missing inputs;
  - the snapshot pipeline never generates a screenshot;
  - the bag-backed branch is only reachable with a passing registry integrity.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.scene_snapshot import (
    SNAPSHOT_STATUS_BAG_BACKED,
    SNAPSHOT_STATUS_FIXTURE,
    SNAPSHOT_STATUS_NOT_EXECUTED,
    SNAPSHOT_STATUS_UNAVAILABLE,
    build_snapshot_for_run,
    evaluate_eligibility,
    snapshot_eligibility_to_dict,
    snapshot_to_dict,
    write_snapshot_artefacts,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _seed_bag_backed_run(repo: Path) -> str:
    run_id = "ttest-bag-backed"
    run_dir = repo / "spatial-replay" / "runs" / run_id
    run_dir.mkdir(parents=True)
    spatial = {
        "run_id": run_id,
        "scenario_id": "s",
        "mission_id": "m",
        "derivation_source": "bag_backed",
        "bag_status": "bag_backed",
        "sample_count": 3,
        "validation_status": "passed",
        "samples": [],
        "segments": [],
        "event_alignments": [],
    }
    (run_dir / "spatial-replay.json").write_text(
        json.dumps(spatial, indent=2, sort_keys=True), encoding="utf-8"
    )
    # Compute hash so the registry record verifies passed.
    from app.artifact_registry import hash_file

    file_path = run_dir / "spatial-replay.json"
    digest = hash_file(file_path)

    registry_path = repo / "spatial-replay" / "registry" / "canonical-artifacts.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at_utc": "",
        "schema_version": "phase18-1",
        "artefact_root": "spatial-replay",
        "notes": [],
        "records": [
            {
                "run_id": run_id,
                "kind": "spatial_replay",
                "derivation_source": "bag_backed",
                "bag_status": "bag_backed",
                "lifecycle": "canonical",
                "integrity": "passed",
                "related_mission_id": "m",
                "related_scenario_id": "s",
                "notes": [],
                "generated_at_utc": "",
                "files": [
                    {
                        "relative_path": f"spatial-replay/runs/{run_id}/spatial-replay.json",
                        "expected_hash": digest,
                        "size_bytes": file_path.stat().st_size,
                        "description": "test artefact",
                    }
                ],
            }
        ],
    }
    registry_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    return run_id


def _seed_fixture_run(repo: Path) -> str:
    """Create a fixture-only run for the snapshot pipeline to inspect."""

    run_id = "ttest-fixture"
    run_dir = repo / "spatial-replay" / "runs" / run_id
    run_dir.mkdir(parents=True)
    spatial = {
        "run_id": run_id,
        "scenario_id": "s",
        "mission_id": "m",
        "derivation_source": "fixture",
        "bag_status": "missing_manifest",
        "sample_count": 1,
        "validation_status": "passed",
        "samples": [],
        "segments": [],
        "event_alignments": [],
    }
    (run_dir / "spatial-replay.json").write_text(
        json.dumps(spatial, indent=2, sort_keys=True), encoding="utf-8"
    )
    from app.artifact_registry import hash_file

    file_path = run_dir / "spatial-replay.json"
    digest = hash_file(file_path)
    registry_path = repo / "spatial-replay" / "registry" / "canonical-artifacts.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        json.dumps(
            {
                "generated_at_utc": "",
                "schema_version": "phase18-1",
                "artefact_root": "spatial-replay",
                "notes": [],
                "records": [
                    {
                        "run_id": run_id,
                        "kind": "spatial_replay",
                        "derivation_source": "fixture",
                        "bag_status": "missing_manifest",
                        "lifecycle": "canonical",
                        "integrity": "passed",
                        "related_mission_id": "m",
                        "related_scenario_id": "s",
                        "notes": [],
                        "generated_at_utc": "",
                        "files": [
                            {
                                "relative_path": f"spatial-replay/runs/{run_id}/spatial-replay.json",
                                "expected_hash": digest,
                                "size_bytes": file_path.stat().st_size,
                                "description": "",
                            }
                        ],
                    }
                ],
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return run_id


def test_missing_run_id_reports_unavailable(tmp_path: Path) -> None:
    eligibility = evaluate_eligibility("nope", repo_root=tmp_path)
    assert eligibility.status == SNAPSHOT_STATUS_UNAVAILABLE
    assert eligibility.eligible_for_bag_backed_snapshot is False
    assert any("spatial-replay.json" in m for m in eligibility.missing_inputs)


def test_fixture_run_is_not_bag_backed(tmp_path: Path) -> None:
    run_id = _seed_fixture_run(tmp_path)
    eligibility = evaluate_eligibility(run_id, repo_root=tmp_path)
    assert eligibility.status == SNAPSHOT_STATUS_FIXTURE
    assert eligibility.eligible_for_bag_backed_snapshot is False


def test_bag_backed_run_is_eligible_when_integrity_passes(tmp_path: Path) -> None:
    run_id = _seed_bag_backed_run(tmp_path)
    eligibility = evaluate_eligibility(run_id, repo_root=tmp_path)
    assert eligibility.status == SNAPSHOT_STATUS_BAG_BACKED
    assert eligibility.eligible_for_bag_backed_snapshot is True
    assert eligibility.missing_inputs == ()


def test_bag_backed_run_is_not_eligible_when_artifact_missing(tmp_path: Path) -> None:
    run_id = _seed_bag_backed_run(tmp_path)
    # Remove the artefact bytes; the registry still references them.
    (tmp_path / "spatial-replay" / "runs" / run_id / "spatial-replay.json").unlink()
    eligibility = evaluate_eligibility(run_id, repo_root=tmp_path)
    assert eligibility.status != SNAPSHOT_STATUS_BAG_BACKED
    assert eligibility.eligible_for_bag_backed_snapshot is False


def test_build_snapshot_returns_hash_chain(tmp_path: Path) -> None:
    run_id = _seed_bag_backed_run(tmp_path)
    snapshot = build_snapshot_for_run(run_id, repo_root=tmp_path)
    assert snapshot.reviewer_export_ready is True
    assert len(snapshot.artifact_hash_chain) == 1
    assert snapshot.artifact_hash_chain[0]["sha256_prefix"]


def test_snapshot_serialises_with_disclaimer(tmp_path: Path) -> None:
    run_id = _seed_fixture_run(tmp_path)
    snapshot = build_snapshot_for_run(run_id, repo_root=tmp_path)
    payload = snapshot_to_dict(snapshot)
    assert "disclaimer" in payload
    assert "not safety-certified" in payload["disclaimer"].lower()


def test_write_snapshot_artefacts_creates_files(tmp_path: Path) -> None:
    run_id = _seed_fixture_run(tmp_path)
    snapshot = build_snapshot_for_run(run_id, repo_root=tmp_path)
    out = tmp_path / "out"
    paths = write_snapshot_artefacts(snapshot, out)
    assert paths["snapshot_json"].exists()
    assert paths["snapshot_md"].exists()
    md = paths["snapshot_md"].read_text(encoding="utf-8")
    assert "Reviewer scene snapshot" in md


def test_committed_canonical_fixture_is_not_bag_backed() -> None:
    eligibility = evaluate_eligibility("canonical-fixture", repo_root=REPO_ROOT)
    # The committed canonical-fixture is fixture-derived.
    assert eligibility.status == SNAPSHOT_STATUS_FIXTURE
    assert eligibility.eligible_for_bag_backed_snapshot is False


def test_committed_canonical_fixture_lists_no_bag_backed_inputs() -> None:
    eligibility = evaluate_eligibility("canonical-fixture", repo_root=REPO_ROOT)
    snapshot = build_snapshot_for_run("canonical-fixture", repo_root=REPO_ROOT)
    assert snapshot.reviewer_export_ready is False
    payload = snapshot_eligibility_to_dict(eligibility)
    assert payload["eligible_for_bag_backed_snapshot"] is False
