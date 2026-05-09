#!/usr/bin/env python3
"""Generate the traceability matrix as JSON + Markdown.

When run with ``--with-verification``, the tool also drives every
scenario through the verifier and reports per-requirement status
backed by the resulting evidence.

Usage:
    python tools/generate_traceability.py
        [--json-out verification/traceability.json]
        [--md-out docs/TRACEABILITY_MATRIX.md]
        [--with-verification]
        [--evidence-root evidence]
        [--runs-root runs/verify]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _common import ensure_app_on_path

ensure_app_on_path()

from app.verification.scenario_verifier import (
    SCENARIO_EXPECTATIONS,
    verify_scenario,
)
from app.verification.traceability import (
    build_traceability_matrix,
    write_traceability,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json-out",
        type=Path,
        default=Path("verification/traceability.json"),
    )
    parser.add_argument(
        "--md-out",
        type=Path,
        default=Path("docs/TRACEABILITY_MATRIX.md"),
    )
    parser.add_argument(
        "--with-verification",
        action="store_true",
        help="run every scenario through the verifier so the matrix carries live status",
    )
    parser.add_argument(
        "--evidence-root",
        type=Path,
        default=Path("evidence"),
        help="evidence root used for evidence_paths in matrix rows",
    )
    parser.add_argument(
        "--runs-root",
        type=Path,
        default=Path("runs/verify"),
    )
    args = parser.parse_args(argv)

    verifications = []
    if args.with_verification:
        args.runs_root.mkdir(parents=True, exist_ok=True)
        for exp in SCENARIO_EXPECTATIONS:
            verifications.append(verify_scenario(exp, runs_root=args.runs_root))

    matrix = build_traceability_matrix(
        verifications=verifications,
        evidence_root=args.evidence_root,
    )
    write_traceability(matrix, json_path=args.json_out, markdown_path=args.md_out)
    sys.stdout.write(
        f"wrote {args.json_out} and {args.md_out}; overall={matrix.overall_status.value}\n"
    )
    return 0 if matrix.overall_status.value == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
