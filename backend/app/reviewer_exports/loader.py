"""Defensive loader for the reviewer-export package.

Walks the documented evidence roots and returns a
:class:`LoadedReviewerInputs`. Missing files become structured
warnings; malformed JSON does not raise. The exporters downstream
treat absent inputs as "emit zero rows + record the absence in the
manifest", never as a failure.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Optional

from app.reviewer_exports.models import LoadedReviewerInputs


def load_reviewer_inputs(
    *,
    programme_review_root: Optional[Path] = None,
    incidents_root: Optional[Path] = None,
    reliability_impact_root: Optional[Path] = None,
    traceability_path: Optional[Path] = None,
) -> LoadedReviewerInputs:
    """Read every documented input. Missing inputs become warnings."""

    loaded = LoadedReviewerInputs()

    pr_root = programme_review_root or Path("programme-review")
    loaded.programme_review_path = pr_root / "programme-review.json"
    loaded.programme_review = _read_json(
        loaded.programme_review_path, loaded.warnings
    )
    loaded.governance_dashboard_path = pr_root / "governance-dashboard.json"
    loaded.governance_dashboard = _read_json(
        loaded.governance_dashboard_path, loaded.warnings
    )
    loaded.trend_report_path = pr_root / "trend-report.json"
    loaded.trend_report = _read_json(loaded.trend_report_path, loaded.warnings)
    loaded.drift_report_path = pr_root / "drift-report.json"
    loaded.drift_report = _read_json(loaded.drift_report_path, loaded.warnings)
    loaded.subsystem_risk_report_path = pr_root / "subsystem-risk-report.json"
    loaded.subsystem_risk_report = _read_json(
        loaded.subsystem_risk_report_path, loaded.warnings
    )
    loaded.gate_history_path = pr_root / "gate-history.json"
    loaded.gate_history = _read_json(loaded.gate_history_path, loaded.warnings)

    inc_root = incidents_root or Path("incidents")
    analytics_root = inc_root / "analytics"
    loaded.replay_quality_index_path = analytics_root / "replay-quality-index.json"
    loaded.replay_quality_index = _read_json(
        loaded.replay_quality_index_path, loaded.warnings
    )

    loaded.incident_index_path = inc_root / "index.json"
    loaded.incident_index = _read_json(
        loaded.incident_index_path, loaded.warnings
    )

    impact_root = reliability_impact_root or Path("reliability-impact")
    loaded.impact_reports, loaded.impact_report_paths = _load_impact_reports(
        impact_root, loaded.warnings
    )

    trace_path = traceability_path or Path("verification/traceability.json")
    loaded.traceability_path = trace_path
    loaded.traceability = _read_json(trace_path, loaded.warnings)

    return loaded


def _read_json(path: Optional[Path], warnings: list[str]) -> Optional[dict]:
    if path is None or not path.exists():
        if path is not None:
            warnings.append(f"input not present: {path}")
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        warnings.append(f"could not read {path}: {exc}")
        return None
    if not text.strip():
        warnings.append(f"{path} is empty")
        return None
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        warnings.append(f"{path} did not parse: {exc}")
        return None
    if not isinstance(payload, dict):
        warnings.append(
            f"{path} has unexpected shape ({type(payload).__name__})"
        )
        return None
    return payload


def _load_impact_reports(
    root: Path, warnings: list[str]
) -> tuple[list[dict], list[Path]]:
    """Walk ``reliability-impact/`` for every ``impact-report.json``."""

    if not root.exists():
        return [], []
    reports: list[dict] = []
    paths: list[Path] = []
    direct = root / "impact-report.json"
    if direct.is_file():
        payload = _read_json(direct, warnings)
        if payload is not None:
            reports.append(payload)
            paths.append(direct)
    for entry in sorted(p for p in root.iterdir() if p.is_dir()):
        nested = entry / "impact-report.json"
        if nested.is_file():
            payload = _read_json(nested, warnings)
            if payload is not None:
                reports.append(payload)
                paths.append(nested)
    return reports, paths
