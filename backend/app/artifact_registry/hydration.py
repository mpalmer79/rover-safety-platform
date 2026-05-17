"""Deterministic hydration of canonical replay artefacts.

The hydration layer rebuilds canonical fixtures by invoking the
spatial-replay builder, then verifies the resulting hashes against
the registry. A drift between expected and computed hashes fails
honestly — the platform never papers over a deterministic
regression.

Hydration is intentionally idempotent: running it twice produces
byte-identical artefacts.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping

from app.spatial_replay import (
    build_spatial_replay,
    validate_spatial_replay,
    write_spatial_replay_artefacts,
)

from .deterministic_hash import hash_file
from .manifest import default_registry_path, load_registry, write_registry
from .models import (
    ARTIFACT_KIND_SPATIAL_REPLAY,
    INTEGRITY_PASSED,
    ArtifactRecord,
    ArtifactRegistry,
    HydrationOutcome,
    HydrationReport,
)
from .validation import aggregate_integrity, verify_artifact


_GENERATED_AT_FOR_FIXTURES: str = "2026-05-11T18:00:00+00:00"
"""Locked timestamp for canonical fixtures. Hydration must produce
byte-identical artefacts every time, which means the
``generated_at`` field cannot drift on each run."""


def _load_events(rehearsal_dir: Path) -> tuple[dict, ...]:
    path = rehearsal_dir / "rehearsal-events.json"
    if not path.exists():
        return ()
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        return ()
    return tuple(e for e in data if isinstance(e, dict))


def _hydrate_spatial_replay_record(
    record: ArtifactRecord,
    *,
    repo_root: Path,
    fixtures_root: Path,
    output_root: Path,
    rehearsal_root: Path,
) -> HydrationOutcome:
    rehearsal_dir = rehearsal_root / record.related_mission_id
    events = _load_events(rehearsal_dir) if rehearsal_dir.exists() else ()

    replay = build_spatial_replay(
        run_id=record.run_id,
        scenario_id=record.related_scenario_id or record.run_id,
        mission_id=record.related_mission_id or record.run_id,
        evidence_root=None,
        fixtures_root=fixtures_root,
        events=events,
        expected_topics=(),
        generated_at_utc=_GENERATED_AT_FOR_FIXTURES,
    )
    validation = validate_spatial_replay(replay)
    out_dir = output_root / record.run_id
    write_spatial_replay_artefacts(replay, validation, out_dir)

    expected_hashes: dict[str, str] = {f.relative_path: f.expected_hash for f in record.files}
    computed_hashes: dict[str, str] = {}
    drift: list[str] = []
    for f in record.files:
        path = repo_root / f.relative_path
        computed = hash_file(path)
        computed_hashes[f.relative_path] = computed
        if not computed:
            drift.append(f"missing after hydration: {f.relative_path}")
            continue
        if f.expected_hash and computed.lower() != f.expected_hash.lower():
            drift.append(
                f"hash drift after hydration: {f.relative_path} "
                f"expected={f.expected_hash[:12]} computed={computed[:12]}"
            )

    integrity, _, verify_drift = verify_artifact(
        record, artefact_root=repo_root
    )
    drift.extend(verify_drift)

    return HydrationOutcome(
        run_id=record.run_id,
        rebuilt=True,
        integrity=integrity,
        expected_hashes=expected_hashes,
        computed_hashes=computed_hashes,
        drift=tuple(drift),
    )


def hydrate_registry(
    *,
    repo_root: Path,
    fixtures_root: Path | None = None,
    output_root: Path | None = None,
    rehearsal_root: Path | None = None,
    write_back: bool = True,
    check_only: bool = False,
) -> HydrationReport:
    """Rebuild every spatial-replay record in the registry.

    The function never raises; integrity drift surfaces in the
    returned :class:`HydrationReport` and is the CI failure signal.

    Phase 20B contract:

    * ``check_only=True`` is a true no-op. The function reads the
      committed bytes on disk, computes their hashes, and compares
      them against the registry's expected hashes. It does NOT
      rebuild artefacts, does NOT write spatial-replay outputs, and
      does NOT rewrite the registry's ``generated_at_utc``.
    * ``check_only=False`` rebuilds every spatial-replay artefact
      and writes the bytes to ``output_root``. The registry is
      refreshed only when ``write_back=True`` and integrity is
      ``passed``.
    """

    repo_root = Path(repo_root)
    fixtures_root = Path(fixtures_root or repo_root / "spatial-replay" / "fixtures")
    output_root = Path(output_root or repo_root / "spatial-replay" / "runs")
    rehearsal_root = Path(rehearsal_root or repo_root / "mission-rehearsals" / "audits")

    reg_path = default_registry_path(repo_root)
    registry = load_registry(reg_path)
    if registry is None:
        return HydrationReport(
            generated_at_utc=datetime.now(timezone.utc).isoformat(),
            registry_path=str(reg_path),
            artefact_root=str(repo_root),
            outcomes=(),
            overall_integrity="missing",
            notes=("registry missing or unparseable",),
        )

    outcomes: list[HydrationOutcome] = []
    for record in registry.records:
        if record.kind != ARTIFACT_KIND_SPATIAL_REPLAY:
            continue
        if check_only:
            outcome = _verify_spatial_replay_record(record, repo_root=repo_root)
        else:
            outcome = _hydrate_spatial_replay_record(
                record,
                repo_root=repo_root,
                fixtures_root=fixtures_root,
                output_root=output_root,
                rehearsal_root=rehearsal_root,
            )
        outcomes.append(outcome)

    overall = aggregate_integrity(o.integrity for o in outcomes)
    report = HydrationReport(
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
        registry_path=str(reg_path),
        artefact_root=str(repo_root),
        outcomes=tuple(outcomes),
        overall_integrity=overall,
    )

    if write_back and not check_only and overall == INTEGRITY_PASSED:
        # Refresh the registry's ``generated_at_utc`` only when
        # hydration passes cleanly. A failing hydration must NOT
        # rewrite the registry - the committed registry remains the
        # authoritative reference.
        registry = ArtifactRegistry(
            generated_at_utc=report.generated_at_utc,
            schema_version=registry.schema_version,
            artefact_root=registry.artefact_root,
            records=registry.records,
            notes=registry.notes,
        )
        write_registry(registry, reg_path)

    return report


def _verify_spatial_replay_record(
    record: ArtifactRecord,
    *,
    repo_root: Path,
) -> HydrationOutcome:
    """Read-only verification of a committed spatial-replay record.

    Computes the hash of each committed file and compares it against
    the registry's expected hash. Never rebuilds, never writes.
    """

    expected_hashes: dict[str, str] = {
        f.relative_path: f.expected_hash for f in record.files
    }
    computed_hashes: dict[str, str] = {}
    drift: list[str] = []
    for f in record.files:
        path = repo_root / f.relative_path
        computed = hash_file(path)
        computed_hashes[f.relative_path] = computed
        if not computed:
            drift.append(f"missing committed file: {f.relative_path}")
            continue
        if f.expected_hash and computed.lower() != f.expected_hash.lower():
            drift.append(
                f"hash drift: {f.relative_path} "
                f"expected={f.expected_hash[:12]} computed={computed[:12]}"
            )

    integrity, _, verify_drift = verify_artifact(record, artefact_root=repo_root)
    drift.extend(verify_drift)

    return HydrationOutcome(
        run_id=record.run_id,
        rebuilt=False,
        integrity=integrity,
        expected_hashes=expected_hashes,
        computed_hashes=computed_hashes,
        drift=tuple(drift),
    )


def hydration_report_to_dict(report: HydrationReport) -> dict:
    return {
        "generated_at_utc": report.generated_at_utc,
        "registry_path": report.registry_path,
        "artefact_root": report.artefact_root,
        "overall_integrity": report.overall_integrity,
        "notes": list(report.notes),
        "outcomes": [
            {
                "run_id": o.run_id,
                "rebuilt": o.rebuilt,
                "integrity": o.integrity,
                "drift": list(o.drift),
                "expected_hashes": dict(o.expected_hashes),
                "computed_hashes": dict(o.computed_hashes),
                "warnings": list(o.warnings),
            }
            for o in report.outcomes
        ],
    }


__all__ = [
    "hydrate_registry",
    "hydration_report_to_dict",
]
