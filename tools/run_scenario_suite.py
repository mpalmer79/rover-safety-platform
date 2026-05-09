#!/usr/bin/env python3
"""Run the Phase 1C scenario validation suite.

Executes the seven required scenarios end-to-end through the
deterministic engine, validates each run directory, and asserts the
expected final state and fired faults. Exits with a non-zero status if
any scenario fails.

Usage:
    python tools/run_scenario_suite.py [<runs_root>] [--json]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _common import ensure_app_on_path

ensure_app_on_path()

from app.validation.scenario_suite import run_scenario_suite


def _print_human(suite_result, runs_root: Path) -> None:
    print(f"Scenario suite results (runs_root={runs_root})")
    print()
    width = max(len(o.case.scenario_file) for o in suite_result.outcomes)
    for outcome in suite_result.outcomes:
        status = "OK" if outcome.ok else "FAIL"
        print(
            f"[{status:4s}] {outcome.case.scenario_file:<{width}}  "
            f"final={outcome.final_state.value:<18s} "
            f"transitions={outcome.transitions}  "
            f"fired={','.join(outcome.fired_faults) or '-'}"
        )
        if not outcome.ok:
            for err in outcome.errors:
                print(f"        ! {err}")
    print()
    if suite_result.ok:
        print("All scenarios passed.")
    else:
        print(f"{suite_result.failure_count} scenario(s) failed.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "runs_root",
        nargs="?",
        type=Path,
        default=Path("runs/scenario_suite"),
        help="directory under which scenario run folders are written",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args(argv)
    result = run_scenario_suite(runs_root=args.runs_root)
    if args.json:
        import json

        json.dump(result.as_dict(), sys.stdout, indent=2, sort_keys=True, default=str)
        sys.stdout.write("\n")
    else:
        _print_human(result, args.runs_root)
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
