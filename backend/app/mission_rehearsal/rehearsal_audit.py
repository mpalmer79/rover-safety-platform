"""Audit bundle builder + Markdown renderer."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Mapping

from .models import (
    MISSION_REHEARSAL_DISCLAIMER,
    MISSION_REHEARSAL_VERSION,
    MissionRehearsalAudit,
    MissionRehearsalDecision,
    MissionRehearsalEvent,
    MissionRehearsalPlan,
    MissionRehearsalReplayBundle,
    MissionRehearsalRequest,
    MissionRehearsalRuntime,
    MissionRehearsalAnalyticsResult,
)


def _request_to_dict(req: MissionRehearsalRequest) -> dict:
    return {
        "request_id": req.request_id,
        "description": req.description,
        "mission_id": req.mission_id,
        "proposal_source": req.proposal_source,
        "requested_at_utc": req.requested_at_utc,
        "seed": req.seed,
        "operator": req.operator,
        "odd_profile_id": req.odd_profile_id,
        "notes": list(req.notes),
    }


def _plan_to_dict(plan: MissionRehearsalPlan | None) -> dict | None:
    if plan is None:
        return None
    return {
        "mission_id": plan.mission_id,
        "request_id": plan.request_id,
        "proposal_source": plan.proposal_source,
        "waypoints": [
            {
                "waypoint_id": w.waypoint_id,
                "label": w.label,
                "stage_kind": w.stage_kind,
                "bounded_distance_m": w.bounded_distance_m,
                "bounded_angle_deg": w.bounded_angle_deg,
                "bounded_speed_mps": w.bounded_speed_mps,
            }
            for w in plan.waypoints
        ],
        "safety_constraints": list(plan.safety_constraints),
        "requested_topics": list(plan.requested_topics),
        "forbidden_topics": list(plan.forbidden_topics),
        "odd_profile_id": plan.odd_profile_id,
        "deterministic_hash": plan.deterministic_hash,
        "risk_band": plan.risk_band,
        "notes": list(plan.notes),
    }


def _decision_to_dict(d: MissionRehearsalDecision) -> dict:
    return {
        "decision_id": d.decision_id,
        "decision_status": d.decision_status,
        "safety_status": d.safety_status,
        "rationale": list(d.rationale),
        "rejected_reasons": list(d.rejected_reasons),
        "allowed_topics": list(d.allowed_topics),
        "forbidden_topics": list(d.forbidden_topics),
        "requires_human_review": d.requires_human_review,
        "decided_at_utc": d.decided_at_utc,
    }


def _event_to_dict(e: MissionRehearsalEvent) -> dict:
    return {
        "event_id": e.event_id,
        "mission_id": e.mission_id,
        "event_type": e.event_type,
        "event_subtype": e.event_subtype,
        "event_time_ns": e.event_time_ns,
        "source_phase": e.source_phase,
        "severity": e.severity,
        "description": e.description,
        "deterministic_hash": e.deterministic_hash,
        "payload": dict(e.payload),
    }


def _runtime_to_dict(rt: MissionRehearsalRuntime | None) -> dict | None:
    if rt is None:
        return None
    return {
        "mission_id": rt.mission_id,
        "final_status": rt.final_status,
        "final_failure_reason": rt.final_failure_reason,
        "safety_status": rt.safety_status,
        "events": [_event_to_dict(e) for e in rt.events],
        "deterministic_hash": rt.deterministic_hash,
        "started_at_utc": rt.started_at_utc,
        "finished_at_utc": rt.finished_at_utc,
        "timeline": {
            "transitions": [list(t) for t in rt.timeline.transitions],
            "rendered_markdown": rt.timeline.rendered_markdown,
            "rendered_mermaid": rt.timeline.rendered_mermaid,
        },
    }


def _replay_to_dict(rep: MissionRehearsalReplayBundle | None) -> dict | None:
    if rep is None:
        return None
    return {
        "mission_id": rep.mission_id,
        "evidence_status": rep.evidence_status,
        "bag_backed": rep.bag_backed,
        "replay_markers": [dict(m) for m in rep.replay_markers],
        "review_status": rep.review_status,
        "rendered_markdown": rep.rendered_markdown,
        "deterministic_hash": rep.deterministic_hash,
        "notes": list(rep.notes),
    }


def _analytics_to_dict(an: MissionRehearsalAnalyticsResult | None) -> dict | None:
    if an is None:
        return None
    return {
        "mission_id": an.mission_id,
        "rehearsal_count": an.rehearsal_count,
        "approved_count": an.approved_count,
        "rejected_count": an.rejected_count,
        "aborted_count": an.aborted_count,
        "completed_count": an.completed_count,
        "supervisor_rejection_count": an.supervisor_rejection_count,
        "validator_rejection_count": an.validator_rejection_count,
        "deterministic_replay_stable": an.deterministic_replay_stable,
        "notes": list(an.notes),
    }


def build_audit_bundle(
    *,
    request: MissionRehearsalRequest,
    plan: MissionRehearsalPlan | None,
    validation_diagnostics: Iterable[Mapping[str, object]],
    decision: MissionRehearsalDecision,
    runtime: MissionRehearsalRuntime | None,
    replay: MissionRehearsalReplayBundle | None,
    analytics: MissionRehearsalAnalyticsResult | None,
    generated_at_utc: str | None = None,
) -> MissionRehearsalAudit:
    timestamp = (
        generated_at_utc
        or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    )
    return MissionRehearsalAudit(
        request=request,
        plan=plan,
        validation_diagnostics=tuple(validation_diagnostics),
        decision=decision,
        runtime=runtime,
        replay=replay,
        analytics=analytics,
        final_status=runtime.final_status if runtime is not None else "rejected",
        final_failure_reason=runtime.final_failure_reason if runtime is not None else "",
        safety_status=runtime.safety_status if runtime is not None else decision.safety_status,
        generated_at_utc=timestamp,
        disclaimer=MISSION_REHEARSAL_DISCLAIMER,
    )


def audit_to_dict(audit: MissionRehearsalAudit) -> dict:
    return {
        "mission_rehearsal_version": MISSION_REHEARSAL_VERSION,
        "request": _request_to_dict(audit.request),
        "plan": _plan_to_dict(audit.plan),
        "validation_diagnostics": [
            dict(d) for d in audit.validation_diagnostics if isinstance(d, Mapping)
        ],
        "decision": _decision_to_dict(audit.decision),
        "runtime": _runtime_to_dict(audit.runtime),
        "replay": _replay_to_dict(audit.replay),
        "analytics": _analytics_to_dict(audit.analytics),
        "final_status": audit.final_status,
        "final_failure_reason": audit.final_failure_reason,
        "safety_status": audit.safety_status,
        "generated_at_utc": audit.generated_at_utc,
        "disclaimer": audit.disclaimer,
    }


def render_rehearsal_report_markdown(audit: MissionRehearsalAudit) -> str:
    lines: list[str] = []
    lines.append(f"# Mission rehearsal report: {audit.request.mission_id}")
    lines.append("")
    lines.append(f"_{audit.disclaimer}_")
    lines.append("")
    lines.append(f"- **Request id:** `{audit.request.request_id}`")
    lines.append(f"- **Mission id:** `{audit.request.mission_id}`")
    lines.append(f"- **Final status:** `{audit.final_status}`")
    if audit.final_failure_reason:
        lines.append(f"- **Failure reason:** `{audit.final_failure_reason}`")
    lines.append(f"- **Safety status:** `{audit.safety_status}`")
    lines.append(f"- **Supervisor decision:** `{audit.decision.decision_status}`")
    lines.append(f"- **Plan deterministic hash:** `{audit.plan.deterministic_hash if audit.plan else 'n/a'}`")
    if audit.runtime is not None:
        lines.append(f"- **Runtime deterministic hash:** `{audit.runtime.deterministic_hash}`")
    lines.append(f"- **Generated (UTC):** {audit.generated_at_utc}")
    lines.append("")

    lines.append("## Request")
    lines.append("")
    lines.append(f"- description: {audit.request.description}")
    lines.append(f"- proposal source: {audit.request.proposal_source}")
    lines.append(f"- seed: {audit.request.seed}")
    if audit.request.operator:
        lines.append(f"- operator: {audit.request.operator}")
    lines.append("")

    if audit.plan is not None:
        lines.append("## Mission plan")
        lines.append("")
        lines.append(f"- risk band: `{audit.plan.risk_band}`")
        lines.append(f"- waypoints: {len(audit.plan.waypoints)}")
        for w in audit.plan.waypoints:
            lines.append(
                f"  - `{w.waypoint_id}` "
                f"({w.stage_kind}) "
                f"dist={w.bounded_distance_m} m, "
                f"angle={w.bounded_angle_deg}° "
                f"speed={w.bounded_speed_mps} m/s"
            )
        lines.append(
            "- requested topics: "
            + (", ".join(f"`{t}`" for t in audit.plan.requested_topics) or "_(none)_")
        )
        lines.append(
            "- forbidden topics: "
            + (", ".join(f"`{t}`" for t in audit.plan.forbidden_topics) or "_(none)_")
        )
        lines.append("")

    lines.append("## Validation")
    lines.append("")
    if audit.validation_diagnostics:
        for d in audit.validation_diagnostics:
            if isinstance(d, Mapping):
                lines.append(
                    f"- [{d.get('severity', '?')}] `{d.get('code', '?')}`: "
                    f"{d.get('message', '')}"
                )
    else:
        lines.append("_validation passed cleanly_")
    lines.append("")

    lines.append("## Supervisor decision")
    lines.append("")
    lines.append(f"- status: `{audit.decision.decision_status}`")
    lines.append(f"- safety status: `{audit.decision.safety_status}`")
    if audit.decision.rejected_reasons:
        lines.append(
            "- rejected reasons: "
            + ", ".join(f"`{r}`" for r in audit.decision.rejected_reasons)
        )
    if audit.decision.rationale:
        lines.append("- rationale:")
        for r in audit.decision.rationale:
            lines.append(f"  - {r}")
    lines.append("")

    if audit.runtime is not None:
        lines.append("## Runtime")
        lines.append("")
        lines.append(f"- events: {len(audit.runtime.events)}")
        lines.append(f"- started: {audit.runtime.started_at_utc}")
        lines.append(f"- finished: {audit.runtime.finished_at_utc}")
        lines.append("- state transitions:")
        for src, dst, reason in audit.runtime.timeline.transitions:
            lines.append(f"  - `{src}` → `{dst}` ({reason})")
        lines.append("")

    if audit.replay is not None:
        lines.append("## Replay bundle")
        lines.append("")
        lines.append(f"- evidence status: `{audit.replay.evidence_status}`")
        lines.append(f"- bag-backed: {audit.replay.bag_backed}")
        lines.append(f"- review status: `{audit.replay.review_status}`")
        lines.append(f"- markers: {len(audit.replay.replay_markers)}")
        lines.append("")

    if audit.analytics is not None:
        lines.append("## Analytics")
        lines.append("")
        for key in (
            "rehearsal_count",
            "approved_count",
            "rejected_count",
            "aborted_count",
            "completed_count",
            "supervisor_rejection_count",
            "validator_rejection_count",
            "deterministic_replay_stable",
        ):
            lines.append(f"- {key}: `{getattr(audit.analytics, key)}`")
        lines.append("")

    lines.append("## Authority statement")
    lines.append("")
    lines.append(
        "This rehearsal report is simulation-only. The runtime "
        "safety supervisor and motion arbitration remain "
        "authoritative; nothing in this artefact authorises live "
        "robot motion or implies safety certification."
    )
    lines.append("")
    return "\n".join(lines)
