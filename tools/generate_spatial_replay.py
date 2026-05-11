#!/usr/bin/env python3
"""Generate a spatial-replay artefact for a run.

The CLI is read-only with respect to runtime state — it never
fabricates bag manifests or pose samples. It reads:

* a rehearsal audit directory (for events + the mission plan);
* an optional bag manifest at
  ``<evidence_root>/runtime/<run_id>/bag-manifest.json``;
* an optional runtime pose-samples file (operator-produced);
* an optional fixture pose-samples file in
  ``spatial-replay/fixtures/<run_id>/pose-samples.jsonl``.

It writes the five output artefacts to
``<output_root>/<run_id>/``.

Usage:
    python tools/generate_spatial_replay.py \
        --run-id canonical-fixture \
        --scenario-id warehouse_pickup_route_alpha \
        --mission-id warehouse_pickup_route_alpha \
        --rehearsal mission-rehearsals/audits/warehouse_pickup_route_alpha \
        --fixtures-root spatial-replay/fixtures \
        --output-root spatial-replay/runs
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from _common import ensure_app_on_path

ensure_app_on_path()

from app.spatial_replay import (
    build_spatial_replay,
    run_output_dir,
    validate_spatial_replay,
    write_spatial_replay_artefacts,
)


def _load_events(rehearsal_dir: Path) -> tuple[dict, ...]:
    path = rehearsal_dir / "rehearsal-events.json"
    if not path.exists():
        return ()
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        return ()
    return tuple(e for e in data if isinstance(e, dict))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--scenario-id", required=True)
    parser.add_argument("--mission-id", required=True)
    parser.add_argument(
        "--rehearsal",
        type=Path,
        required=True,
        help="Path to a mission-rehearsals/audits/<id>/ directory.",
    )
    parser.add_argument(
        "--evidence-root",
        type=Path,
        default=None,
        help="Path to <repo>/evidence (for bag-backed runs). Optional.",
    )
    parser.add_argument(
        "--fixtures-root",
        type=Path,
        default=Path("spatial-replay/fixtures"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("spatial-replay/runs"),
    )
    parser.add_argument(
        "--expected-topic",
        action="append",
        default=[],
        help="Repeatable. Pose topics expected to be present.",
    )
    parser.add_argument(
        "--generated-at",
        default="",
        help="Override generated_at timestamp (UTC ISO 8601).",
    )
    args = parser.parse_args(argv)

    events = _load_events(args.rehearsal)
    generated_at = args.generated_at or datetime.now(timezone.utc).isoformat()

    replay = build_spatial_replay(
        run_id=args.run_id,
        scenario_id=args.scenario_id,
        mission_id=args.mission_id,
        evidence_root=args.evidence_root,
        fixtures_root=args.fixtures_root,
        events=events,
        expected_topics=tuple(args.expected_topic),
        generated_at_utc=generated_at,
    )

    validation = validate_spatial_replay(
        replay, expected_topics=tuple(args.expected_topic)
    )

    out_dir = run_output_dir(args.output_root.parent, args.run_id)
    # ``run_output_dir`` expects spatial-replay root; we passed
    # output-root (already the runs/ dir), so compute parent.
    out_dir = args.output_root / args.run_id
    paths = write_spatial_replay_artefacts(replay, validation, out_dir)

    print(f"derivation_source={replay.derivation_source}")
    print(f"bag_status={replay.bag_status}")
    print(f"trajectory_status={replay.trajectory_status}")
    print(f"validation_status={replay.validation_status}")
    print(f"sample_count={len(replay.samples)}")
    print(f"segment_count={len(replay.segments)}")
    for key, p in paths.items():
        print(f"{key}={p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
