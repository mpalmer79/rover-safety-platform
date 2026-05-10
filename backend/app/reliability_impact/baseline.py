"""Reliability baseline management.

The baseline pin is intentional. Callers either supply explicit
paths or fall back to the canonical files under
``reliability-baselines/``. CI never auto-updates a baseline.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from app.reliability_impact.models import BaselineReference


DEFAULT_BASELINE_ROOT = Path("reliability-baselines")
DEFAULT_QUALITY_INDEX = "replay-quality-index.baseline.json"
DEFAULT_ANALYTICS_REPORT = "replay-analytics-report.baseline.json"


def resolve_baseline(
    *,
    quality_index: Optional[Path] = None,
    analytics_report: Optional[Path] = None,
    baseline_root: Optional[Path] = None,
) -> BaselineReference:
    """Resolve the baseline files.

    Order:

    1. Explicit ``quality_index`` / ``analytics_report`` paths.
    2. Canonical names under ``baseline_root`` (default
       ``reliability-baselines/``).
    3. ``None`` for each missing path; the caller treats absence as
       a warning, never as a failure.
    """

    root = baseline_root or DEFAULT_BASELINE_ROOT
    resolved_quality = quality_index
    resolved_analytics = analytics_report

    if resolved_quality is None:
        candidate = root / DEFAULT_QUALITY_INDEX
        resolved_quality = candidate if candidate.exists() else None
    if resolved_analytics is None:
        candidate = root / DEFAULT_ANALYTICS_REPORT
        resolved_analytics = candidate if candidate.exists() else None

    notes_parts: list[str] = []
    if resolved_quality is None:
        notes_parts.append(
            f"baseline replay-quality-index missing (looked in {root}/)"
        )
    if resolved_analytics is None:
        notes_parts.append(
            f"baseline analytics-report missing (looked in {root}/)"
        )
    notes = "; ".join(notes_parts)

    return BaselineReference(
        quality_index_path=resolved_quality,
        analytics_report_path=resolved_analytics,
        notes=notes,
    )


def write_baseline(
    *,
    quality_index_source: Optional[Path] = None,
    analytics_report_source: Optional[Path] = None,
    baseline_root: Optional[Path] = None,
) -> BaselineReference:
    """Copy current analytics outputs into the baseline directory.

    The caller is expected to opt in explicitly (e.g. via a CLI
    ``--write-baseline`` flag). Files that are missing on disk are
    skipped silently — the resulting reference simply lacks that
    path.
    """

    root = baseline_root or DEFAULT_BASELINE_ROOT
    root.mkdir(parents=True, exist_ok=True)
    quality_dst: Optional[Path] = None
    analytics_dst: Optional[Path] = None
    if (
        quality_index_source is not None
        and quality_index_source.exists()
    ):
        quality_dst = root / DEFAULT_QUALITY_INDEX
        quality_dst.write_text(
            quality_index_source.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    if (
        analytics_report_source is not None
        and analytics_report_source.exists()
    ):
        analytics_dst = root / DEFAULT_ANALYTICS_REPORT
        analytics_dst.write_text(
            analytics_report_source.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    return BaselineReference(
        quality_index_path=quality_dst,
        analytics_report_path=analytics_dst,
        notes="baseline written via explicit operator action",
    )


def load_baseline_payload(path: Optional[Path]) -> Optional[dict]:
    """Defensive JSON read. Returns ``None`` if the file is absent or unparseable."""

    if path is None or not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
