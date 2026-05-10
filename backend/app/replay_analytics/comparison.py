"""Cross-incident replay comparison.

Extends Phase 6's incident comparator with replay-quality columns:
score, coverage status, marker alignment, missing-topic count,
contradictions, and review completion. Rows are ordered
deterministically by descending score, then by incident id.
"""

from __future__ import annotations

from typing import Iterable

from app.replay_analytics.coverage import ReplayCoverageReport
from app.replay_analytics.loader import LoadedReplayBundle
from app.replay_analytics.models import (
    ReplayComparison,
    ReplayQualityScore,
)


def build_comparison(
    *,
    comparison_id: str,
    bundles: Iterable[LoadedReplayBundle],
    coverages: dict[str, ReplayCoverageReport],
    scores: dict[str, ReplayQualityScore],
) -> ReplayComparison:
    """Compose a :class:`ReplayComparison` for the supplied incidents."""

    bundles = list(bundles)
    rows: list[dict] = []
    for bundle in bundles:
        cov = coverages.get(bundle.incident_id)
        score = scores.get(bundle.incident_id)
        rows.append(
            _row_for(bundle=bundle, coverage=cov, score=score)
        )
    rows.sort(
        key=lambda r: (-int(r.get("quality_score", 0)), r.get("incident_id", ""))
    )

    deltas: list[dict] = []
    if len(rows) >= 2:
        head = rows[0]
        for other in rows[1:]:
            deltas.append(_pairwise_delta(head, other))

    notes: list[str] = []
    origins = {r.get("evidence_origin", "unknown") for r in rows}
    if len(origins) > 1:
        notes.append(
            "compared incidents have different evidence_origin values; "
            "treat the deltas as informational, not equivalence."
        )

    return ReplayComparison(
        comparison_id=comparison_id, rows=rows, deltas=deltas, notes=tuple(notes)
    )


def _row_for(
    *,
    bundle: LoadedReplayBundle,
    coverage: ReplayCoverageReport | None,
    score: ReplayQualityScore | None,
) -> dict:
    cov_metric = coverage.metric if coverage else (lambda _name: None)
    align = cov_metric("marker_alignment_pct") if coverage else None
    timeline = cov_metric("timeline_alignment_pct") if coverage else None
    topics = cov_metric("expected_topics_present_pct") if coverage else None
    completeness = cov_metric("evidence_completeness_pct") if coverage else None
    review = cov_metric("review_artifact_completeness_pct") if coverage else None
    incident_report = bundle.incident_report or {}
    safety_states = incident_report.get("safety_states") or []
    return {
        "incident_id": bundle.incident_id,
        "scenario_id": incident_report.get("scenario_id"),
        "evidence_origin": bundle.evidence_origin,
        "bag_status": bundle.bag_status,
        "evidence_status": bundle.evidence_status,
        "quality_score": score.score if score else 0,
        "coverage_status": (
            score.coverage_status.value if score else "missing"
        ),
        "review_completion_status": _review_status(bundle),
        "marker_alignment_pct": align.value if align else None,
        "timeline_alignment_pct": timeline.value if timeline else None,
        "expected_topics_present_pct": topics.value if topics else None,
        "evidence_completeness_pct": (
            completeness.value if completeness else None
        ),
        "review_artifact_completeness_pct": (
            review.value if review else None
        ),
        "contradiction_count": len(incident_report.get("contradictions") or []),
        "missing_topics_count": len(
            (bundle.replay_manifest or {}).get("missing_topics") or []
        ),
        "safety_states": list(safety_states),
        "outcome": incident_report.get("outcome", ""),
        "blocking_gaps": list(score.blocking_gaps) if score else [],
    }


def _review_status(bundle: LoadedReplayBundle) -> str:
    if bundle.review_audit:
        return bundle.review_audit.get("status", "not_started")
    return "not_started"


def _pairwise_delta(head: dict, other: dict) -> dict:
    return {
        "left_incident": head.get("incident_id"),
        "right_incident": other.get("incident_id"),
        "score_delta": int(head.get("quality_score", 0))
        - int(other.get("quality_score", 0)),
        "marker_alignment_delta": _delta_metric(head, other, "marker_alignment_pct"),
        "evidence_completeness_delta": _delta_metric(
            head, other, "evidence_completeness_pct"
        ),
        "missing_topics_delta": int(other.get("missing_topics_count", 0))
        - int(head.get("missing_topics_count", 0)),
        "contradictions_delta": int(other.get("contradiction_count", 0))
        - int(head.get("contradiction_count", 0)),
        "left_evidence_origin": head.get("evidence_origin"),
        "right_evidence_origin": other.get("evidence_origin"),
    }


def _delta_metric(head: dict, other: dict, key: str):
    a = head.get(key)
    b = other.get(key)
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        return None
    return round(float(a) - float(b), 2)


def render_comparison_md(comparison: ReplayComparison) -> str:
    lines: list[str] = []
    lines.append(f"# Replay Analytics Comparison — `{comparison.comparison_id}`")
    lines.append("")
    lines.append(
        "_Generated by `rover_ws/tools/compare_replay_reviews.py`. "
        "The platform is **not safety-certified**; this comparison is "
        "engineering analytics material._"
    )
    lines.append("")
    if not comparison.rows:
        lines.append("_No incidents supplied._")
        return "\n".join(lines) + "\n"
    lines.append(
        "| Incident | Scenario | Origin | Bag | Score | Coverage | "
        "Review | Marker% | Topics% | Evidence% | "
        "Missing topics | Contradictions |"
    )
    lines.append(
        "|---|---|---|---|---|---|---|---|---|---|---|---|"
    )
    for r in comparison.rows:
        lines.append(
            "| `{incident}` | `{scenario}` | `{origin}` | `{bag}` | "
            "{score} | `{coverage}` | `{review}` | {marker} | {topics} | "
            "{evidence} | {missing} | {contradictions} |".format(
                incident=r["incident_id"],
                scenario=r.get("scenario_id") or "-",
                origin=r["evidence_origin"],
                bag=r["bag_status"],
                score=r["quality_score"],
                coverage=r["coverage_status"],
                review=r["review_completion_status"],
                marker=_fmt(r.get("marker_alignment_pct")),
                topics=_fmt(r.get("expected_topics_present_pct")),
                evidence=_fmt(r.get("evidence_completeness_pct")),
                missing=r.get("missing_topics_count", 0),
                contradictions=r.get("contradiction_count", 0),
            )
        )
    lines.append("")
    if comparison.deltas:
        lines.append("## Pairwise deltas (vs. top-scoring incident)")
        lines.append("")
        lines.append(
            "| Right | Score Δ | Marker% Δ | Evidence% Δ | "
            "Missing topics Δ | Contradictions Δ |"
        )
        lines.append("|---|---|---|---|---|---|")
        for d in comparison.deltas:
            lines.append(
                "| `{right}` | {score} | {marker} | {evidence} | "
                "{missing} | {contradictions} |".format(
                    right=d["right_incident"],
                    score=d["score_delta"],
                    marker=_fmt(d.get("marker_alignment_delta")),
                    evidence=_fmt(d.get("evidence_completeness_delta")),
                    missing=d.get("missing_topics_delta", 0),
                    contradictions=d.get("contradictions_delta", 0),
                )
            )
        lines.append("")
    if comparison.notes:
        lines.append("## Notes")
        lines.append("")
        for note in comparison.notes:
            lines.append(f"- {note}")
        lines.append("")
    return "\n".join(lines)


def _fmt(value) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.1f}"
    return str(value)
