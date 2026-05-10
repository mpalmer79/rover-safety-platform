"""Replay coverage analysis.

Derives a deterministic :class:`ReplayCoverageReport` from a loaded
replay bundle. Every metric is one of:

* ``available=True, value=<float in [0, 100]>`` — derived directly
  from the artefacts;
* ``available=False, value=None`` — the input needed to compute the
  metric is missing; the scoring engine treats this conservatively.

Static-only and missing-bag inputs always degrade the metrics: the
analyzer never fabricates coverage where evidence is absent.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from app.replay_analytics.loader import LoadedReplayBundle
from app.replay_analytics.models import (
    COVERAGE_METRIC_NAMES,
    ReplayCoverageMetric,
    ReplayCoverageReport,
    ReplayCoverageStatus,
)


_REQUIRED_REVIEW_ARTIFACTS: tuple[str, ...] = (
    "replay-review-manifest.json",
    "replay-review-report.json",
    "replay-review-report.md",
    "replay-review.md",
    "replay-markers.json",
    "foxglove-session.json",
    "incident-report.json",
    "incident-report.md",
    "timeline.json",
    "timeline.md",
)


def analyze_coverage(bundle: LoadedReplayBundle) -> ReplayCoverageReport:
    """Compute the per-incident coverage report."""

    notes: list[str] = []
    metrics: list[ReplayCoverageMetric] = []

    metrics.append(_topics_metric(bundle, notes))
    metrics.append(_marker_alignment_metric(bundle, notes))
    metrics.append(_timeline_alignment_metric(bundle, notes))
    metrics.append(_validation_pass_rate_metric(bundle, notes))
    metrics.append(_evidence_completeness_metric(bundle, notes))
    metrics.append(_review_artifact_completeness_metric(bundle, notes))

    coverage_status = _aggregate_status(bundle, metrics)
    return ReplayCoverageReport(
        incident_id=bundle.incident_id,
        bag_status=bundle.bag_status,
        evidence_origin=bundle.evidence_origin,
        metrics=tuple(metrics),
        coverage_status=coverage_status,
        notes=tuple(notes),
        generated_at_utc=datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
    )


# ---------------------------------------------------------------------------
# Per-metric computation.
# ---------------------------------------------------------------------------


def _topics_metric(
    bundle: LoadedReplayBundle, notes: list[str]
) -> ReplayCoverageMetric:
    """Fraction of required topics present in the bag inventory."""

    if bundle.replay_manifest is None:
        return ReplayCoverageMetric(
            name="expected_topics_present_pct",
            value=None,
            available=False,
            detail="no replay manifest",
        )
    expected_required = [
        t for t in bundle.replay_manifest.get("expected_topics", [])
        if isinstance(t, dict) and t.get("required")
    ]
    expected_required_names = [t.get("name", "") for t in expected_required]
    available_topics = set(bundle.replay_manifest.get("available_topics", []))
    if not available_topics:
        return ReplayCoverageMetric(
            name="expected_topics_present_pct",
            value=None,
            available=False,
            detail=(
                "bag inventory unavailable; cannot measure topic coverage"
            ),
        )
    if not expected_required_names:
        notes.append("no required topics declared by manifest")
        return ReplayCoverageMetric(
            name="expected_topics_present_pct",
            value=100.0,
            available=True,
            detail="no required topics declared",
        )
    present = sum(1 for n in expected_required_names if n in available_topics)
    pct = round(100.0 * present / len(expected_required_names), 2)
    return ReplayCoverageMetric(
        name="expected_topics_present_pct",
        value=pct,
        available=True,
        detail=(
            f"{present} of {len(expected_required_names)} required "
            f"topic(s) in bag inventory"
        ),
    )


def _marker_alignment_metric(
    bundle: LoadedReplayBundle, notes: list[str]
) -> ReplayCoverageMetric:
    """Fraction of markers with ``alignment=exact``."""

    if not bundle.markers:
        if bundle.has_replay_review:
            notes.append("replay markers absent")
        return ReplayCoverageMetric(
            name="marker_alignment_pct",
            value=None,
            available=False,
            detail="no markers emitted",
        )
    exact = sum(1 for m in bundle.markers if m.get("alignment") == "exact")
    pct = round(100.0 * exact / len(bundle.markers), 2)
    return ReplayCoverageMetric(
        name="marker_alignment_pct",
        value=pct,
        available=True,
        detail=f"{exact} of {len(bundle.markers)} marker(s) at exact alignment",
    )


def _timeline_alignment_metric(
    bundle: LoadedReplayBundle, notes: list[str]
) -> ReplayCoverageMetric:
    """Fraction of timeline entries that carry ``sim_time_ns``."""

    if bundle.incident_report is None:
        return ReplayCoverageMetric(
            name="timeline_alignment_pct",
            value=None,
            available=False,
            detail="no incident report",
        )
    timeline = bundle.incident_report.get("timeline") or {}
    entries = timeline.get("entries") or []
    if not entries:
        return ReplayCoverageMetric(
            name="timeline_alignment_pct",
            value=None,
            available=False,
            detail="incident timeline has no entries",
        )
    aligned = sum(
        1 for e in entries if isinstance(e.get("sim_time_ns"), (int, float))
    )
    pct = round(100.0 * aligned / len(entries), 2)
    return ReplayCoverageMetric(
        name="timeline_alignment_pct",
        value=pct,
        available=True,
        detail=f"{aligned} of {len(entries)} entries carry sim_time_ns",
    )


def _validation_pass_rate_metric(
    bundle: LoadedReplayBundle, notes: list[str]
) -> ReplayCoverageMetric:
    """Fraction of replay-validation results with status=passed."""

    if bundle.replay_report is None:
        return ReplayCoverageMetric(
            name="replay_validation_pass_rate",
            value=None,
            available=False,
            detail="no replay report",
        )
    results = bundle.replay_report.get("validation_results", []) or []
    if not results:
        return ReplayCoverageMetric(
            name="replay_validation_pass_rate",
            value=None,
            available=False,
            detail="replay report has no validation results",
        )
    passed = sum(1 for r in results if r.get("status") == "passed")
    pct = round(100.0 * passed / len(results), 2)
    return ReplayCoverageMetric(
        name="replay_validation_pass_rate",
        value=pct,
        available=True,
        detail=f"{passed} of {len(results)} validation result(s) passed",
    )


def _evidence_completeness_metric(
    bundle: LoadedReplayBundle, notes: list[str]
) -> ReplayCoverageMetric:
    """Score derived from the Phase-6 evidence_status."""

    mapping = {
        "complete": 100.0,
        "live_runtime": 100.0,
        "partial": 60.0,
        "static_only": 30.0,
        "not_executed": 25.0,
        "missing": 0.0,
        "inconsistent": 10.0,
    }
    if not bundle.evidence_status:
        return ReplayCoverageMetric(
            name="evidence_completeness_pct",
            value=None,
            available=False,
            detail="no incident report (evidence_status unknown)",
        )
    value = mapping.get(bundle.evidence_status)
    if value is None:
        notes.append(
            f"unrecognised evidence_status {bundle.evidence_status!r}; "
            "treating as 0%"
        )
        value = 0.0
    return ReplayCoverageMetric(
        name="evidence_completeness_pct",
        value=value,
        available=True,
        detail=f"evidence_status={bundle.evidence_status}",
    )


def _review_artifact_completeness_metric(
    bundle: LoadedReplayBundle, notes: list[str]
) -> ReplayCoverageMetric:
    """Fraction of canonical review artefacts present in the bundle dir."""

    incident_dir = bundle.incident_dir
    present = 0
    for name in _REQUIRED_REVIEW_ARTIFACTS:
        if (incident_dir / name).exists():
            present += 1
    pct = round(100.0 * present / len(_REQUIRED_REVIEW_ARTIFACTS), 2)
    return ReplayCoverageMetric(
        name="review_artifact_completeness_pct",
        value=pct,
        available=True,
        detail=(
            f"{present} of {len(_REQUIRED_REVIEW_ARTIFACTS)} canonical "
            "review artefact(s) present"
        ),
    )


# ---------------------------------------------------------------------------
# Aggregation.
# ---------------------------------------------------------------------------


def _aggregate_status(
    bundle: LoadedReplayBundle, metrics: list[ReplayCoverageMetric]
) -> ReplayCoverageStatus:
    """Map the metrics + bag status to a coverage label.

    The aggregate is deterministic and conservative: static-only or
    missing-bag inputs cannot reach ``substantial``/``complete``.
    """

    bag_status = bundle.bag_status
    if not bundle.has_replay_review:
        return ReplayCoverageStatus.MISSING
    if bag_status == "static_only":
        return ReplayCoverageStatus.SPARSE
    if bag_status == "missing_bag":
        return ReplayCoverageStatus.SPARSE
    available = [m for m in metrics if m.available and m.value is not None]
    if not available:
        return ReplayCoverageStatus.PARTIAL
    avg = sum(m.value for m in available) / len(available)
    if bag_status == "ready" and avg >= 90.0:
        return ReplayCoverageStatus.COMPLETE
    if bag_status in {"ready", "partial", "passed"} and avg >= 75.0:
        return ReplayCoverageStatus.SUBSTANTIAL
    if avg >= 50.0:
        return ReplayCoverageStatus.PARTIAL
    return ReplayCoverageStatus.SPARSE
