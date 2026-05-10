"""Replay review bundle orchestrator.

Wires the bag indexer, marker generator, manifest builder, Foxglove
session generator, validator, and reporter into a single pure-logic
call:

    build_replay_review(incident_dir=...) -> ReplayReviewBundle

The orchestrator persists every artefact under ``incident_dir/`` (no
mutation of source evidence, no work outside the incident dir) and
returns a fully-populated bundle. The CLI
``rover_ws/tools/build_replay_review_bundle.py`` is a thin wrapper.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.replay_review.bag_index import (
    candidate_bag_roots,
    index_bag_candidates,
    merge_inventory,
)
from app.replay_review.foxglove_session import build_foxglove_session, write_session
from app.replay_review.manifest import build_manifest, render_manifest_md
from app.replay_review.marker import build_markers
from app.replay_review.models import (
    ReplayReviewBundle,
)
from app.replay_review.reporter import build_report, render_report_md
from app.replay_review.validator import (
    aggregate_status,
    validate_replay_review,
)


_DEFAULT_LAYOUT_PATH = "foxglove/layouts/incident-review-layout.json"
_DEFAULT_DATA_SOURCE = (
    "Local file: select the rosbag2 .mcap (preferred) or .db3 chunk listed in "
    "bag_indices[].artifacts."
)


def build_replay_review(
    *,
    incident_dir: Path,
    runtime_run_dir: Optional[Path] = None,
    runs_root: Optional[Path] = None,
    foxglove_layout_path: str = _DEFAULT_LAYOUT_PATH,
    extra_known_limitations: tuple[str, ...] = (),
) -> ReplayReviewBundle:
    """Compose, persist, and return a :class:`ReplayReviewBundle`."""

    incident_dir = Path(incident_dir)
    incident_path = incident_dir / "incident-report.json"
    if not incident_path.exists():
        raise FileNotFoundError(
            f"incident bundle missing incident-report.json: {incident_path}"
        )
    incident = json.loads(incident_path.read_text(encoding="utf-8"))
    run_id = incident.get("run_id")

    candidates = candidate_bag_roots(
        incident_dir=incident_dir,
        runtime_run_dir=runtime_run_dir,
        runs_root=runs_root,
        run_id=run_id,
    )
    bag_indices = index_bag_candidates(candidates)

    markers = tuple(build_markers(incident=incident))

    foxglove_session_path = "foxglove-session.json"
    manifest = build_manifest(
        incident=incident,
        bag_indices=bag_indices,
        foxglove_layout_path=foxglove_layout_path,
        foxglove_session_path=foxglove_session_path,
        timeline_marker_count=len(markers),
        known_limitations=_compose_known_limitations(extra_known_limitations),
    )

    session = build_foxglove_session(
        incident_id=manifest.incident_id,
        layout_path=foxglove_layout_path,
        recommended_data_source=_DEFAULT_DATA_SOURCE,
        markers=markers,
        known_limitations=manifest.known_limitations,
    )

    layout_file = (
        Path(foxglove_layout_path)
        if Path(foxglove_layout_path).is_absolute()
        else _resolve_relative_layout(incident_dir=incident_dir, rel=foxglove_layout_path)
    )
    validations = tuple(
        validate_replay_review(
            incident_dir=incident_dir,
            manifest=manifest,
            session=session,
            markers=markers,
            layout_file=layout_file,
        )
    )

    replay_execution_status = aggregate_status(
        manifest=manifest, validations=validations
    )
    report = build_report(
        manifest=manifest,
        session=session,
        markers=markers,
        validations=validations,
        replay_execution_status=replay_execution_status,
    )

    # Persist.
    write_session(session, path=incident_dir / foxglove_session_path)
    _write_json(incident_dir / "replay-review-manifest.json", manifest.as_dict())
    (incident_dir / "replay-review.md").write_text(
        render_manifest_md(manifest), encoding="utf-8"
    )
    _write_json(incident_dir / "replay-markers.json", [m.as_dict() for m in markers])
    _write_json(incident_dir / "replay-review-report.json", report.as_dict())
    (incident_dir / "replay-review-report.md").write_text(
        render_report_md(report), encoding="utf-8"
    )

    return ReplayReviewBundle(
        incident_id=manifest.incident_id,
        bundle_dir=incident_dir,
        manifest=manifest,
        report=report,
        foxglove_session=session,
        markers=markers,
    )


def _compose_known_limitations(extra: tuple[str, ...]) -> tuple[str, ...]:
    """Compose the manifest's known_limitations list from the defaults + extras."""

    from app.replay_review.manifest import _DEFAULT_KNOWN_LIMITATIONS  # noqa: E402

    return _DEFAULT_KNOWN_LIMITATIONS + tuple(extra)


def _resolve_relative_layout(*, incident_dir: Path, rel: str) -> Path:
    """Resolve a relative layout path against several plausible bases.

    Order:

    1. ``Path(rel)`` (absolute or cwd-relative);
    2. ``incident_dir.parent.parent / rel`` (the conventional
       ``incidents/<id>/`` -> repo root walk);
    3. the repository root inferred from this module's location.

    The first existing match wins. If none exist the function returns
    the cwd-relative ``Path(rel)`` so the validator can flag the
    missing layout honestly.
    """

    direct = Path(rel)
    if direct.exists():
        return direct
    via_incident = incident_dir.parent.parent / rel
    if via_incident.exists():
        return via_incident
    # Module path: backend/app/replay_review/bundle.py -> repo root
    # is parents[3].
    repo_root = Path(__file__).resolve().parents[3]
    via_repo = repo_root / rel
    if via_repo.exists():
        return via_repo
    return direct


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
