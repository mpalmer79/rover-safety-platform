#!/usr/bin/env python3
"""Live-runtime evidence validator (Phase 13).

Validates a single ``evidence/runtime/<run_id>/`` bundle.

Checks:
  * required files exist (metadata, runner-profile, live-run-summary,
    bag-manifest, qualification-summary, known-limitations);
  * the bag manifest is honest (bag_backed requires real artefacts;
    not_executed requires a structured reason; unknown bag_status
    is a hard fail);
  * static fixtures cannot masquerade as bag-backed.

Exits 0 if every check passes; 1 otherwise. Always honest: this
tool never upgrades a status.

Usage:
    rover_ws/tools/validate_live_runtime_evidence.py
        --bundle evidence/runtime/<run_id>
        [--required-topic <topic> ...]
        [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _probe_common import ensure_app_on_path  # noqa: E402

ensure_app_on_path()

from app.live_runtime import (  # noqa: E402
    REQUIRED_EVIDENCE_FILES,
    bag_manifest_is_bag_backed,
    evidence_bundle_missing_files,
    load_bag_manifest,
    validate_bag_manifest,
)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--required-topic", action="append", default=None)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def validate_bundle(
    bundle_dir: Path, *, required_topics: tuple[str, ...] = ()
) -> tuple[bool, list[str], dict]:
    bundle_dir = Path(bundle_dir)
    failures: list[str] = []

    if not bundle_dir.is_dir():
        return False, [f"bundle directory missing: {bundle_dir}"], {}

    missing = evidence_bundle_missing_files(bundle_dir)
    for name in missing:
        failures.append(f"missing required file: {name}")

    bag_path = bundle_dir / "bag-manifest.json"
    manifest = load_bag_manifest(bag_path) if bag_path.exists() else None
    bag_warnings = validate_bag_manifest(
        manifest, bundle_root=bundle_dir, required_topics=tuple(required_topics)
    )
    for w in bag_warnings:
        failures.append(f"bag manifest: {w}")

    # Cross-check: static-only bundles can never be bag_backed.
    if manifest is not None:
        if manifest.bag_status == "bag_backed" and not bag_manifest_is_bag_backed(
            manifest
        ):
            failures.append(
                "bag manifest claims bag_backed but lacks real artefact paths"
            )

    summary = {
        "bundle_dir": str(bundle_dir),
        "required_files_present": [
            name for name in REQUIRED_EVIDENCE_FILES if (bundle_dir / name).exists()
        ],
        "missing_required_files": list(missing),
        "bag_status": getattr(manifest, "bag_status", None),
        "bag_warnings": list(bag_warnings),
        "passed": not failures,
        "failures": failures,
    }
    return not failures, failures, summary


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(list(argv) if argv is not None else sys.argv[1:])
    ok, failures, summary = validate_bundle(
        args.bundle, required_topics=tuple(args.required_topic or ())
    )
    if args.json:
        json.dump(summary, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        status = "OK" if ok else "FAILED"
        print(f"[{status}] {args.bundle}")
        for f in failures:
            print(f"  - {f}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
