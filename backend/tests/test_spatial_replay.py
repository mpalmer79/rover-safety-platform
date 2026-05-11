"""Tests for the Phase 17C spatial-replay layer.

Honesty rules under test:
* a missing bag manifest never produces ``bag_backed``;
* a manifest with missing artefacts never produces ``bag_backed``;
* fixture pose samples are never labelled ``bag_backed``;
* the trajectory builder is deterministic;
* the event aligner falls back to off-map when out of tolerance;
* the validator gate-keeps the bag-backed claim.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.live_runtime.bag_manifest import write_bag_manifest
from app.live_runtime.models import BagManifest
from app.spatial_replay import (
    DEFAULT_ALIGNMENT_TOLERANCE_NS,
    DERIVATION_BAG_BACKED,
    DERIVATION_FIXTURE,
    DERIVATION_UNAVAILABLE,
    PoseSample,
    SpatialReplay,
    TRAJECTORY_STATUS_COMPLETE,
    TRAJECTORY_STATUS_PARTIAL,
    align_event,
    align_events,
    build_segments,
    build_spatial_replay,
    classify_trajectory,
    evaluate_bag_eligibility,
    is_honestly_bag_backed,
    read_pose_samples,
    spatial_replay_to_dict,
    topic_sources,
    validate_spatial_replay,
    write_pose_samples,
    write_spatial_replay_artefacts,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_FIXTURE_ROOT = REPO_ROOT / "spatial-replay" / "fixtures"
CANONICAL_RUN_DIR = REPO_ROOT / "spatial-replay" / "runs" / "canonical-fixture"


# ---------------------------------------------------------------------
# Fixtures helpers
# ---------------------------------------------------------------------


def _bag_manifest(
    *,
    status: str = "bag_backed",
    bag_paths: tuple[str, ...] = ("bags/run.mcap",),
    metadata: str = "bags/metadata.yaml",
    topics: tuple[str, ...] = ("/odom", "/tf"),
    validation: str = "passed",
) -> BagManifest:
    return BagManifest(
        run_id="r-1",
        scenario_id="s-1",
        bag_status=status,
        bag_format="mcap",
        bag_paths=bag_paths,
        metadata_yaml_path=metadata,
        topic_inventory=topics,
        message_counts={t: 100 for t in topics},
        start_time="2026-05-11T00:00:00+00:00",
        end_time="2026-05-11T00:00:10+00:00",
        duration_seconds=10.0,
        missing_required_topics=(),
        validation_status=validation,
    )


# ---------------------------------------------------------------------
# Eligibility / bag-backed gating
# ---------------------------------------------------------------------


def test_missing_manifest_blocks_bag_backed() -> None:
    eligibility = evaluate_bag_eligibility(None, bundle_root=None, has_pose_samples=True)
    assert eligibility.is_bag_backed is False
    assert any("missing" in r for r in eligibility.reasons)


def test_partial_manifest_blocks_bag_backed() -> None:
    manifest = _bag_manifest(status="partial", validation="partial")
    eligibility = evaluate_bag_eligibility(
        manifest, bundle_root=None, has_pose_samples=True
    )
    assert eligibility.is_bag_backed is False
    assert any("partial" in r for r in eligibility.reasons)


def test_missing_pose_samples_blocks_bag_backed(tmp_path: Path) -> None:
    manifest = _bag_manifest()
    # Make the bag/metadata files exist so the bundle-root validator passes.
    (tmp_path / "bags").mkdir()
    (tmp_path / "bags" / "run.mcap").write_bytes(b"")
    (tmp_path / "bags" / "metadata.yaml").write_text("")
    eligibility = evaluate_bag_eligibility(
        manifest, bundle_root=tmp_path, has_pose_samples=False
    )
    assert eligibility.is_bag_backed is False
    assert any("pose samples" in r for r in eligibility.reasons)


def test_eligibility_passes_when_every_condition_is_met(tmp_path: Path) -> None:
    manifest = _bag_manifest()
    (tmp_path / "bags").mkdir()
    (tmp_path / "bags" / "run.mcap").write_bytes(b"")
    (tmp_path / "bags" / "metadata.yaml").write_text("")
    eligibility = evaluate_bag_eligibility(
        manifest, bundle_root=tmp_path, has_pose_samples=True
    )
    assert eligibility.is_bag_backed is True
    assert eligibility.reasons == ()


# ---------------------------------------------------------------------
# Fixture vs bag-backed distinction
# ---------------------------------------------------------------------


def test_fixture_samples_are_not_bag_backed(tmp_path: Path) -> None:
    fixtures_root = tmp_path / "fixtures"
    run_dir = fixtures_root / "run-x"
    run_dir.mkdir(parents=True)
    write_pose_samples(
        [
            PoseSample("s0", 0, 0.0, 0.0, 0.0, "/odom", "high"),
            PoseSample("s1", 1_000_000_000, 1.0, 0.0, 0.0, "/odom", "high"),
        ],
        run_dir / "pose-samples.jsonl",
    )
    replay = build_spatial_replay(
        run_id="run-x",
        scenario_id="s-1",
        mission_id="m-1",
        evidence_root=None,
        fixtures_root=fixtures_root,
        events=(),
        expected_topics=(),
    )
    assert replay.derivation_source == DERIVATION_FIXTURE
    assert replay.bag_status == "missing_manifest"
    assert len(replay.samples) == 2


def test_canonical_fixture_emits_fixture_derivation() -> None:
    samples = read_pose_samples(
        CANONICAL_FIXTURE_ROOT / "canonical-fixture" / "pose-samples.jsonl"
    )
    assert len(samples) == 10
    replay = build_spatial_replay(
        run_id="canonical-fixture",
        scenario_id="warehouse_pickup_route_alpha",
        mission_id="warehouse_pickup_route_alpha",
        evidence_root=None,
        fixtures_root=CANONICAL_FIXTURE_ROOT,
        events=(),
        expected_topics=(),
    )
    assert replay.derivation_source == DERIVATION_FIXTURE
    assert replay.bag_status == "missing_manifest"


def test_canonical_fixture_run_artifact_is_fixture_labelled() -> None:
    """The committed runs/canonical-fixture/spatial-replay.json must
    declare derivation_source=fixture, never bag_backed."""

    path = CANONICAL_RUN_DIR / "spatial-replay.json"
    assert path.exists(), "committed canonical fixture artefact missing"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["derivation_source"] == "fixture"
    assert data["bag_status"] == "missing_manifest"
    # Validation must be passed/partial (not_executed would mean no samples).
    assert data["validation_status"] in {"passed", "partial"}
    assert data["sample_count"] > 0


# ---------------------------------------------------------------------
# Derivation source round trip
# ---------------------------------------------------------------------


def test_derivation_source_round_trips_through_json() -> None:
    replay = SpatialReplay(
        run_id="r",
        scenario_id="s",
        mission_id="m",
        evidence_origin="fixture",
        bag_status="missing_manifest",
        derivation_source=DERIVATION_FIXTURE,
        trajectory_status=TRAJECTORY_STATUS_COMPLETE,
        validation_status="passed",
        samples=(PoseSample("s0", 0, 0.0, 0.0, 0.0, "/odom", "high"),),
    )
    payload = spatial_replay_to_dict(replay)
    assert payload["derivation_source"] == DERIVATION_FIXTURE
    assert payload["bag_status"] == "missing_manifest"
    # JSON round-trip preserves the string verbatim.
    assert json.loads(json.dumps(payload))["derivation_source"] == DERIVATION_FIXTURE


def test_validator_rejects_bag_backed_without_samples() -> None:
    replay = SpatialReplay(
        run_id="r",
        scenario_id="s",
        mission_id="m",
        evidence_origin="runtime",
        bag_status="bag_backed",
        derivation_source=DERIVATION_BAG_BACKED,
        trajectory_status="missing",
        validation_status="not_executed",
        samples=(),
    )
    validation = validate_spatial_replay(replay)
    assert validation.status == "failed"
    assert any("requires at least one pose sample" in w for w in validation.warnings)


# ---------------------------------------------------------------------
# Trajectory builder determinism + classification
# ---------------------------------------------------------------------


def test_segments_are_deterministic() -> None:
    samples = (
        PoseSample("s0", 0, 0.0, 0.0, 0.0, "/odom", "high"),
        PoseSample("s1", 1_000_000_000, 1.0, 0.0, 0.0, "/odom", "high"),
        PoseSample("s2", 2_000_000_000, 2.0, 0.0, 0.0, "/odom", "high"),
    )
    a = build_segments(samples)
    b = build_segments(samples)
    assert len(a) == 2
    assert a == b
    # First segment is exactly 1 m, 1 s long.
    assert a[0].distance_m == pytest.approx(1.0)
    assert a[0].duration_ns == 1_000_000_000


def test_classify_trajectory_complete_partial_missing() -> None:
    s = (
        PoseSample("s0", 0, 0.0, 0.0, 0.0, "/odom", "high"),
        PoseSample("s1", 1_000_000_000, 1.0, 0.0, 0.0, "/odom", "high"),
    )
    assert classify_trajectory(s, expected_topics=("/odom",)) == TRAJECTORY_STATUS_COMPLETE
    assert classify_trajectory(s, expected_topics=("/odom", "/tf")) == TRAJECTORY_STATUS_PARTIAL
    assert classify_trajectory(()) == "missing"


def test_topic_sources_returns_unique_sorted() -> None:
    s = (
        PoseSample("s0", 0, 0.0, 0.0, 0.0, "/odom", "high"),
        PoseSample("s1", 1_000_000_000, 1.0, 0.0, 0.0, "/tf", "high"),
    )
    assert topic_sources(s) == ("/odom", "/tf")


# ---------------------------------------------------------------------
# Event alignment
# ---------------------------------------------------------------------


def test_event_alignment_matches_nearest_sample() -> None:
    samples = (
        PoseSample("s0", 0, 0.0, 0.0, 0.0, "/odom", "high"),
        PoseSample("s1", 1_000_000_000, 1.0, 0.0, 0.0, "/odom", "high"),
        PoseSample("s2", 2_000_000_000, 2.0, 0.0, 0.0, "/odom", "high"),
    )
    event = {
        "event_id": "e1",
        "event_time_ns": 1_050_000_000,
        "deterministic_hash": "h1",
    }
    alignment = align_event(event, samples)
    assert alignment.matched_sample_id == "s1"
    assert alignment.spatial_position == (1.0, 0.0)
    assert alignment.confidence == "high"


def test_event_alignment_off_map_when_out_of_tolerance() -> None:
    samples = (PoseSample("s0", 0, 0.0, 0.0, 0.0, "/odom", "high"),)
    event = {
        "event_id": "e1",
        "event_time_ns": 5_000_000_000,
        "deterministic_hash": "h1",
    }
    alignment = align_event(event, samples, tolerance_ns=DEFAULT_ALIGNMENT_TOLERANCE_NS)
    assert alignment.matched_sample_id == ""
    assert alignment.spatial_position is None
    assert alignment.confidence == "unaligned"


def test_align_events_preserves_order() -> None:
    samples = (PoseSample("s0", 0, 0.0, 0.0, 0.0, "/odom", "high"),)
    events = [
        {"event_id": "a", "event_time_ns": 0, "deterministic_hash": "h-a"},
        {"event_id": "b", "event_time_ns": 0, "deterministic_hash": "h-b"},
    ]
    out = align_events(events, samples)
    assert [a.event_id for a in out] == ["a", "b"]


# ---------------------------------------------------------------------
# Missing-topic honesty
# ---------------------------------------------------------------------


def test_missing_topic_produces_warning_not_fabrication(tmp_path: Path) -> None:
    fixtures_root = tmp_path / "fixtures"
    run_dir = fixtures_root / "rid"
    run_dir.mkdir(parents=True)
    write_pose_samples(
        [
            PoseSample("s0", 0, 0.0, 0.0, 0.0, "/odom", "high"),
            PoseSample("s1", 1_000_000_000, 1.0, 0.0, 0.0, "/odom", "high"),
        ],
        run_dir / "pose-samples.jsonl",
    )
    replay = build_spatial_replay(
        run_id="rid",
        scenario_id="s",
        mission_id="m",
        evidence_root=None,
        fixtures_root=fixtures_root,
        events=(),
        expected_topics=("/odom", "/tf"),
    )
    assert replay.derivation_source == DERIVATION_FIXTURE
    assert replay.missing_topics == ("/tf",)
    # Trajectory is partial because /tf samples weren't present.
    assert replay.trajectory_status == TRAJECTORY_STATUS_PARTIAL
    # No /tf samples were invented.
    assert all(s.source_topic == "/odom" for s in replay.samples)


# ---------------------------------------------------------------------
# Honesty gatekeeper
# ---------------------------------------------------------------------


def test_is_honestly_bag_backed_requires_samples() -> None:
    replay = SpatialReplay(
        run_id="r",
        scenario_id="s",
        mission_id="m",
        evidence_origin="runtime",
        bag_status="bag_backed",
        derivation_source=DERIVATION_BAG_BACKED,
        trajectory_status="missing",
        validation_status="not_executed",
        samples=(),
    )
    assert is_honestly_bag_backed(replay) is False


def test_is_honestly_bag_backed_rejects_fixture() -> None:
    replay = SpatialReplay(
        run_id="r",
        scenario_id="s",
        mission_id="m",
        evidence_origin="fixture",
        bag_status="missing_manifest",
        derivation_source=DERIVATION_FIXTURE,
        trajectory_status=TRAJECTORY_STATUS_COMPLETE,
        validation_status="passed",
        samples=(PoseSample("s0", 0, 0.0, 0.0, 0.0, "/odom", "high"),),
    )
    assert is_honestly_bag_backed(replay) is False


def test_is_honestly_bag_backed_accepts_full_evidence() -> None:
    replay = SpatialReplay(
        run_id="r",
        scenario_id="s",
        mission_id="m",
        evidence_origin="runtime",
        bag_status="bag_backed",
        derivation_source=DERIVATION_BAG_BACKED,
        trajectory_status=TRAJECTORY_STATUS_COMPLETE,
        validation_status="passed",
        samples=(PoseSample("s0", 0, 0.0, 0.0, 0.0, "/odom", "high"),),
    )
    assert is_honestly_bag_backed(replay) is True


# ---------------------------------------------------------------------
# End-to-end builder + reporter
# ---------------------------------------------------------------------


def test_builder_writes_all_artefacts(tmp_path: Path) -> None:
    fixtures_root = tmp_path / "fixtures"
    run_dir = fixtures_root / "rid"
    run_dir.mkdir(parents=True)
    write_pose_samples(
        [PoseSample("s0", 0, 0.0, 0.0, 0.0, "/odom", "high")],
        run_dir / "pose-samples.jsonl",
    )
    replay = build_spatial_replay(
        run_id="rid",
        scenario_id="s",
        mission_id="m",
        evidence_root=None,
        fixtures_root=fixtures_root,
        events=(),
        expected_topics=(),
        generated_at_utc="2026-05-11T18:00:00+00:00",
    )
    validation = validate_spatial_replay(replay)
    out = tmp_path / "out"
    paths = write_spatial_replay_artefacts(replay, validation, out)
    for key, p in paths.items():
        assert p.exists(), f"{key} missing"
    payload = json.loads(paths["spatial_replay_json"].read_text(encoding="utf-8"))
    assert payload["derivation_source"] == DERIVATION_FIXTURE
    md = paths["report_md"].read_text(encoding="utf-8")
    assert "not safety-certified" in md.lower()
    assert "fixture" in md.lower()


def test_unavailable_when_no_samples_and_no_manifest(tmp_path: Path) -> None:
    replay = build_spatial_replay(
        run_id="empty",
        scenario_id="s",
        mission_id="m",
        evidence_root=None,
        fixtures_root=tmp_path,
        events=(),
        expected_topics=(),
    )
    assert replay.derivation_source == DERIVATION_UNAVAILABLE
    assert replay.samples == ()


def test_bag_backed_when_runtime_samples_and_valid_manifest(tmp_path: Path) -> None:
    evidence_root = tmp_path / "evidence"
    run_dir = evidence_root / "runtime" / "r-1"
    bags_dir = run_dir / "bags"
    bags_dir.mkdir(parents=True)
    (bags_dir / "run.mcap").write_bytes(b"")
    (bags_dir / "metadata.yaml").write_text("")
    write_bag_manifest(
        _bag_manifest(bag_paths=("bags/run.mcap",), metadata="bags/metadata.yaml"),
        run_dir / "bag-manifest.json",
    )
    write_pose_samples(
        [
            PoseSample("s0", 0, 0.0, 0.0, 0.0, "/odom", "high"),
            PoseSample("s1", 1_000_000_000, 1.0, 0.0, 0.0, "/odom", "high"),
        ],
        run_dir / "pose-samples.jsonl",
    )

    replay = build_spatial_replay(
        run_id="r-1",
        scenario_id="s-1",
        mission_id="m-1",
        evidence_root=evidence_root,
        fixtures_root=None,
        events=(),
        expected_topics=("/odom",),
    )
    assert replay.derivation_source == DERIVATION_BAG_BACKED
    assert replay.bag_status == "bag_backed"
    assert is_honestly_bag_backed(replay)


def test_bag_backed_demoted_when_bag_path_missing(tmp_path: Path) -> None:
    evidence_root = tmp_path / "evidence"
    run_dir = evidence_root / "runtime" / "r-2"
    run_dir.mkdir(parents=True)
    # No bag file on disk.
    write_bag_manifest(
        _bag_manifest(bag_paths=("bags/missing.mcap",)),
        run_dir / "bag-manifest.json",
    )
    write_pose_samples(
        [PoseSample("s0", 0, 0.0, 0.0, 0.0, "/odom", "high")],
        run_dir / "pose-samples.jsonl",
    )

    replay = build_spatial_replay(
        run_id="r-2",
        scenario_id="s",
        mission_id="m",
        evidence_root=evidence_root,
        fixtures_root=None,
        events=(),
        expected_topics=(),
    )
    # The runtime samples exist, but the bag manifest does not validate
    # (bag path missing on disk), so we should NOT see bag_backed.
    assert replay.derivation_source != DERIVATION_BAG_BACKED
