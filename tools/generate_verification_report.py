#!/usr/bin/env python3
"""Run every scenario through the verifier and write the report.

Usage:
    python tools/generate_verification_report.py
        [--md-out docs/SCENARIO_VERIFICATION_REPORT.md]
        [--json-out verification/verification_report.json]
        [--runs-root runs/verify]
        [--evidence-root evidence]
        [--scenario <id> ...]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _common import ensure_app_on_path

ensure_app_on_path()

from app.verification.evidence import write_evidence
from app.verification.report_generator import (
    VerificationReport,
    render_scenario_verification_report,
)
from app.verification.scenario_verifier import (
    SCENARIO_EXPECTATIONS,
    ScenarioExpectation,
    verify_scenario,
)


def _select(scenarios: list[str] | None) -> list[ScenarioExpectation]:
    if not scenarios:
        return list(SCENARIO_EXPECTATIONS)
    by_id = {e.scenario_id: e for e in SCENARIO_EXPECTATIONS}
    out: list[ScenarioExpectation] = []
    for sid in scenarios:
        if sid not in by_id:
            sys.stderr.write(f"unknown scenario: {sid}\n")
            sys.exit(2)
        out.append(by_id[sid])
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--md-out",
        type=Path,
        default=Path("docs/SCENARIO_VERIFICATION_REPORT.md"),
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=Path("verification/verification_report.json"),
    )
    parser.add_argument(
        "--runs-root",
        type=Path,
        default=Path("runs/verify"),
    )
    parser.add_argument(
        "--evidence-root",
        type=Path,
        default=Path("evidence"),
    )
    parser.add_argument(
        "--scenario",
        action="append",
        help="run only the named scenario(s)",
    )
    parser.add_argument(
        "--no-evidence",
        action="store_true",
        help="skip writing per-scenario evidence directories",
    )
    args = parser.parse_args(argv)

    expectations = _select(args.scenario)
    args.runs_root.mkdir(parents=True, exist_ok=True)

    verifications = []
    for exp in expectations:
        v = verify_scenario(exp, runs_root=args.runs_root)
        verifications.append(v)
        if not args.no_evidence:
            args.evidence_root.mkdir(parents=True, exist_ok=True)
            write_evidence(v, evidence_root=args.evidence_root)

    md = render_scenario_verification_report(verifications)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.write_text(md, encoding="utf-8")

    report = VerificationReport(
        verifications=tuple(verifications),
        generated_at_utc="",  # placeholder; reports already include timestamp
    )
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    payload = report.to_dict()
    args.json_out.write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )

    sys.stdout.write(
        f"wrote {args.md_out} and {args.json_out}; overall={report.overall_status.value}\n"
    )
    return 0 if report.overall_status.value == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
