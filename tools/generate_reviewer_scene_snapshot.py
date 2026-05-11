#!/usr/bin/env python3
"""Generate reviewer scene-snapshot metadata for a run.

The CLI is read-only with respect to runtime state. It:

  * reads the canonical artefact registry,
  * reads the spatial-replay artefact for ``--run-id``,
  * computes deterministic eligibility for a bag-backed snapshot,
  * writes ``<output>/<run_id>.scene-snapshot.json`` and
    ``<output>/<run_id>.scene-snapshot.md``.

The CLI NEVER generates a screenshot. The image rendering pipeline
is a separate operator activity (see
``docs/REVIEWER_SCENE_SNAPSHOT_GUIDE.md``).

Usage:

    python tools/generate_reviewer_scene_snapshot.py \\
        --run-id canonical-fixture
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from _common import ensure_app_on_path

ensure_app_on_path()

from app.scene_snapshot import build_snapshot_for_run, write_snapshot_artefacts


def main(argv: list[str] | None = None) -> int:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--repo-root", type=Path, default=repo_root)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("spatial-replay/snapshots"),
    )
    parser.add_argument(
        "--generated-at",
        default=datetime.now(timezone.utc).isoformat(),
    )
    args = parser.parse_args(argv)

    repo = args.repo_root.resolve()
    snapshot = build_snapshot_for_run(
        args.run_id, repo_root=repo, generated_at_utc=args.generated_at
    )
    out_dir = (
        args.output_root
        if args.output_root.is_absolute()
        else repo / args.output_root
    )
    paths = write_snapshot_artefacts(snapshot, out_dir)

    print(f"status={snapshot.status}")
    print(f"reviewer_export_ready={snapshot.reviewer_export_ready}")
    for k, p in paths.items():
        print(f"{k}={p}")
    for m in snapshot.missing_inputs:
        print(f"  missing: {m}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
