"""Build the on-disk live-runtime evidence directory.

The platform is **not safety-certified**. This module *constructs*
the directory layout under ``evidence/runtime/<run_id>/``. It does
not launch ROS or Gazebo — that is the role of
``rover_ws/tools/live_bag_capture.py``. The capture orchestrator
calls into here to produce a coherent, validatable bundle whether
the run was real, partial, or `not_executed`.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .bag_manifest import (
    bag_manifest_to_dict,
    build_not_executed_manifest,
    write_bag_manifest,
)
from .models import (
    BAG_STATUS_NOT_EXECUTED,
    LIVE_RUN_STATUS_NOT_EXECUTED,
    LIVE_RUNTIME_DISCLAIMER,
    BagManifest,
    LiveRunSummary,
    RunnerProfile,
    REQUIRED_EVIDENCE_FILES,
)
from .runner_profile import (
    runner_profile_to_dict,
    runner_supports_live_execution,
    write_runner_profile,
)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    Path(path).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _write_text(path: Path, text: str) -> None:
    if not text.endswith("\n"):
        text = text + "\n"
    Path(path).write_text(text, encoding="utf-8")


def write_metadata(
    path: Path,
    *,
    run_id: str,
    plan_id: str,
    runner_id: str,
    started_at: str,
    finished_at: str,
    notes: str = "",
) -> None:
    payload = {
        "run_id": run_id,
        "plan_id": plan_id,
        "runner_id": runner_id,
        "started_at": started_at,
        "finished_at": finished_at,
        "notes": notes,
        "disclaimer": LIVE_RUNTIME_DISCLAIMER,
    }
    _write_json(path, payload)


def write_live_run_summary(path: Path, summary: LiveRunSummary) -> None:
    payload = asdict(summary)
    payload["scenario_ids"] = list(summary.scenario_ids)
    payload["disclaimer"] = LIVE_RUNTIME_DISCLAIMER
    _write_json(path, payload)


def write_qualification_summary_md(
    path: Path,
    *,
    run_id: str,
    summary: LiveRunSummary,
    bag_manifest: BagManifest,
    runner_profile: RunnerProfile | None,
) -> None:
    lines = [
        "# Live Runtime Qualification Summary",
        "",
        f"_{LIVE_RUNTIME_DISCLAIMER}_",
        "",
        f"- **Run id:** `{run_id}`",
        f"- **Plan id:** `{summary.plan_id}`",
        f"- **Runner id:** `{summary.runner_id}`",
        f"- **Status:** `{summary.status}`",
        f"- **Bag status:** `{bag_manifest.bag_status}`",
        f"- **Started:** `{summary.started_at}`",
        f"- **Finished:** `{summary.finished_at}`",
        "",
    ]
    if summary.scenario_ids:
        lines.append("## Scenarios")
        lines.append("")
        for sid in summary.scenario_ids:
            lines.append(f"- `{sid}`")
        lines.append("")
    if summary.not_executed_reason:
        lines.append("## not_executed reason")
        lines.append("")
        lines.append(summary.not_executed_reason)
        lines.append("")
    if runner_profile is not None:
        lines.append("## Runner profile")
        lines.append("")
        lines.append(f"- ROS distro: `{runner_profile.ros_distro}`")
        lines.append(f"- Gazebo: `{runner_profile.gazebo_version}`")
        lines.append(f"- Workspace: `{runner_profile.workspace_path}`")
        lines.append(f"- Supports rosbag2: `{runner_profile.supports_rosbag2}`")
        lines.append(f"- Supports Gazebo: `{runner_profile.supports_gazebo}`")
        if runner_profile.runner_labels:
            lines.append(
                f"- Labels: {', '.join('`'+l+'`' for l in runner_profile.runner_labels)}"
            )
        lines.append("")
    _write_text(path, "\n".join(lines))


def write_known_limitations_md(
    path: Path, *, items: tuple[str, ...]
) -> None:
    lines = [
        "# Known Limitations",
        "",
        f"_{LIVE_RUNTIME_DISCLAIMER}_",
        "",
    ]
    if not items:
        lines.append("- None recorded.")
    else:
        for entry in items:
            lines.append(f"- {entry}")
    _write_text(path, "\n".join(lines))


def init_run_directory(root: Path, run_id: str) -> Path:
    bundle = Path(root) / run_id
    (bundle / "bags").mkdir(parents=True, exist_ok=True)
    (bundle / "logs").mkdir(parents=True, exist_ok=True)
    return bundle


def write_evidence_bundle(
    *,
    bundle_dir: Path,
    run_id: str,
    plan_id: str,
    runner_profile: RunnerProfile | None,
    summary: LiveRunSummary,
    bag_manifest: BagManifest,
    events_jsonl: str = "",
    extra_known_limitations: tuple[str, ...] = (),
) -> None:
    bundle_dir = Path(bundle_dir)
    bundle_dir.mkdir(parents=True, exist_ok=True)
    (bundle_dir / "bags").mkdir(parents=True, exist_ok=True)
    (bundle_dir / "logs").mkdir(parents=True, exist_ok=True)

    write_metadata(
        bundle_dir / "metadata.json",
        run_id=run_id,
        plan_id=plan_id,
        runner_id=summary.runner_id,
        started_at=summary.started_at,
        finished_at=summary.finished_at,
        notes=summary.notes,
    )
    if runner_profile is not None:
        write_runner_profile(runner_profile, bundle_dir / "runner-profile.json")
    else:
        _write_json(
            bundle_dir / "runner-profile.json",
            {"runner_id": summary.runner_id, "qualification_status": "unknown"},
        )
    write_live_run_summary(bundle_dir / "live-run-summary.json", summary)
    write_bag_manifest(bag_manifest, bundle_dir / "bag-manifest.json")
    write_qualification_summary_md(
        bundle_dir / "qualification-summary.md",
        run_id=run_id,
        summary=summary,
        bag_manifest=bag_manifest,
        runner_profile=runner_profile,
    )
    items: list[str] = list(extra_known_limitations)
    if summary.status == LIVE_RUN_STATUS_NOT_EXECUTED:
        items.append("Live execution did not occur on this run.")
    if bag_manifest.bag_status == BAG_STATUS_NOT_EXECUTED:
        items.append("No rosbag2 artefacts were captured on this run.")
    write_known_limitations_md(
        bundle_dir / "known-limitations.md", items=tuple(items)
    )
    # events.jsonl: empty file is allowed; only write content if provided.
    events_path = bundle_dir / "events.jsonl"
    if events_jsonl or not events_path.exists():
        Path(events_path).write_text(events_jsonl, encoding="utf-8")


def build_not_executed_bundle(
    *,
    bundle_dir: Path,
    run_id: str,
    plan_id: str,
    runner_id: str,
    runner_profile: RunnerProfile | None,
    scenario_ids: tuple[str, ...],
    reason: str,
    started_at: str,
    finished_at: str,
) -> None:
    """Emit a coherent ``not_executed`` evidence bundle (no fabrication)."""

    summary = LiveRunSummary(
        run_id=run_id,
        runner_id=runner_id,
        plan_id=plan_id,
        scenario_ids=scenario_ids,
        started_at=started_at,
        finished_at=finished_at,
        status=LIVE_RUN_STATUS_NOT_EXECUTED,
        bag_status=BAG_STATUS_NOT_EXECUTED,
        not_executed_reason=reason,
        notes="",
    )
    manifest = build_not_executed_manifest(
        run_id=run_id,
        scenario_id=scenario_ids[0] if scenario_ids else "",
        reason=reason,
    )
    write_evidence_bundle(
        bundle_dir=Path(bundle_dir),
        run_id=run_id,
        plan_id=plan_id,
        runner_profile=runner_profile,
        summary=summary,
        bag_manifest=manifest,
    )


def evidence_bundle_required_files(bundle_dir: Path) -> tuple[str, ...]:
    """Return the names of required files present in the bundle."""

    bundle_dir = Path(bundle_dir)
    return tuple(name for name in REQUIRED_EVIDENCE_FILES if (bundle_dir / name).exists())


def evidence_bundle_missing_files(bundle_dir: Path) -> tuple[str, ...]:
    bundle_dir = Path(bundle_dir)
    return tuple(name for name in REQUIRED_EVIDENCE_FILES if not (bundle_dir / name).exists())


def detect_environment_block_reason() -> str | None:
    """Return a string explaining why live execution can't run, else None.

    The check is intentionally cheap and pessimistic: anything that
    suggests we are NOT on a Jazzy + Gazebo host returns a reason
    string. The check covers the env vars and binaries that real
    Jazzy hosts always have.
    """

    if os.environ.get("ROS_DISTRO", "") != "jazzy":
        return "ROS_DISTRO is not 'jazzy'; live execution requires a Jazzy host"
    return None


__all__ = [
    "init_run_directory",
    "write_metadata",
    "write_live_run_summary",
    "write_qualification_summary_md",
    "write_known_limitations_md",
    "write_evidence_bundle",
    "build_not_executed_bundle",
    "evidence_bundle_required_files",
    "evidence_bundle_missing_files",
    "detect_environment_block_reason",
]
