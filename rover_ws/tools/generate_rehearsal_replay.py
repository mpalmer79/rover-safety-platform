#!/usr/bin/env python3
"""Phase 16: regenerate the replay-review artefacts from a stored audit.

The platform is **not safety-certified**. Reads a stored
``rehearsal-audit.json``, rebuilds the replay bundle deterministically
from the recorded plan + runtime, and writes ``replay-review.json``,
``replay-review.md``, and ``analytics.json`` into the same audit
directory. Used to refresh replay artefacts without re-running the
full rehearsal.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _probe_common import ensure_app_on_path  # noqa: E402

ensure_app_on_path()

from app.mission_rehearsal.models import (  # noqa: E402
    MissionRehearsalDecision,
    MissionRehearsalEvent,
    MissionRehearsalPlan,
    MissionRehearsalRuntime,
    MissionRehearsalTimeline,
    RehearsalWaypoint,
)
from app.mission_rehearsal import (  # noqa: E402
    build_analytics_result,
    build_replay_bundle,
)


def _str_tuple(value) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    return tuple(str(v) for v in value)


def _plan_from_dict(d) -> MissionRehearsalPlan:
    waypoints = tuple(
        RehearsalWaypoint(
            waypoint_id=str(w.get("waypoint_id") or ""),
            label=str(w.get("label") or ""),
            stage_kind=str(w.get("stage_kind") or "move"),
            bounded_distance_m=float(w.get("bounded_distance_m") or 0.0),
            bounded_angle_deg=float(w.get("bounded_angle_deg") or 0.0),
            bounded_speed_mps=float(w.get("bounded_speed_mps") or 0.0),
        )
        for w in (d.get("waypoints") or [])
    )
    return MissionRehearsalPlan(
        mission_id=str(d.get("mission_id") or ""),
        request_id=str(d.get("request_id") or ""),
        proposal_source=str(d.get("proposal_source") or ""),
        waypoints=waypoints,
        safety_constraints=_str_tuple(d.get("safety_constraints")),
        requested_topics=_str_tuple(d.get("requested_topics")),
        forbidden_topics=_str_tuple(d.get("forbidden_topics")),
        odd_profile_id=str(d.get("odd_profile_id") or "default-warehouse"),
        deterministic_hash=str(d.get("deterministic_hash") or ""),
        risk_band=str(d.get("risk_band") or "guarded"),
        notes=_str_tuple(d.get("notes")),
    )


def _event_from_dict(e) -> MissionRehearsalEvent:
    return MissionRehearsalEvent(
        event_id=str(e.get("event_id") or ""),
        mission_id=str(e.get("mission_id") or ""),
        event_type=str(e.get("event_type") or ""),
        event_subtype=str(e.get("event_subtype") or ""),
        event_time_ns=int(e.get("event_time_ns") or 0),
        source_phase=str(e.get("source_phase") or ""),
        severity=str(e.get("severity") or "info"),
        description=str(e.get("description") or ""),
        deterministic_hash=str(e.get("deterministic_hash") or ""),
        payload=dict(e.get("payload") or {}),
    )


def _runtime_from_dict(d) -> MissionRehearsalRuntime:
    events = tuple(_event_from_dict(e) for e in (d.get("events") or []))
    timeline_dict = d.get("timeline") or {}
    timeline = MissionRehearsalTimeline(
        mission_id=str(d.get("mission_id") or ""),
        transitions=tuple(tuple(t) for t in (timeline_dict.get("transitions") or [])),
        events=events,
        rendered_markdown=str(timeline_dict.get("rendered_markdown") or ""),
        rendered_mermaid=str(timeline_dict.get("rendered_mermaid") or ""),
    )
    return MissionRehearsalRuntime(
        mission_id=str(d.get("mission_id") or ""),
        final_status=str(d.get("final_status") or ""),
        final_failure_reason=str(d.get("final_failure_reason") or ""),
        safety_status=str(d.get("safety_status") or "guarded"),
        events=events,
        timeline=timeline,
        deterministic_hash=str(d.get("deterministic_hash") or ""),
        started_at_utc=str(d.get("started_at_utc") or ""),
        finished_at_utc=str(d.get("finished_at_utc") or ""),
    )


def _decision_from_dict(d) -> MissionRehearsalDecision:
    return MissionRehearsalDecision(
        decision_id=str(d.get("decision_id") or ""),
        decision_status=str(d.get("decision_status") or "rejected"),
        safety_status=str(d.get("safety_status") or "not_evaluated"),
        rationale=_str_tuple(d.get("rationale")),
        rejected_reasons=_str_tuple(d.get("rejected_reasons")),
        allowed_topics=_str_tuple(d.get("allowed_topics")),
        forbidden_topics=_str_tuple(d.get("forbidden_topics")),
        requires_human_review=bool(d.get("requires_human_review")),
        decided_at_utc=str(d.get("decided_at_utc") or ""),
    )


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--audit", required=True, type=Path)
    p.add_argument("--json", action="store_true")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    try:
        payload = json.loads(args.audit.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"audit file not found: {args.audit}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"audit file is not valid JSON: {exc}", file=sys.stderr)
        return 2

    plan_dict = payload.get("plan")
    runtime_dict = payload.get("runtime")
    if plan_dict is None or runtime_dict is None:
        print("audit must contain both plan and runtime", file=sys.stderr)
        return 2

    plan = _plan_from_dict(plan_dict)
    runtime = _runtime_from_dict(runtime_dict)
    decision = _decision_from_dict(payload.get("decision") or {})
    diagnostics = tuple(payload.get("validation_diagnostics") or ())

    replay = build_replay_bundle(plan=plan, runtime=runtime)
    analytics = build_analytics_result(
        runtime=runtime, decision=decision, validation_diagnostics=diagnostics,
    )

    bundle_dir = args.audit.parent
    replay_path = bundle_dir / "replay-review.json"
    replay_md_path = bundle_dir / "replay-review.md"
    analytics_path = bundle_dir / "analytics.json"

    replay_path.write_text(
        json.dumps(
            {
                "mission_id": replay.mission_id,
                "evidence_status": replay.evidence_status,
                "bag_backed": replay.bag_backed,
                "replay_markers": [dict(m) for m in replay.replay_markers],
                "review_status": replay.review_status,
                "rendered_markdown": replay.rendered_markdown,
                "deterministic_hash": replay.deterministic_hash,
                "notes": list(replay.notes),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    replay_md_path.write_text(replay.rendered_markdown, encoding="utf-8")
    analytics_path.write_text(
        json.dumps(
            {
                "mission_id": analytics.mission_id,
                "rehearsal_count": analytics.rehearsal_count,
                "approved_count": analytics.approved_count,
                "rejected_count": analytics.rejected_count,
                "aborted_count": analytics.aborted_count,
                "completed_count": analytics.completed_count,
                "supervisor_rejection_count": analytics.supervisor_rejection_count,
                "validator_rejection_count": analytics.validator_rejection_count,
                "deterministic_replay_stable": analytics.deterministic_replay_stable,
                "notes": list(analytics.notes),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    summary = {
        "mission_id": plan.mission_id,
        "replay_review": str(replay_path),
        "replay_review_md": str(replay_md_path),
        "analytics": str(analytics_path),
        "review_status": replay.review_status,
        "bag_backed": replay.bag_backed,
    }
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"mission_id:   {plan.mission_id}")
        print(f"review_status: {replay.review_status}")
        print(f"bag_backed:    {replay.bag_backed}")
        for key in ("replay_review", "replay_review_md", "analytics"):
            print(f"  wrote {key}: {summary[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
