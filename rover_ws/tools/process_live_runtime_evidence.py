#!/usr/bin/env python3
"""Process raw live-runtime evidence into the canonical evidence record.

Given a runner profile, an optional scenario plan, and an optional
bag directory, this tool constructs the canonical
:class:`LiveRuntimeEvidence` record, writes the evidence files, and
optionally promotes the maturity baseline. It is also the chokepoint
that callers (CI, the pipeline, an operator) use to apply the
honesty guardrails: this tool will refuse to label evidence as
``bag_backed`` unless the bag manifest supports it.

Usage::

    rover_ws/tools/process_live_runtime_evidence.py \
        --runner-profile live-runtime/runner-profile.local.json \
        --scenario-plan live-runtime/scenario-plans/smoke-live-runtime.yaml \
        --bag-dir evidence/runtime/<run_id>/bag \
        --output evidence/runtime/<run_id> \
        --run-id <run_id> \
        [--dry-run | --static-check-only] \
        [--promote-baseline path/to/maturity-baseline.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from _probe_common import ensure_app_on_path  # noqa: E402

ensure_app_on_path()

from app.live_runtime.evidence_processor import (  # noqa: E402
    EvidenceMode,
    LiveRuntimeEvidence,
    process_evidence,
    write_evidence,
)
from app.live_runtime.maturity_baseline import (  # noqa: E402
    MaturityBaseline,
    MaturityStatus,
    new_not_established_baseline,
    load_maturity_baseline,
    promote_baseline,
)
from app.live_runtime.runner_profile import (  # noqa: E402
    RunnerProfile,
    load_runner_profile,
    validate_runner_profile,
)
from app.live_runtime.scenario_plan import (  # noqa: E402
    LiveScenarioPlan,
    load_scenario_plan,
    validate_scenario_plan,
)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--runner-profile", type=Path, default=None)
    p.add_argument("--scenario-plan", type=Path, default=None)
    p.add_argument("--bag-dir", type=Path, default=None)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--run-id", default=None)
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--static-check-only", action="store_true")
    p.add_argument("--promote-baseline", type=Path, default=None)
    p.add_argument("--json", action="store_true")
    return p.parse_args(argv)


def _load_runner(path: Path | None) -> RunnerProfile | None:
    if path is None:
        return None
    return load_runner_profile(path)


def _load_plan(path: Path | None) -> LiveScenarioPlan | None:
    if path is None:
        return None
    return load_scenario_plan(path)


def _resolve_run_id(explicit: str | None, output: Path) -> str:
    if explicit:
        return explicit
    if output.name and output.name not in (".", ""):
        return output.name
    return "live-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _maybe_promote_baseline(
    evidence: LiveRuntimeEvidence, baseline_path: Path
) -> tuple[MaturityBaseline, str]:
    """Promote the baseline if the evidence is genuinely bag-backed.

    Returns the (possibly unchanged) baseline plus a human-readable
    reason. The function never promotes a baseline based on a static
    or dry-run record.
    """

    if baseline_path.is_file():
        previous = load_maturity_baseline(baseline_path)
    else:
        previous = new_not_established_baseline()

    if evidence.mode is not EvidenceMode.BAG_BACKED:
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        baseline_path.write_text(
            json.dumps(previous.as_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return (
            previous,
            f"baseline left unchanged: evidence mode is '{evidence.mode.value}'",
        )

    new_baseline = promote_baseline(
        previous,
        run_id=evidence.run_id,
        bag_dir=evidence.bag_manifest.bag_dir,
        runner_id=(
            evidence.runner_profile.runner_id if evidence.runner_profile else None
        ),
        scenario_plan_id=evidence.scenario_plan_id,
        captured_at=evidence.generated_at,
    )
    baseline_path.parent.mkdir(parents=True, exist_ok=True)
    baseline_path.write_text(
        json.dumps(new_baseline.as_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return new_baseline, "baseline promoted to 'established' from bag-backed run"


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])

    runner = _load_runner(args.runner_profile)
    if runner is not None:
        errors = validate_runner_profile(runner)
        if errors:
            print("runner profile validation failed:", file=sys.stderr)
            for err in errors:
                print(f"  - {err}", file=sys.stderr)
            return 2

    plan = _load_plan(args.scenario_plan)
    if plan is not None:
        plan_errors = validate_scenario_plan(plan)
        if plan_errors:
            print("scenario plan validation failed:", file=sys.stderr)
            for err in plan_errors:
                print(f"  - {err}", file=sys.stderr)
            return 2

    run_id = _resolve_run_id(args.run_id, args.output)

    evidence = process_evidence(
        run_id=run_id,
        runner_profile=runner,
        scenario_plan=plan,
        bag_dir=args.bag_dir,
        dry_run=args.dry_run,
        static_only=args.static_check_only,
    )

    paths = write_evidence(evidence, args.output)
    promotion_msg = None
    if args.promote_baseline is not None:
        _, promotion_msg = _maybe_promote_baseline(evidence, args.promote_baseline)

    if args.json:
        print(
            json.dumps(
                {
                    "run_id": evidence.run_id,
                    "mode": evidence.mode.value,
                    "status": evidence.status.value,
                    "reason": evidence.reason,
                    "paths": paths,
                    "baseline_promotion": promotion_msg,
                    "is_bag_backed": evidence.is_bag_backed,
                },
                indent=2,
            )
        )
    else:
        print(f"run_id: {evidence.run_id}")
        print(f"mode: {evidence.mode.value}")
        print(f"status: {evidence.status.value}")
        print(f"reason: {evidence.reason}")
        for label, p in paths.items():
            print(f"  wrote {label}: {p}")
        if promotion_msg:
            print(f"  baseline: {promotion_msg}")

    if evidence.status.value == "failed":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
