"""Bag-manifest loading and eligibility checks for spatial replay.

The eligibility check is the most important honesty boundary in
Phase 17C: it is the only gatekeeper that can produce a
``bag_backed`` derivation source. The check fails closed — any
missing or ambiguous evidence demotes the run to ``fixture`` /
``bounded_inputs`` / ``topology_only`` / ``unavailable``.
"""

from __future__ import annotations

from pathlib import Path

from app.live_runtime.bag_manifest import load_bag_manifest, validate_bag_manifest
from app.live_runtime.models import (
    BAG_STATUS_BAG_BACKED,
    BAG_STATUS_PARTIAL,
    BagManifest,
)

from .models import BagEligibility


def runtime_run_dir(evidence_root: Path, run_id: str) -> Path:
    """Resolve the evidence directory for a given run id."""

    return Path(evidence_root) / "runtime" / run_id


def load_run_manifest(evidence_root: Path, run_id: str) -> BagManifest | None:
    """Load the bag manifest for a run; return ``None`` if missing."""

    path = runtime_run_dir(evidence_root, run_id) / "bag-manifest.json"
    return load_bag_manifest(path)


def evaluate_bag_eligibility(
    manifest: BagManifest | None,
    *,
    bundle_root: Path | None,
    has_pose_samples: bool,
) -> BagEligibility:
    """Return whether the run honestly qualifies as bag-backed.

    The function never raises; it returns a :class:`BagEligibility`
    with a list of human-readable reasons explaining the demotion.
    """

    reasons: list[str] = []

    if manifest is None:
        return BagEligibility(False, ("bag manifest missing or unparseable",))

    if manifest.bag_status != BAG_STATUS_BAG_BACKED:
        reasons.append(
            f"bag_status={manifest.bag_status!r}, not {BAG_STATUS_BAG_BACKED!r}"
        )

    if not manifest.bag_paths:
        reasons.append("manifest has no bag_paths")

    if not manifest.metadata_yaml_path:
        reasons.append("manifest has no metadata_yaml_path")

    # The shared validator confirms the paths on disk + topic coverage.
    warnings = validate_bag_manifest(manifest, bundle_root=bundle_root)
    for w in warnings:
        # Only fail the eligibility check on warnings that contradict
        # the bag-backed claim. Soft warnings (e.g. missing required
        # topics) demote to partial via the trajectory builder.
        if "bag path missing" in w or "metadata yaml missing" in w:
            reasons.append(w)

    if not has_pose_samples:
        reasons.append("no pose samples extracted from manifest topics")

    if manifest.validation_status not in ("passed", "partial"):
        reasons.append(
            f"validation_status={manifest.validation_status!r} blocks bag_backed"
        )

    if reasons:
        return BagEligibility(False, tuple(reasons))
    return BagEligibility(True, ())


def manifest_bag_status(manifest: BagManifest | None) -> str:
    """Return the manifest's bag_status, or ``'missing_manifest'``."""

    if manifest is None:
        return "missing_manifest"
    return manifest.bag_status


__all__ = [
    "BAG_STATUS_BAG_BACKED",
    "BAG_STATUS_PARTIAL",
    "evaluate_bag_eligibility",
    "load_run_manifest",
    "manifest_bag_status",
    "runtime_run_dir",
]
