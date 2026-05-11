#!/usr/bin/env python3
"""Validate a live-runtime evidence directory.

Reads the artefacts written by ``run_live_runtime_pipeline.py`` (or
hand-assembled by an operator) and verifies the Phase 14 honesty
guardrails hold:

* the runner profile is internally consistent;
* the bag manifest classification matches what is on disk;
* the evidence record's mode matches the bag manifest;
* a static or missing-bag run is not labelled ``bag_backed``;
* the maturity baseline (if present) is consistent with the
  evidence record.

Exits non-zero on any guardrail violation. Prints a structured JSON
report when ``--json`` is supplied.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _probe_common import ensure_app_on_path  # noqa: E402

ensure_app_on_path()

from app.live_runtime.bag_manifest import (  # noqa: E402
    BagStatus,
    inspect_bag_directory,
)
from app.live_runtime.evidence_processor import EvidenceMode  # noqa: E402
from app.live_runtime.maturity_baseline import (  # noqa: E402
    MaturityStatus,
    assert_baseline_honest,
    load_maturity_baseline,
)
from app.live_runtime.runner_profile import (  # noqa: E402
    parse_runner_profile,
    validate_runner_profile,
)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--evidence-dir", required=True, type=Path)
    p.add_argument(
        "--maturity-baseline",
        type=Path,
        default=None,
        help="Optional maturity baseline JSON to cross-check",
    )
    p.add_argument("--json", action="store_true")
    return p.parse_args(argv)


def _validate(evidence_dir: Path, baseline_path: Path | None) -> dict:
    findings: list[dict] = []

    def fail(check: str, detail: str) -> None:
        findings.append({"check": check, "status": "failed", "detail": detail})

    def ok(check: str, detail: str = "") -> None:
        findings.append({"check": check, "status": "passed", "detail": detail})

    evidence_path = evidence_dir / "evidence.json"
    if not evidence_path.is_file():
        fail("evidence_json_present", f"missing {evidence_path}")
        return _summarise(findings)
    ok("evidence_json_present")

    evidence = _load_json(evidence_path)

    # Runner profile.
    rp_data = evidence.get("runner_profile")
    if rp_data is None:
        ok("runner_profile_optional", "no runner profile attached")
    else:
        try:
            profile = parse_runner_profile(rp_data)
        except ValueError as exc:
            fail("runner_profile_parse", str(exc))
            return _summarise(findings)
        errors = validate_runner_profile(profile)
        if errors:
            fail("runner_profile_validate", "; ".join(errors))
        else:
            ok("runner_profile_validate")

    # Bag manifest cross-check.
    bm_recorded = evidence.get("bag_manifest", {}) or {}
    bag_dir = bm_recorded.get("bag_dir")
    recorded_status = bm_recorded.get("status")
    if bag_dir and recorded_status != BagStatus.NOT_EXECUTED.value:
        observed = inspect_bag_directory(Path(bag_dir))
        if observed.status.value != recorded_status:
            fail(
                "bag_manifest_matches_disk",
                f"recorded status '{recorded_status}' "
                f"!= observed '{observed.status.value}'",
            )
        else:
            ok("bag_manifest_matches_disk")
    else:
        ok("bag_manifest_matches_disk", "no on-disk bag to cross-check")

    # Honesty guardrails on evidence mode.
    mode = evidence.get("mode")
    if mode == EvidenceMode.BAG_BACKED.value:
        if recorded_status != BagStatus.BAG_BACKED.value:
            fail(
                "bag_backed_requires_bag_backed_manifest",
                f"mode=bag_backed but bag manifest status='{recorded_status}'",
            )
        else:
            ok("bag_backed_requires_bag_backed_manifest")
        if evidence.get("missing_required_topics"):
            fail(
                "bag_backed_has_no_missing_topics",
                f"missing topics: {evidence['missing_required_topics']}",
            )
        else:
            ok("bag_backed_has_no_missing_topics")
    elif mode in (EvidenceMode.STATIC_ONLY.value, EvidenceMode.DRY_RUN.value):
        if recorded_status == BagStatus.BAG_BACKED.value:
            fail(
                "static_or_dry_run_is_not_bag_backed",
                "mode is static/dry-run but bag manifest claims bag_backed",
            )
        else:
            ok("static_or_dry_run_is_not_bag_backed")

    # Maturity baseline cross-check (optional).
    if baseline_path is not None:
        if not baseline_path.is_file():
            fail("maturity_baseline_present", f"missing {baseline_path}")
        else:
            try:
                baseline = load_maturity_baseline(baseline_path)
            except ValueError as exc:
                fail("maturity_baseline_parse", str(exc))
                return _summarise(findings)
            has_bag_backed = mode == EvidenceMode.BAG_BACKED.value
            errors = assert_baseline_honest(
                baseline, has_bag_backed_evidence=has_bag_backed
            )
            if errors:
                fail("maturity_baseline_validate", "; ".join(errors))
            else:
                ok("maturity_baseline_validate")
            if (
                baseline.status is MaturityStatus.ESTABLISHED
                and not has_bag_backed
            ):
                fail(
                    "baseline_consistent_with_evidence",
                    "baseline=established but evidence mode is not bag_backed",
                )
            else:
                ok("baseline_consistent_with_evidence")

    return _summarise(findings)


def _summarise(findings: list[dict]) -> dict:
    failed = [f for f in findings if f["status"] == "failed"]
    return {
        "status": "failed" if failed else "passed",
        "failed_count": len(failed),
        "findings": findings,
    }


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    summary = _validate(args.evidence_dir, args.maturity_baseline)
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"status: {summary['status']}")
        for finding in summary["findings"]:
            print(f"  [{finding['status']}] {finding['check']}: {finding['detail']}")
    return 0 if summary["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
