#!/usr/bin/env python3
"""Run every Phase 1C / Phase 2 scenario and produce evidence artefacts.

The default invocation runs the full scenario set against the
deterministic engine, writes one evidence directory per scenario
under ``evidence/scenarios/<scenario_id>/``, and emits a structured
JSON manifest to stdout (or to ``--output``).

Usage:
    python tools/generate_evidence.py [--evidence-root evidence] [--runs-root runs/verify]
                                      [--scenario <id> ...] [--output evidence/manifest.json]
                                      [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _common import ensure_app_on_path

ensure_app_on_path()

from app.verification.evidence import write_evidence
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
        "--evidence-root",
        type=Path,
        default=Path("evidence"),
        help="root directory under which evidence/<scenario_id>/ is written",
    )
    parser.add_argument(
        "--runs-root",
        type=Path,
        default=Path("runs/verify"),
        help="root directory under which scenario run folders are written",
    )
    parser.add_argument(
        "--scenario",
        action="append",
        help="run only the named scenario (may be passed multiple times)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="path to write the manifest JSON (default: stdout when --json)",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON manifest")
    args = parser.parse_args(argv)

    expectations = _select(args.scenario)
    args.evidence_root.mkdir(parents=True, exist_ok=True)
    args.runs_root.mkdir(parents=True, exist_ok=True)

    manifest = {
        "evidence_root": str(args.evidence_root),
        "runs_root": str(args.runs_root),
        "scenarios": [],
    }
    overall_ok = True
    for exp in expectations:
        verification = verify_scenario(exp, runs_root=args.runs_root)
        evidence = write_evidence(verification, evidence_root=args.evidence_root)
        ok = verification.status.value == "passed"
        overall_ok = overall_ok and ok
        manifest["scenarios"].append(
            {
                "scenario_id": exp.scenario_id,
                "status": verification.status.value,
                "summary": evidence.summary,
                "artefacts": [a.kind for a in evidence.artefacts],
                "evidence_dir": str(args.evidence_root / "scenarios" / exp.scenario_id),
            }
        )

    payload = json.dumps(manifest, indent=2, sort_keys=True)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    if args.json or args.output is None:
        sys.stdout.write(payload + "\n")
    return 0 if overall_ok else 1


if __name__ == "__main__":
    sys.exit(main())
