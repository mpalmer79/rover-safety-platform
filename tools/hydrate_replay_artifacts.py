#!/usr/bin/env python3
"""Deterministic hydration of canonical replay artefacts.

Read the canonical artefact registry, regenerate every committed
spatial-replay artefact from its source rehearsal + fixture inputs,
verify the resulting deterministic hashes against the registry, and
emit a Markdown + JSON report.

The CLI is honest:

* it never invents bag-backed evidence;
* it never rewrites the canonical registry when hydration drifts;
* it never bypasses the spatial-replay validator.

A drift between the registry's expected hashes and the bytes
produced by hydration exits non-zero so CI fails honestly.

Usage:

    python tools/hydrate_replay_artifacts.py
    python tools/hydrate_replay_artifacts.py --check-only

"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _common import ensure_app_on_path

ensure_app_on_path()

from app.artifact_registry import (
    INTEGRITY_PASSED,
    default_registry_path,
    hydrate_registry,
    hydration_report_to_dict,
    load_registry,
    render_hydration_markdown,
    render_registry_markdown,
)


def main(argv: list[str] | None = None) -> int:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=repo_root,
        help="Override the inferred repo root.",
    )
    parser.add_argument(
        "--report-md",
        type=Path,
        default=Path("spatial-replay/registry/hydration-report.md"),
        help="Where to write the human-readable hydration report.",
    )
    parser.add_argument(
        "--report-json",
        type=Path,
        default=Path("spatial-replay/registry/hydration-report.json"),
        help="Where to write the machine-readable hydration report.",
    )
    parser.add_argument(
        "--registry-md",
        type=Path,
        default=Path("spatial-replay/registry/canonical-artifacts.md"),
        help="Where to write the human-readable registry summary.",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Verify committed hashes only. Read-only: writes no "
        "files, modifies no reports, leaves no dirty working tree.",
    )
    parser.add_argument(
        "--write-reports",
        action="store_true",
        help="When set alongside --check-only, write the hydration "
        "report + registry summary in addition to verification. By "
        "default --check-only writes nothing.",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    report = hydrate_registry(
        repo_root=repo_root,
        write_back=not args.check_only,
        check_only=args.check_only,
    )

    md_path = (repo_root / args.report_md).resolve() if not args.report_md.is_absolute() else args.report_md
    json_path = (repo_root / args.report_json).resolve() if not args.report_json.is_absolute() else args.report_json
    reg_md_path = (repo_root / args.registry_md).resolve() if not args.registry_md.is_absolute() else args.registry_md

    # Phase 20B: --check-only is a true no-op unless --write-reports
    # is explicitly passed. The default behaviour is read-only.
    should_write_reports = (not args.check_only) or args.write_reports
    if should_write_reports:
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(render_hydration_markdown(report) + "\n", encoding="utf-8")
        json_path.write_text(
            json.dumps(hydration_report_to_dict(report), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        registry = load_registry(default_registry_path(repo_root))
        if registry is not None:
            reg_md_path.write_text(render_registry_markdown(registry) + "\n", encoding="utf-8")
    else:
        registry = load_registry(default_registry_path(repo_root))

    print(f"overall_integrity={report.overall_integrity}")
    print(f"hydration_report={md_path}")
    print(f"hydration_report_json={json_path}")
    if registry is not None:
        print(f"registry_summary={reg_md_path}")
    for outcome in report.outcomes:
        print(f"  {outcome.run_id}: {outcome.integrity}")
        for d in outcome.drift:
            print(f"    drift: {d}")

    return 0 if report.overall_integrity == INTEGRITY_PASSED else 1


if __name__ == "__main__":
    sys.exit(main())
