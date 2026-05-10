#!/usr/bin/env python3
"""Validate a replay review bundle.

Reads the manifest + Foxglove session + markers + report from the
supplied incident directory, re-runs the static validation suite,
and either prints a summary or emits the validation JSON.

Usage:
    rover_ws/tools/validate_replay_review.py
        --incident incidents/<incident_id>
        [--foxglove-layout foxglove/layouts/incident-review-layout.json]
        [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _probe_common import ensure_app_on_path  # noqa: E402

ensure_app_on_path()

from app.replay_review import (  # noqa: E402
    BagIndex,
    FoxgloveSession,
    ReplayMarker,
    ReplayReviewManifest,
    ReplayValidationResult,
    aggregate_status,
    build_foxglove_session,
    validate_replay_review,
)
from app.replay_review.models import (  # noqa: E402
    BagArtifact,
    FoxglovePanelHint,
    ReplayEvidenceOrigin,
    ReplayExecutionStatus,
    ReplayTopic,
)


def _manifest_from_json(payload: dict) -> ReplayReviewManifest:
    return ReplayReviewManifest(
        incident_id=payload.get("incident_id", ""),
        run_id=payload.get("run_id"),
        scenario_id=payload.get("scenario_id"),
        evidence_status=payload.get("evidence_status", ""),
        bag_status=ReplayExecutionStatus(payload.get("bag_status", "missing_bag")),
        bag_indices=tuple(_bag_index_from_json(b) for b in payload.get("bag_indices", [])),
        expected_topics=tuple(
            ReplayTopic(
                name=t.get("name", ""),
                purpose=t.get("purpose", ""),
                required=bool(t.get("required", False)),
            )
            for t in payload.get("expected_topics", [])
        ),
        available_topics=tuple(payload.get("available_topics", [])),
        missing_topics=tuple(payload.get("missing_topics", [])),
        foxglove_layout_path=payload.get("foxglove_layout_path", ""),
        foxglove_session_path=payload.get("foxglove_session_path", ""),
        timeline_marker_count=int(payload.get("timeline_marker_count", 0)),
        review_steps=tuple(payload.get("review_steps", [])),
        known_limitations=tuple(payload.get("known_limitations", [])),
        generated_at_utc=payload.get("generated_at_utc", ""),
    )


def _bag_index_from_json(payload: dict) -> BagIndex:
    artifacts = [
        BagArtifact(
            path=Path(a.get("path", "")),
            kind=a.get("kind", "unknown"),
            size_bytes=int(a.get("size_bytes", 0)),
            notes=a.get("notes", ""),
        )
        for a in payload.get("artifacts", [])
    ]
    metadata_path_raw = payload.get("metadata_path", "")
    return BagIndex(
        bag_root=Path(payload.get("bag_root", ".")),
        artifacts=artifacts,
        metadata_path=Path(metadata_path_raw) if metadata_path_raw else None,
        inventory_topics=tuple(payload.get("inventory_topics", [])),
        message_counts=dict(payload.get("message_counts", {})),
        start_time_ns=payload.get("start_time_ns"),
        end_time_ns=payload.get("end_time_ns"),
        notes=list(payload.get("notes", [])),
    )


def _markers_from_json(records: list) -> list[ReplayMarker]:
    out: list[ReplayMarker] = []
    for r in records:
        try:
            origin = ReplayEvidenceOrigin(r.get("evidence_origin", "unknown"))
        except ValueError:
            origin = ReplayEvidenceOrigin.UNKNOWN
        out.append(
            ReplayMarker(
                marker_id=r.get("marker_id", ""),
                label=r.get("label", ""),
                description=r.get("description", ""),
                timeline_index=int(r.get("timeline_index", 0)),
                relative_time_ms=r.get("relative_time_ms"),
                sim_time_ns=r.get("sim_time_ns"),
                source_event_id=r.get("source_event_id", ""),
                source_file=r.get("source_file", ""),
                confidence=r.get("confidence", "unknown"),
                evidence_origin=origin,
                alignment=r.get("alignment", "exact"),
            )
        )
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--incident", type=Path, required=True)
    parser.add_argument(
        "--foxglove-layout",
        type=Path,
        default=Path("foxglove/layouts/incident-review-layout.json"),
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    manifest_path = args.incident / "replay-review-manifest.json"
    session_path = args.incident / "foxglove-session.json"
    markers_path = args.incident / "replay-markers.json"
    if not manifest_path.exists():
        sys.stderr.write(f"manifest not found: {manifest_path}\n")
        sys.stderr.write("Run build_replay_review_bundle.py first.\n")
        return 2
    manifest = _manifest_from_json(json.loads(manifest_path.read_text()))
    markers = (
        _markers_from_json(json.loads(markers_path.read_text(encoding="utf-8")))
        if markers_path.exists()
        else []
    )
    if session_path.exists():
        sess_payload = json.loads(session_path.read_text(encoding="utf-8"))
        # Build a session value with the same metadata; we don't need
        # to round-trip every field for validation.
        session = build_foxglove_session(
            incident_id=sess_payload.get("incident_id", manifest.incident_id),
            layout_path=sess_payload.get("layout_path", manifest.foxglove_layout_path),
            recommended_data_source=sess_payload.get("recommended_data_source", ""),
            markers=markers,
            known_limitations=tuple(sess_payload.get("known_limitations", [])),
        )
    else:
        session = build_foxglove_session(
            incident_id=manifest.incident_id,
            layout_path=manifest.foxglove_layout_path,
            recommended_data_source="",
            markers=markers,
        )

    results = validate_replay_review(
        incident_dir=args.incident,
        manifest=manifest,
        session=session,
        markers=markers,
        layout_file=args.foxglove_layout,
    )
    status = aggregate_status(manifest=manifest, validations=results)

    payload = {
        "incident_id": manifest.incident_id,
        "aggregate_status": status.value,
        "results": [r.as_dict() for r in results],
    }
    if args.json:
        json.dump(payload, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print(f"validate-replay-review {manifest.incident_id}: {status.value}")
        for r in results:
            print(f"  [{r.status.value}] {r.name}: {r.detail}")
    return 0 if status.value not in {"failed"} else 1


if __name__ == "__main__":
    sys.exit(main())
