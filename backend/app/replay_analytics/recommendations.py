"""Deterministic replay-recommendations engine.

Walks the loaded bundle and the coverage report, then emits a list
of :class:`ReplayRecommendation` instances. Each recommendation is
grounded in an evidence gap and cites the exact missing artefact;
no AI-generated vague suggestions.
"""

from __future__ import annotations

from typing import Iterable

from app.replay_analytics.coverage import ReplayCoverageReport
from app.replay_analytics.loader import LoadedReplayBundle
from app.replay_analytics.models import (
    ReplayGap,
    ReplayGapSeverity,
    ReplayRecommendation,
)


def detect_gaps(
    *,
    bundle: LoadedReplayBundle,
    coverage: ReplayCoverageReport,
) -> list[ReplayGap]:
    """Walk the inputs and emit per-incident gap findings."""

    incident_id = bundle.incident_id
    gaps: list[ReplayGap] = []

    if not bundle.has_replay_review:
        gaps.append(
            ReplayGap(
                incident_id=incident_id,
                label="replay_review_missing",
                severity=ReplayGapSeverity.CRITICAL,
                detail=(
                    "no replay-review bundle present; analytics cannot run"
                ),
                evidence_paths=(str(bundle.incident_dir),),
            )
        )
        return gaps

    if bundle.bag_status == "missing_bag":
        gaps.append(
            ReplayGap(
                incident_id=incident_id,
                label="missing_bag",
                severity=ReplayGapSeverity.HIGH,
                detail=(
                    "no rosbag2 / MCAP artefacts detected in any candidate "
                    "location; visual replay impossible"
                ),
                evidence_paths=tuple(
                    str(b.get("bag_root", ""))
                    for b in (bundle.replay_manifest or {}).get("bag_indices", [])
                ),
            )
        )

    if bundle.bag_status == "static_only":
        gaps.append(
            ReplayGap(
                incident_id=incident_id,
                label="static_only_evidence",
                severity=ReplayGapSeverity.MODERATE,
                detail=(
                    "incident is static-only; no live runtime evidence "
                    "available for replay analysis"
                ),
            )
        )

    missing_topics = (
        bundle.replay_manifest.get("missing_topics", [])
        if bundle.replay_manifest
        else []
    )
    for topic in missing_topics:
        gaps.append(
            ReplayGap(
                incident_id=incident_id,
                label=f"missing_topic[{topic}]",
                severity=ReplayGapSeverity.HIGH,
                detail=f"required topic {topic} absent from bag inventory",
                evidence_paths=(
                    str(bundle.incident_dir / "replay-review-manifest.json"),
                ),
            )
        )

    if not bundle.markers:
        gaps.append(
            ReplayGap(
                incident_id=incident_id,
                label="markers_missing",
                severity=ReplayGapSeverity.MODERATE,
                detail=(
                    "no replay markers emitted; incident timeline did not "
                    "produce marker indices"
                ),
                evidence_paths=(
                    str(bundle.incident_dir / "replay-markers.json"),
                ),
            )
        )

    align_metric = coverage.metric("marker_alignment_pct")
    if align_metric and align_metric.available and align_metric.value is not None:
        if align_metric.value < 50.0:
            gaps.append(
                ReplayGap(
                    incident_id=incident_id,
                    label="poor_marker_alignment",
                    severity=ReplayGapSeverity.MODERATE,
                    detail=(
                        f"only {align_metric.value:.1f}% of markers carry "
                        "exact alignment; align manually in Foxglove"
                    ),
                    evidence_paths=(
                        str(bundle.incident_dir / "replay-markers.json"),
                    ),
                )
            )

    contradictions = (
        bundle.incident_report.get("contradictions") or []
        if bundle.incident_report
        else []
    )
    if contradictions:
        gaps.append(
            ReplayGap(
                incident_id=incident_id,
                label="incident_contradictions",
                severity=ReplayGapSeverity.HIGH,
                detail=(
                    f"{len(contradictions)} contradiction(s) recorded in the "
                    "incident report; resolve before claiming a clean replay"
                ),
                evidence_paths=(
                    str(bundle.incident_dir / "incident-report.json"),
                ),
            )
        )

    review_metric = coverage.metric("review_artifact_completeness_pct")
    if review_metric and review_metric.available and review_metric.value is not None:
        if review_metric.value < 100.0:
            gaps.append(
                ReplayGap(
                    incident_id=incident_id,
                    label="incomplete_review_artefacts",
                    severity=ReplayGapSeverity.LOW,
                    detail=(
                        f"only {review_metric.value:.1f}% of canonical review "
                        "artefacts are present in the bundle"
                    ),
                    evidence_paths=(str(bundle.incident_dir),),
                )
            )

    return gaps


def build_recommendations(
    *,
    bundle: LoadedReplayBundle,
    gaps: Iterable[ReplayGap],
) -> list[ReplayRecommendation]:
    """Map each gap to a concrete operational recommendation."""

    incident_id = bundle.incident_id
    out: list[ReplayRecommendation] = []
    for gap in gaps:
        if gap.label == "replay_review_missing":
            out.append(
                ReplayRecommendation(
                    incident_id=incident_id,
                    label="run_build_replay_review_bundle",
                    detail=(
                        "Run `rover_ws/tools/build_replay_review_bundle.py "
                        f"--incident {bundle.incident_dir}` so the analytics "
                        "layer has artefacts to inspect."
                    ),
                    cited_artifacts=tuple(gap.evidence_paths),
                )
            )
            continue
        if gap.label == "missing_bag":
            out.append(
                ReplayRecommendation(
                    incident_id=incident_id,
                    label="capture_rosbag2",
                    detail=(
                        "Capture a rosbag2 (.mcap or .db3 + metadata.yaml) "
                        f"on a Jazzy host and place it under "
                        f"{bundle.incident_dir}/bags/."
                    ),
                    cited_artifacts=tuple(gap.evidence_paths),
                )
            )
            continue
        if gap.label == "static_only_evidence":
            out.append(
                ReplayRecommendation(
                    incident_id=incident_id,
                    label="rerun_on_jazzy_host",
                    detail=(
                        "Re-run the underlying scenario on a Jazzy host "
                        "with `qualified_runtime_run.py --ros-launch` to "
                        "capture live runtime evidence."
                    ),
                )
            )
            continue
        if gap.label.startswith("missing_topic["):
            topic = gap.label[len("missing_topic[") : -1]
            out.append(
                ReplayRecommendation(
                    incident_id=incident_id,
                    label=f"add_topic[{topic}]",
                    detail=(
                        f"Add `{topic}` to the rosbag2 record set so the "
                        "replay session covers the documented contract."
                    ),
                    cited_artifacts=tuple(gap.evidence_paths),
                )
            )
            continue
        if gap.label == "markers_missing":
            out.append(
                ReplayRecommendation(
                    incident_id=incident_id,
                    label="rerun_reconstruct_incident",
                    detail=(
                        "Re-run `rover_ws/tools/reconstruct_incident.py` to "
                        "regenerate the timeline; if markers remain absent, "
                        "extend the incident-analysis layer to cover the "
                        "missing event categories."
                    ),
                    cited_artifacts=tuple(gap.evidence_paths),
                )
            )
            continue
        if gap.label == "poor_marker_alignment":
            out.append(
                ReplayRecommendation(
                    incident_id=incident_id,
                    label="improve_marker_alignment",
                    detail=(
                        "Align the Foxglove playhead manually for the "
                        "markers without sim_time_ns and record the "
                        "corrected offsets in operator notes."
                    ),
                    cited_artifacts=tuple(gap.evidence_paths),
                )
            )
            continue
        if gap.label == "incident_contradictions":
            out.append(
                ReplayRecommendation(
                    incident_id=incident_id,
                    label="resolve_contradictions",
                    detail=(
                        "Inspect the contradictions listed in incident-"
                        "report.md and either reconcile the underlying "
                        "evidence or annotate the report."
                    ),
                    cited_artifacts=tuple(gap.evidence_paths),
                )
            )
            continue
        if gap.label == "incomplete_review_artefacts":
            out.append(
                ReplayRecommendation(
                    incident_id=incident_id,
                    label="regenerate_review_artefacts",
                    detail=(
                        "Re-run `build_replay_review_bundle.py` and / or "
                        "`reconstruct_incident.py` to repopulate the "
                        "missing canonical review artefacts."
                    ),
                    cited_artifacts=tuple(gap.evidence_paths),
                )
            )
            continue
    if not out:
        out.append(
            ReplayRecommendation(
                incident_id=incident_id,
                label="no_recommendations",
                detail=(
                    "No gaps detected in the available artefacts; record an "
                    "operator review acknowledgement to close out the "
                    "incident."
                ),
            )
        )
    return out
