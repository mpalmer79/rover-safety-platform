#!/usr/bin/env python3
"""Compare a qualification run to a baseline.

Modes:

* ``capture`` — read an evidence run dir and write a baseline JSON
  suitable for later comparison.
* ``compare`` — read a baseline JSON and a fresh evidence run dir,
  classify each delta, and emit a structured comparison.

The comparator never silently auto-ignores a regression. Every delta
carries a deterministic detail string; severity is one of
``expected_difference``, ``warning``, ``regression``, or
``critical_regression``.

Usage:
    rover_ws/tools/compare_runtime_baseline.py capture <run-dir> --baseline-out <path>
    rover_ws/tools/compare_runtime_baseline.py compare <run-dir> --baseline <path>
                                              [--required-topics t1,t2,...]
                                              [--required-nodes n1,n2,...]
                                              [--required-tf-frames f1,f2,...]
                                              [--out <path>]
                                              [--md <path>]
                                              [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _probe_common import (  # noqa: E402  (sys.path mutated)
    ensure_app_on_path,
    write_json,
)

ensure_app_on_path()

from app.runtime_validation.baselines import (  # noqa: E402
    baseline_from_evidence,
    compare_baseline,
    load_baseline,
    render_comparison_md,
    write_baseline,
)


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    capture = sub.add_parser("capture", help="capture a baseline from an evidence run")
    capture.add_argument("run_dir", type=Path, help="evidence/runtime/<run_id>/")
    capture.add_argument(
        "--baseline-out",
        type=Path,
        required=True,
        help="path to write the baseline JSON",
    )

    compare = sub.add_parser("compare", help="compare a run to a baseline")
    compare.add_argument("run_dir", type=Path)
    compare.add_argument("--baseline", type=Path, required=True)
    compare.add_argument("--required-topics", default="")
    compare.add_argument("--required-nodes", default="")
    compare.add_argument("--required-tf-frames", default="")
    compare.add_argument("--optional-topics", default="")
    compare.add_argument("--optional-nodes", default="")
    compare.add_argument(
        "--out",
        type=Path,
        default=None,
        help="path to write the comparison JSON (default: <run_dir>/baseline-comparison.json)",
    )
    compare.add_argument(
        "--md",
        type=Path,
        default=None,
        help="path to write the comparison Markdown (default: <run_dir>/baseline-comparison.md)",
    )
    compare.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)

    if args.cmd == "capture":
        if not args.run_dir.exists():
            sys.stderr.write(f"run dir does not exist: {args.run_dir}\n")
            return 2
        baseline = baseline_from_evidence(args.run_dir)
        write_baseline(baseline=baseline, path=args.baseline_out)
        sys.stdout.write(
            f"wrote baseline {args.baseline_out} from {args.run_dir}\n"
        )
        return 0

    # compare
    if not args.run_dir.exists():
        sys.stderr.write(f"run dir does not exist: {args.run_dir}\n")
        return 2
    if not args.baseline.exists():
        sys.stderr.write(f"baseline does not exist: {args.baseline}\n")
        return 2
    baseline = load_baseline(args.baseline)
    observed = baseline_from_evidence(args.run_dir)
    comparison = compare_baseline(
        baseline=baseline,
        observed=observed,
        baseline_path=args.baseline,
        observed_path=args.run_dir,
        required_topics=_split_csv(args.required_topics),
        required_nodes=_split_csv(args.required_nodes),
        required_tf_frames=_split_csv(args.required_tf_frames),
        optional_topics=_split_csv(args.optional_topics),
        optional_nodes=_split_csv(args.optional_nodes),
    )
    out_path = args.out or (args.run_dir / "baseline-comparison.json")
    md_path = args.md or (args.run_dir / "baseline-comparison.md")
    write_json(out_path, comparison.as_dict())
    md_path.write_text(render_comparison_md(comparison), encoding="utf-8")

    if args.json:
        json.dump(comparison.as_dict(), sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        counts = comparison.summary_counts()
        print(
            f"baseline-comparison: severity={comparison.severity.value} "
            f"deltas={sum(counts.values())} ({counts})"
        )
        print(f"  json: {out_path}")
        print(f"  md:   {md_path}")
    return 0 if not comparison.has_regression() else 1


if __name__ == "__main__":
    sys.exit(main())
