#!/usr/bin/env python3
"""Analyse the reliability impact of a set of source changes.

Reads a change inventory (from ``git diff``, an explicit
``--changed-files`` list, or the working tree) plus the current
replay analytics outputs, compares against a pinned baseline,
classifies subsystem / requirement / evidence impacts, assesses
risk, and writes the resulting reliability-impact bundle.

The CLI is deterministic: given the same inputs it produces
byte-identical artefacts (apart from the ``generated_at_utc`` stamp).
It never fails for missing live runtime evidence on a github-hosted
runner — the CI gate is informational; the documented failure
conditions live in the gate module.

Usage:
    rover_ws/tools/analyze_source_impact.py
        [--base-ref <ref>] [--head-ref <ref>]
        [--changed-files path1,path2,... | --changed-files-file path]
        [--analytics-current incidents/analytics/replay-quality-index.json]
        [--analytics-current-report incidents/analytics/replay-analytics-report.json]
        [--baseline-root reliability-baselines]
        [--output reliability-impact/]
        [--write-baseline]
        [--fixture]
        [--traceability-passed] [--traceability-failed]
        [--tests-passed] [--tests-failed]
        [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from _probe_common import ensure_app_on_path  # noqa: E402

ensure_app_on_path()

from app.reliability_impact import (  # noqa: E402
    build_report,
    collect_source_change,
    resolve_baseline,
    write_baseline,
    write_report_files,
)


def _parse_changed_files(
    value: Optional[str], file_value: Optional[Path]
) -> Optional[list[str]]:
    parts: list[str] = []
    if value:
        parts.extend(s for s in value.replace(",", "\n").splitlines() if s.strip())
    if file_value is not None and file_value.exists():
        parts.extend(
            s.strip()
            for s in file_value.read_text(encoding="utf-8").splitlines()
            if s.strip()
        )
    if not parts:
        return None
    return parts


def _resolve_bool_flag(passed: bool, failed: bool) -> Optional[bool]:
    if passed and not failed:
        return True
    if failed and not passed:
        return False
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-ref", type=str, default=None)
    parser.add_argument("--head-ref", type=str, default=None)
    parser.add_argument(
        "--changed-files",
        type=str,
        default=None,
        help="comma- or newline-separated list of changed files",
    )
    parser.add_argument(
        "--changed-files-file",
        type=Path,
        default=None,
        help="path to a file with one changed file per line",
    )
    parser.add_argument(
        "--analytics-current",
        type=Path,
        default=Path("incidents/analytics/replay-quality-index.json"),
    )
    parser.add_argument(
        "--analytics-current-report",
        type=Path,
        default=Path("incidents/analytics/replay-analytics-report.json"),
    )
    parser.add_argument(
        "--baseline-root",
        type=Path,
        default=Path("reliability-baselines"),
    )
    parser.add_argument(
        "--baseline-quality-index", type=Path, default=None
    )
    parser.add_argument(
        "--baseline-analytics-report", type=Path, default=None
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reliability-impact"),
        help="bundle directory",
    )
    parser.add_argument(
        "--write-baseline",
        action="store_true",
        help=(
            "copy the current analytics outputs into the baseline "
            "directory after the analysis runs"
        ),
    )
    parser.add_argument("--fixture", action="store_true")
    parser.add_argument("--traceability-passed", action="store_true")
    parser.add_argument("--traceability-failed", action="store_true")
    parser.add_argument("--tests-passed", action="store_true")
    parser.add_argument("--tests-failed", action="store_true")
    parser.add_argument(
        "--ci-github-hosted",
        action="store_true",
        help="force the gate to treat this run as github-hosted",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    changed_files = _parse_changed_files(
        args.changed_files, args.changed_files_file
    )
    source_change = collect_source_change(
        base_ref=args.base_ref,
        head_ref=args.head_ref,
        changed_files=changed_files,
        fixture_mode=args.fixture,
    )

    baseline = resolve_baseline(
        quality_index=args.baseline_quality_index,
        analytics_report=args.baseline_analytics_report,
        baseline_root=args.baseline_root,
    )

    is_github_hosted = True if args.ci_github_hosted else None

    report = build_report(
        source_change=source_change,
        baseline=baseline,
        current_quality_index=(
            args.analytics_current if args.analytics_current.exists() else None
        ),
        current_analytics_report=(
            args.analytics_current_report
            if args.analytics_current_report.exists()
            else None
        ),
        traceability_passed=_resolve_bool_flag(
            args.traceability_passed, args.traceability_failed
        ),
        tests_passed=_resolve_bool_flag(args.tests_passed, args.tests_failed),
        is_github_hosted=is_github_hosted,
        fixture_mode=args.fixture,
    )

    write_report_files(report, out_dir=args.output)

    if args.write_baseline:
        write_baseline(
            quality_index_source=args.analytics_current,
            analytics_report_source=args.analytics_current_report,
            baseline_root=args.baseline_root,
        )

    if args.json:
        json.dump(report.as_dict(), sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        print(
            f"reliability-impact: gate={report.gate_decision.status.value} "
            f"risk={report.assessment.overall_risk.value} "
            f"delta={report.analytics_delta.severity.value} "
            f"files={len(report.source_change.changed_files)}"
        )
        print(f"  output: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
