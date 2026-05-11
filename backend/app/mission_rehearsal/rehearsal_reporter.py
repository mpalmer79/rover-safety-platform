"""Filesystem reporter for mission rehearsal audit bundles.

Bundle layout::

    <bundle_dir>/
      mission-request.json
      mission-plan.json
      validator-result.json
      supervisor-review.json
      rehearsal-events.json
      timeline.json
      timeline.mmd
      replay-review.json
      replay-review.md
      analytics.json
      rehearsal-audit.json
      rehearsal-report.md
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Mapping

from .models import (
    MissionRehearsalAnalyticsResult,
    MissionRehearsalAudit,
    MissionRehearsalDecision,
    MissionRehearsalPlan,
    MissionRehearsalReplayBundle,
    MissionRehearsalRequest,
    MissionRehearsalRuntime,
)
from .rehearsal_audit import (
    audit_to_dict,
    build_audit_bundle,
    render_rehearsal_report_markdown,
)


def _dump_json(path: Path, payload) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_audit_files(
    *,
    request: MissionRehearsalRequest,
    plan: MissionRehearsalPlan | None,
    validation_diagnostics: Iterable[Mapping[str, object]],
    decision: MissionRehearsalDecision,
    runtime: MissionRehearsalRuntime | None,
    replay: MissionRehearsalReplayBundle | None,
    analytics: MissionRehearsalAnalyticsResult | None,
    bundle_dir: Path,
    generated_at_utc: str | None = None,
) -> tuple[MissionRehearsalAudit, dict]:
    bundle_dir = Path(bundle_dir)
    bundle_dir.mkdir(parents=True, exist_ok=True)

    audit = build_audit_bundle(
        request=request,
        plan=plan,
        validation_diagnostics=validation_diagnostics,
        decision=decision,
        runtime=runtime,
        replay=replay,
        analytics=analytics,
        generated_at_utc=generated_at_utc,
    )
    audit_dict = audit_to_dict(audit)

    paths: dict[str, str] = {}

    request_path = bundle_dir / "mission-request.json"
    _dump_json(request_path, audit_dict["request"])
    paths["mission_request"] = str(request_path)

    plan_path = bundle_dir / "mission-plan.json"
    _dump_json(plan_path, audit_dict["plan"])
    paths["mission_plan"] = str(plan_path)

    validator_path = bundle_dir / "validator-result.json"
    _dump_json(
        validator_path,
        {
            "diagnostics": audit_dict["validation_diagnostics"],
            "rejection_count": sum(
                1
                for d in audit_dict["validation_diagnostics"]
                if isinstance(d, Mapping) and d.get("severity") == "rejection"
            ),
        },
    )
    paths["validator_result"] = str(validator_path)

    supervisor_path = bundle_dir / "supervisor-review.json"
    _dump_json(supervisor_path, audit_dict["decision"])
    paths["supervisor_review"] = str(supervisor_path)

    if audit.runtime is not None:
        events_path = bundle_dir / "rehearsal-events.json"
        _dump_json(events_path, audit_dict["runtime"]["events"])
        paths["rehearsal_events"] = str(events_path)

        timeline_json_path = bundle_dir / "timeline.json"
        _dump_json(
            timeline_json_path,
            {
                "transitions": audit_dict["runtime"]["timeline"]["transitions"],
                "events": audit_dict["runtime"]["events"],
            },
        )
        paths["timeline_json"] = str(timeline_json_path)

        timeline_mmd_path = bundle_dir / "timeline.mmd"
        timeline_mmd_path.write_text(
            audit.runtime.timeline.rendered_mermaid, encoding="utf-8"
        )
        paths["timeline_mmd"] = str(timeline_mmd_path)

    if audit.replay is not None:
        replay_path = bundle_dir / "replay-review.json"
        _dump_json(replay_path, audit_dict["replay"])
        paths["replay_review"] = str(replay_path)
        replay_md_path = bundle_dir / "replay-review.md"
        replay_md_path.write_text(audit.replay.rendered_markdown, encoding="utf-8")
        paths["replay_review_md"] = str(replay_md_path)

    if audit.analytics is not None:
        analytics_path = bundle_dir / "analytics.json"
        _dump_json(analytics_path, audit_dict["analytics"])
        paths["analytics"] = str(analytics_path)

    audit_json_path = bundle_dir / "rehearsal-audit.json"
    _dump_json(audit_json_path, audit_dict)
    paths["rehearsal_audit"] = str(audit_json_path)

    report_path = bundle_dir / "rehearsal-report.md"
    report_path.write_text(
        render_rehearsal_report_markdown(audit), encoding="utf-8"
    )
    paths["rehearsal_report"] = str(report_path)

    return audit, paths
