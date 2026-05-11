"""Build + serialise reviewer scene-snapshot metadata.

The pipeline reads the canonical artefact registry and the
spatial-replay artefact for one run, and emits a deterministic
description of what a reviewer-grade snapshot could be. No images
are generated; the layer is metadata-only until a real browser /
render harness is wired into a future phase.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from app.artifact_registry import (
    ArtifactRegistry,
    INTEGRITY_PASSED,
    default_registry_path,
    find_record,
    load_registry,
    short_hash,
    verify_artifact,
)

from .models import (
    SNAPSHOT_DISCLAIMER,
    SNAPSHOT_STATUS_BAG_BACKED,
    SNAPSHOT_STATUS_FIXTURE,
    SNAPSHOT_STATUS_NOT_EXECUTED,
    SNAPSHOT_STATUS_UNAVAILABLE,
    SceneSnapshot,
    SceneSnapshotEligibility,
)


def _load_spatial_replay(
    repo_root: Path, run_id: str
) -> Mapping[str, object] | None:
    path = repo_root / "spatial-replay" / "runs" / run_id / "spatial-replay.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def evaluate_eligibility(
    run_id: str,
    *,
    repo_root: Path,
    registry: ArtifactRegistry | None = None,
) -> SceneSnapshotEligibility:
    """Return a deterministic eligibility summary for ``run_id``.

    Eligible-for-bag-backed-snapshot iff:
      * a spatial-replay artefact exists on disk;
      * its ``derivation_source`` is ``bag_backed``;
      * its ``bag_status`` is ``bag_backed``;
      * the artefact registry record exists + ``integrity == passed``.
    """

    if registry is None:
        registry = load_registry(default_registry_path(repo_root))

    record = find_record(registry, run_id) if registry else None
    spatial = _load_spatial_replay(repo_root, run_id)

    missing: list[str] = []
    if spatial is None:
        missing.append(
            f"spatial-replay/runs/{run_id}/spatial-replay.json"
        )
    if record is None:
        missing.append(
            f"spatial-replay/registry/canonical-artifacts.json record for {run_id}"
        )

    derivation = str(spatial.get("derivation_source")) if spatial else ""
    bag_status = str(spatial.get("bag_status")) if spatial else ""
    # Recompute integrity from the bytes on disk so we don't trust a
    # stale value carved into the registry file.
    if record is not None:
        live_integrity, _, _ = verify_artifact(record, artefact_root=repo_root)
        integrity = live_integrity
    else:
        integrity = "missing"

    eligible = (
        spatial is not None
        and record is not None
        and derivation == "bag_backed"
        and bag_status == "bag_backed"
        and integrity == INTEGRITY_PASSED
    )

    if eligible:
        status = SNAPSHOT_STATUS_BAG_BACKED
    elif derivation == "fixture" and integrity == INTEGRITY_PASSED:
        status = SNAPSHOT_STATUS_FIXTURE
    elif spatial is None and record is None:
        status = SNAPSHOT_STATUS_UNAVAILABLE
    else:
        status = SNAPSHOT_STATUS_NOT_EXECUTED

    if status == SNAPSHOT_STATUS_NOT_EXECUTED:
        if derivation != "bag_backed":
            missing.append(
                f"derivation_source = bag_backed (currently {derivation!r})"
            )
        if bag_status != "bag_backed":
            missing.append(
                f"bag_status = bag_backed (currently {bag_status!r})"
            )
        if integrity != INTEGRITY_PASSED:
            missing.append(
                f"registry integrity = passed (currently {integrity!r})"
            )

    notes: tuple[str, ...] = ()
    if status == SNAPSHOT_STATUS_FIXTURE:
        notes = (
            "Fixture-derived run; not eligible for a bag-backed snapshot.",
        )
    elif status == SNAPSHOT_STATUS_UNAVAILABLE:
        notes = ("No spatial-replay or registry record for this run id.",)
    elif status == SNAPSHOT_STATUS_BAG_BACKED:
        notes = (
            "Eligible for a bag-backed reviewer snapshot. "
            "A browser-render harness is required to produce the image.",
        )

    return SceneSnapshotEligibility(
        run_id=run_id,
        status=status,
        eligible_for_bag_backed_snapshot=eligible,
        derivation_source=derivation,
        bag_status=bag_status,
        integrity=integrity,
        missing_inputs=tuple(missing),
        notes=notes,
    )


def build_snapshot_for_run(
    run_id: str,
    *,
    repo_root: Path,
    generated_at_utc: str = "",
) -> SceneSnapshot:
    """Return a :class:`SceneSnapshot` description.

    The snapshot's ``reviewer_export_ready`` is true only when the
    eligibility check passed AND the underlying artefact registry
    record validates.
    """

    registry = load_registry(default_registry_path(repo_root))
    eligibility = evaluate_eligibility(
        run_id, repo_root=repo_root, registry=registry
    )

    record = find_record(registry, run_id) if registry else None
    chain: list[Mapping[str, str]] = []
    if record is not None:
        for f in record.files:
            chain.append(
                {
                    "relative_path": f.relative_path,
                    "sha256_prefix": short_hash(f.expected_hash),
                    "size_bytes": str(f.size_bytes),
                }
            )

    return SceneSnapshot(
        run_id=run_id,
        status=eligibility.status,
        scene_source=(
            "apps/mission-control/src/3d/MissionScene"
            if eligibility.eligible_for_bag_backed_snapshot
            else ""
        ),
        derivation_source=eligibility.derivation_source,
        bag_status=eligibility.bag_status,
        integrity=eligibility.integrity,
        artifact_registry_entry=(
            "spatial-replay/registry/canonical-artifacts.json"
            if record is not None
            else ""
        ),
        spatial_replay_path=(
            f"spatial-replay/runs/{run_id}/spatial-replay.json"
            if eligibility.derivation_source
            else ""
        ),
        artifact_hash_chain=tuple(chain),
        missing_inputs=eligibility.missing_inputs,
        reviewer_export_ready=eligibility.eligible_for_bag_backed_snapshot,
        generated_at_utc=generated_at_utc,
        notes=eligibility.notes,
    )


def snapshot_to_dict(snapshot: SceneSnapshot) -> dict[str, object]:
    return {
        "run_id": snapshot.run_id,
        "status": snapshot.status,
        "scene_source": snapshot.scene_source,
        "derivation_source": snapshot.derivation_source,
        "bag_status": snapshot.bag_status,
        "integrity": snapshot.integrity,
        "artifact_registry_entry": snapshot.artifact_registry_entry,
        "spatial_replay_path": snapshot.spatial_replay_path,
        "artifact_hash_chain": [dict(item) for item in snapshot.artifact_hash_chain],
        "missing_inputs": list(snapshot.missing_inputs),
        "reviewer_export_ready": snapshot.reviewer_export_ready,
        "generated_at_utc": snapshot.generated_at_utc,
        "notes": list(snapshot.notes),
        "disclaimer": SNAPSHOT_DISCLAIMER,
    }


def snapshot_eligibility_to_dict(
    eligibility: SceneSnapshotEligibility,
) -> dict[str, object]:
    return {
        "run_id": eligibility.run_id,
        "status": eligibility.status,
        "eligible_for_bag_backed_snapshot": eligibility.eligible_for_bag_backed_snapshot,
        "derivation_source": eligibility.derivation_source,
        "bag_status": eligibility.bag_status,
        "integrity": eligibility.integrity,
        "missing_inputs": list(eligibility.missing_inputs),
        "notes": list(eligibility.notes),
    }


def write_snapshot_artefacts(
    snapshot: SceneSnapshot, out_dir: Path
) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "snapshot_json": out_dir / f"{snapshot.run_id}.scene-snapshot.json",
        "snapshot_md": out_dir / f"{snapshot.run_id}.scene-snapshot.md",
    }
    paths["snapshot_json"].write_text(
        json.dumps(snapshot_to_dict(snapshot), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    paths["snapshot_md"].write_text(
        render_snapshot_markdown(snapshot), encoding="utf-8"
    )
    return paths


def render_snapshot_markdown(snapshot: SceneSnapshot) -> str:
    lines = [
        f"# Reviewer scene snapshot — `{snapshot.run_id}`",
        "",
        f"- **Status:** `{snapshot.status}`",
        f"- **Derivation source:** `{snapshot.derivation_source or '—'}`",
        f"- **Bag status:** `{snapshot.bag_status or '—'}`",
        f"- **Registry integrity:** `{snapshot.integrity}`",
        f"- **Reviewer export ready:** "
        f"{'yes' if snapshot.reviewer_export_ready else 'no'}",
        "",
        SNAPSHOT_DISCLAIMER,
        "",
    ]
    if snapshot.missing_inputs:
        lines += ["## Missing inputs", ""]
        for m in snapshot.missing_inputs:
            lines.append(f"- {m}")
        lines.append("")
    if snapshot.artifact_hash_chain:
        lines += ["## Artefact hash chain", "", "| file | sha256(16) | size |", "|---|---|---:|"]
        for entry in snapshot.artifact_hash_chain:
            lines.append(
                f"| `{entry['relative_path']}` | `{entry['sha256_prefix']}` | {entry['size_bytes']} B |"
            )
        lines.append("")
    if snapshot.notes:
        lines += ["## Notes", ""]
        for n in snapshot.notes:
            lines.append(f"- {n}")
        lines.append("")
    return "\n".join(lines)


__all__ = [
    "build_snapshot_for_run",
    "evaluate_eligibility",
    "render_snapshot_markdown",
    "snapshot_eligibility_to_dict",
    "snapshot_to_dict",
    "write_snapshot_artefacts",
]
