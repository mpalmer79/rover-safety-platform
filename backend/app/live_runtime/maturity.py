"""Aggregate live runs into a maturity report.

The platform is **not safety-certified**. The maturity report is a
read-only rollup over ``evidence/runtime/`` plus the downstream
artefacts the live pipeline integrates with (incident
reconstruction, replay review, replay analytics, programme review,
reviewer export). Every count is derived from on-disk files;
nothing is synthesised.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Mapping

from .bag_manifest import bag_manifest_is_bag_backed, load_bag_manifest
from .models import (
    BAG_STATUS_BAG_BACKED,
    BAG_STATUS_INVALID,
    BAG_STATUS_MISSING_BAG,
    BAG_STATUS_NOT_EXECUTED,
    BAG_STATUS_PARTIAL,
    LIVE_RUN_STATUS_NOT_EXECUTED,
    LIVE_RUN_STATUSES,
    LiveRuntimeMaturityCounters,
    LiveRuntimeMaturityReport,
    QUALIFICATION_STATUS_NOT_QUALIFIED,
    QUALIFICATION_STATUS_QUALIFIED,
    QUALIFICATION_STATUS_UNKNOWN,
)
from .runner_profile import load_runner_profile, runner_supports_live_execution


def _safe_load(path: Path) -> dict | None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    if not text.strip():
        return None
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _list_run_dirs(evidence_root: Path) -> list[Path]:
    if not evidence_root.is_dir():
        return []
    return sorted(p for p in evidence_root.iterdir() if p.is_dir())


def _integration_status(root: Path, *names: str) -> str:
    for name in names:
        if (root / name).exists():
            return "integrated"
    return "not_started"


def aggregate_maturity(
    *,
    evidence_root: Path,
    incidents_root: Path | None = None,
    replay_analytics_root: Path | None = None,
    programme_review_root: Path | None = None,
    reviewer_export_root: Path | None = None,
    generated_at_utc: str,
) -> LiveRuntimeMaturityReport:
    evidence_root = Path(evidence_root)
    run_dirs = _list_run_dirs(evidence_root)

    runs_by_status: Counter[str] = Counter()
    bag_counts: Counter[str] = Counter()
    scenario_counts: Counter[str] = Counter()
    topic_counts: Counter[str] = Counter()
    latest_run_id = ""
    latest_run_status = ""
    latest_runner_profile_path: Path | None = None

    for run_dir in run_dirs:
        summary = _safe_load(run_dir / "live-run-summary.json") or {}
        bag = load_bag_manifest(run_dir / "bag-manifest.json")
        status = str(summary.get("status", "") or LIVE_RUN_STATUS_NOT_EXECUTED)
        if status not in LIVE_RUN_STATUSES:
            status = LIVE_RUN_STATUS_NOT_EXECUTED
        runs_by_status[status] += 1
        scenarios = list(summary.get("scenario_ids", []) or [])
        for sid in scenarios:
            scenario_counts[str(sid)] += 1
        if bag is None:
            bag_counts[BAG_STATUS_NOT_EXECUTED] += 1
        else:
            if bag.bag_status == BAG_STATUS_BAG_BACKED and not bag_manifest_is_bag_backed(
                bag
            ):
                bag_counts[BAG_STATUS_INVALID] += 1
            else:
                bag_counts[bag.bag_status] += 1
            for t in bag.topic_inventory:
                topic_counts[str(t)] += 1
        latest_run_id = run_dir.name
        latest_run_status = status
        latest_runner_profile_path = run_dir / "runner-profile.json"

    runner_status = QUALIFICATION_STATUS_UNKNOWN
    if latest_runner_profile_path is not None and latest_runner_profile_path.exists():
        prof = load_runner_profile(latest_runner_profile_path)
        if prof is not None:
            if runner_supports_live_execution(prof):
                runner_status = QUALIFICATION_STATUS_QUALIFIED
            else:
                runner_status = QUALIFICATION_STATUS_NOT_QUALIFIED

    counters = LiveRuntimeMaturityCounters(
        bag_backed=bag_counts.get(BAG_STATUS_BAG_BACKED, 0),
        missing_bag=bag_counts.get(BAG_STATUS_MISSING_BAG, 0),
        partial=bag_counts.get(BAG_STATUS_PARTIAL, 0),
        not_executed=bag_counts.get(BAG_STATUS_NOT_EXECUTED, 0),
        invalid=bag_counts.get(BAG_STATUS_INVALID, 0),
    )

    review_status = _integration_status(
        Path(incidents_root) if incidents_root else Path("/__missing__"),
        "replay-review-report.json",
    )
    analytics_status = _integration_status(
        Path(replay_analytics_root) if replay_analytics_root else Path("/__missing__"),
        "replay-analytics-report.json",
    )
    programme_status = _integration_status(
        Path(programme_review_root) if programme_review_root else Path("/__missing__"),
        "programme-review.json",
    )

    known_limitations: list[str] = []
    if counters.bag_backed == 0:
        known_limitations.append(
            "no bag-backed evidence on disk; downstream replay review and "
            "analytics still consume canonical fixtures"
        )
    if runs_by_status.get(LIVE_RUN_STATUS_NOT_EXECUTED, 0) > 0:
        known_limitations.append(
            f"{runs_by_status[LIVE_RUN_STATUS_NOT_EXECUTED]} live runs are "
            "marked not_executed (honest fall-back)"
        )
    if runner_status != QUALIFICATION_STATUS_QUALIFIED:
        known_limitations.append(
            "runner profile does not currently certify Jazzy + Gazebo + rosbag2"
        )

    next_actions: list[str] = []
    if runner_status != QUALIFICATION_STATUS_QUALIFIED:
        next_actions.append("provision a self-hosted Jazzy + Gazebo runner")
    if counters.bag_backed == 0:
        next_actions.append(
            "execute live-runtime-evidence.yml on a self-hosted runner to "
            "produce bag-backed artefacts"
        )
    next_actions.append(
        "feed bag-backed evidence into incident reconstruction and replay "
        "analytics so programme review picks up live trends"
    )

    return LiveRuntimeMaturityReport(
        generated_at_utc=generated_at_utc,
        evidence_root=str(evidence_root),
        runs_total=len(run_dirs),
        runs_by_status=dict(runs_by_status),
        bag_counters=counters,
        required_topic_coverage=dict(topic_counts),
        scenario_coverage=dict(scenario_counts),
        runner_status=runner_status,
        latest_run_id=latest_run_id,
        latest_run_status=latest_run_status,
        replay_review_integration=review_status,
        analytics_integration=analytics_status,
        programme_review_integration=programme_status,
        known_limitations=tuple(known_limitations),
        next_actions=tuple(next_actions),
    )


__all__ = [
    "aggregate_maturity",
]
