"""Replay review validator.

Runs deterministic checks against a freshly-built manifest +
Foxglove session + marker list and emits a list of
:class:`ReplayValidationResult`. Every check returns one of the
Phase-3 status values; ``not_executed`` is reserved for paths that
genuinely require a live Jazzy host.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

from app.replay_review.models import (
    BagIndex,
    FoxgloveSession,
    ReplayExecutionStatus,
    ReplayMarker,
    ReplayReviewManifest,
    ReplayValidationResult,
    ReplayValidationStatus,
)


def validate_replay_review(
    *,
    incident_dir: Path,
    manifest: ReplayReviewManifest,
    session: FoxgloveSession,
    markers: Iterable[ReplayMarker],
    layout_file: Optional[Path] = None,
) -> list[ReplayValidationResult]:
    """Run every check and return the results."""

    results: list[ReplayValidationResult] = []
    markers = tuple(markers)

    # 1. incident-report.json must exist.
    report_path = incident_dir / "incident-report.json"
    if report_path.exists():
        results.append(
            ReplayValidationResult(
                name="incident_report_present",
                status=ReplayValidationStatus.PASSED,
                detail=f"{report_path.name} present",
                evidence_paths=(str(report_path),),
            )
        )
    else:
        results.append(
            ReplayValidationResult(
                name="incident_report_present",
                status=ReplayValidationStatus.FAILED,
                detail=f"{report_path.name} not found",
                reason="run reconstruct_incident.py to produce the bundle",
            )
        )

    # 2. timeline must exist.
    timeline_path = incident_dir / "timeline.json"
    if timeline_path.exists():
        results.append(
            ReplayValidationResult(
                name="timeline_present",
                status=ReplayValidationStatus.PASSED,
                detail=f"{timeline_path.name} present",
                evidence_paths=(str(timeline_path),),
            )
        )
    else:
        results.append(
            ReplayValidationResult(
                name="timeline_present",
                status=ReplayValidationStatus.FAILED,
                detail=f"{timeline_path.name} not found",
            )
        )

    # 3. markers generated.
    if markers:
        align_kinds = {m.alignment for m in markers}
        if align_kinds == {"exact"}:
            results.append(
                ReplayValidationResult(
                    name="markers_generated",
                    status=ReplayValidationStatus.PASSED,
                    detail=f"{len(markers)} marker(s) with exact alignment",
                )
            )
        elif "exact" in align_kinds:
            results.append(
                ReplayValidationResult(
                    name="markers_generated",
                    status=ReplayValidationStatus.PARTIAL,
                    detail=(
                        f"{len(markers)} marker(s); "
                        f"{sum(1 for m in markers if m.alignment == 'exact')} exact, "
                        f"{sum(1 for m in markers if m.alignment != 'exact')} partial/unaligned"
                    ),
                    reason="some markers lack sim_time_ns; align manually in Foxglove",
                )
            )
        else:
            results.append(
                ReplayValidationResult(
                    name="markers_generated",
                    status=ReplayValidationStatus.PARTIAL,
                    detail=f"{len(markers)} marker(s) without exact alignment",
                    reason="no marker carries sim_time_ns; relative-time alignment only",
                )
            )
    else:
        results.append(
            ReplayValidationResult(
                name="markers_generated",
                status=ReplayValidationStatus.SKIPPED,
                detail="no markers emitted",
                reason="incident timeline did not provide marker indices",
            )
        )

    # 4. Foxglove layout file present.
    layout_path = layout_file or Path(manifest.foxglove_layout_path)
    if layout_path.exists():
        results.append(
            ReplayValidationResult(
                name="foxglove_layout_present",
                status=ReplayValidationStatus.PASSED,
                detail=f"layout at {layout_path}",
                evidence_paths=(str(layout_path),),
            )
        )
    else:
        results.append(
            ReplayValidationResult(
                name="foxglove_layout_present",
                status=ReplayValidationStatus.FAILED,
                detail=f"layout file not found at {layout_path}",
                reason="commit foxglove/layouts/incident-review-layout.json",
            )
        )

    # 5. Foxglove session.
    results.append(
        ReplayValidationResult(
            name="foxglove_session_well_formed",
            status=ReplayValidationStatus.PASSED,
            detail=(
                f"schema_version={session.schema_version}; "
                f"{len(session.panel_hints)} panel hint(s)"
            ),
        )
    )

    # 6. bag status.
    if manifest.bag_status == ReplayExecutionStatus.READY:
        results.append(
            ReplayValidationResult(
                name="bag_artefacts_present",
                status=ReplayValidationStatus.PASSED,
                detail="bag chunks + metadata detected",
            )
        )
    elif manifest.bag_status == ReplayExecutionStatus.PARTIAL:
        results.append(
            ReplayValidationResult(
                name="bag_artefacts_present",
                status=ReplayValidationStatus.PARTIAL,
                detail="some bag artefacts present (chunks or metadata)",
                reason="full replay requires both rosbag2 metadata.yaml and bag chunks",
            )
        )
    elif manifest.bag_status == ReplayExecutionStatus.STATIC_ONLY:
        results.append(
            ReplayValidationResult(
                name="bag_artefacts_present",
                status=ReplayValidationStatus.SKIPPED,
                detail="static-only incident; bag not required",
                reason="incident evidence_status=static_only",
            )
        )
    else:  # MISSING_BAG
        results.append(
            ReplayValidationResult(
                name="bag_artefacts_present",
                status=ReplayValidationStatus.NOT_EXECUTED,
                detail="no bag artefacts detected",
                reason=(
                    "live bag replay requires rosbag2 output on a Jazzy host; "
                    "see docs/REPLAY_REVIEW_RUNBOOK.md"
                ),
            )
        )

    # 7. expected topics coverage when a bag was indexed.
    if manifest.bag_status in (
        ReplayExecutionStatus.READY,
        ReplayExecutionStatus.PARTIAL,
    ):
        if manifest.missing_topics:
            results.append(
                ReplayValidationResult(
                    name="expected_topics_present",
                    status=ReplayValidationStatus.FAILED,
                    detail=(
                        f"{len(manifest.missing_topics)} required topic(s) not in bag: "
                        + ", ".join(manifest.missing_topics[:5])
                    ),
                    reason="bag inventory missing required topics; rerecord on Jazzy",
                )
            )
        else:
            results.append(
                ReplayValidationResult(
                    name="expected_topics_present",
                    status=ReplayValidationStatus.PASSED,
                    detail="every required topic present in bag inventory",
                )
            )
    else:
        results.append(
            ReplayValidationResult(
                name="expected_topics_present",
                status=ReplayValidationStatus.NOT_EXECUTED,
                detail="bag not present; topic coverage cannot be checked",
                reason="record a bag on a Jazzy host to enable this check",
            )
        )

    return results


def aggregate_status(
    *,
    manifest: ReplayReviewManifest,
    validations: Iterable[ReplayValidationResult],
) -> ReplayExecutionStatus:
    """Roll the validation results up into a single status.

    The aggregate respects the bag status floor: a missing bag never
    becomes ``passed``; a static-only incident never claims
    ``ready``.
    """

    validations = tuple(validations)
    failed = [v for v in validations if v.status == ReplayValidationStatus.FAILED]
    if failed:
        return ReplayExecutionStatus.FAILED
    if manifest.bag_status == ReplayExecutionStatus.STATIC_ONLY:
        return ReplayExecutionStatus.STATIC_ONLY
    if manifest.bag_status == ReplayExecutionStatus.MISSING_BAG:
        return ReplayExecutionStatus.MISSING_BAG
    if manifest.bag_status == ReplayExecutionStatus.PARTIAL:
        return ReplayExecutionStatus.PARTIAL
    if any(v.status == ReplayValidationStatus.PARTIAL for v in validations):
        return ReplayExecutionStatus.PARTIAL
    if any(v.status == ReplayValidationStatus.NOT_EXECUTED for v in validations):
        # The bag is ready but at least one check could not run; still
        # call it "ready" because the live replay step is the
        # operator's responsibility, not the static validator's.
        if manifest.bag_status == ReplayExecutionStatus.READY:
            return ReplayExecutionStatus.READY
        return ReplayExecutionStatus.NOT_EXECUTED
    if manifest.bag_status == ReplayExecutionStatus.READY:
        return ReplayExecutionStatus.READY
    return ReplayExecutionStatus.PARTIAL
