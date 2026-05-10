"""Loader for the Phase 8 analytics layer.

Reads the artefacts produced by Phase 6 (incident reconstruction)
and Phase 7 (replay review) for a single incident bundle. The
loader is defensive: missing files become structured warnings, not
exceptions, and the analytics layer downstream treats unavailable
inputs honestly.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


_REPORT_FILES: tuple[str, ...] = (
    "incident-report.json",
    "replay-review-manifest.json",
    "replay-review-report.json",
    "replay-markers.json",
    "foxglove-session.json",
)


@dataclass
class LoadedReplayBundle:
    """A loaded incident bundle with its replay-review artefacts."""

    incident_dir: Path
    incident_report: Optional[dict] = None
    replay_manifest: Optional[dict] = None
    replay_report: Optional[dict] = None
    markers: list[dict] = field(default_factory=list)
    foxglove_session: Optional[dict] = None
    review_audit: Optional[dict] = None
    """Optional explicit operator-review audit metadata."""

    warnings: list[str] = field(default_factory=list)

    @property
    def incident_id(self) -> str:
        if self.incident_report:
            return self.incident_report.get("incident_id") or self.incident_dir.name
        return self.incident_dir.name

    @property
    def has_replay_review(self) -> bool:
        return self.replay_manifest is not None and self.replay_report is not None

    @property
    def evidence_status(self) -> str:
        if self.incident_report:
            return self.incident_report.get("evidence_status", "")
        return ""

    @property
    def bag_status(self) -> str:
        if self.replay_manifest:
            return self.replay_manifest.get("bag_status", "missing_bag")
        return "missing_bag"

    @property
    def evidence_origin(self) -> str:
        if self.replay_report:
            return self.replay_report.get("evidence_origin", "unknown")
        return "unknown"

    def as_dict(self) -> dict:
        return {
            "incident_dir": str(self.incident_dir),
            "incident_id": self.incident_id,
            "has_replay_review": self.has_replay_review,
            "warnings": list(self.warnings),
        }


def load_replay_bundle(incident_dir: Path) -> LoadedReplayBundle:
    """Load every replay-review artefact under ``incident_dir``.

    Files that are missing or malformed do not raise; the loader
    records a structured warning and the analytics layer treats the
    inputs as unavailable.
    """

    incident_dir = Path(incident_dir)
    bundle = LoadedReplayBundle(incident_dir=incident_dir)
    if not incident_dir.exists() or not incident_dir.is_dir():
        bundle.warnings.append(f"incident dir missing: {incident_dir}")
        return bundle

    for name, attr in (
        ("incident-report.json", "incident_report"),
        ("replay-review-manifest.json", "replay_manifest"),
        ("replay-review-report.json", "replay_report"),
        ("foxglove-session.json", "foxglove_session"),
        ("review-audit.json", "review_audit"),
    ):
        path = incident_dir / name
        payload = _load_json(path, bundle.warnings)
        setattr(bundle, attr, payload)

    markers_path = incident_dir / "replay-markers.json"
    payload = _load_json(markers_path, bundle.warnings)
    if isinstance(payload, list):
        bundle.markers = list(payload)
    elif payload is not None:
        bundle.warnings.append(
            f"replay-markers.json has unexpected shape (expected list): "
            f"{type(payload).__name__}"
        )

    return bundle


def load_replay_bundles(
    incidents_root: Path,
    *,
    skip_dirs: tuple[str, ...] = ("comparisons", "analytics"),
) -> list[LoadedReplayBundle]:
    """Scan ``incidents_root`` and load every immediate subdirectory."""

    incidents_root = Path(incidents_root)
    out: list[LoadedReplayBundle] = []
    if not incidents_root.exists():
        return out
    for path in sorted(incidents_root.iterdir()):
        if not path.is_dir() or path.name in skip_dirs:
            continue
        out.append(load_replay_bundle(path))
    return out


def _load_json(path: Path, warnings: list[str]) -> Optional[object]:
    if not path.exists():
        # Missing files are common (replay-review may not have been run
        # yet); only record the most actionable ones explicitly.
        if path.name in {"incident-report.json"}:
            warnings.append(f"required file missing: {path.name}")
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        warnings.append(f"could not read {path.name}: {exc}")
        return None
    if not text.strip():
        warnings.append(f"{path.name} is empty")
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        warnings.append(f"{path.name} did not parse: {exc}")
        return None
