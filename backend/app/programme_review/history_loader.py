"""Loader for the Phase 10 longitudinal history.

The loader walks the documented evidence roots and produces a
:class:`LoadedHistory` instance with one :class:`HistoryRecord` per
artefact. Malformed inputs become structured warnings; missing
directories yield empty lists. The loader never raises; the layer
above treats absence as ``insufficient_history``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from app.programme_review.models import HistoryRecord, LoadedHistory


# Default discovery layout. CI passes its own roots; tests use
# tmp_path-rooted fixtures.
DEFAULT_RELIABILITY_IMPACT_ROOTS: tuple[Path, ...] = (
    Path("reliability-impact"),
)
DEFAULT_REPLAY_ANALYTICS_PATH: Path = Path(
    "incidents/analytics/replay-analytics-report.json"
)
DEFAULT_REPLAY_ANALYTICS_QUALITY_PATH: Path = Path(
    "incidents/analytics/replay-quality-index.json"
)
DEFAULT_RUNTIME_EVIDENCE_ROOT: Path = Path("evidence/runtime")
DEFAULT_INCIDENTS_ROOT: Path = Path("incidents")


def load_history(
    *,
    reliability_impact_roots: Optional[Iterable[Path]] = None,
    replay_analytics_paths: Optional[Iterable[Path]] = None,
    runtime_evidence_root: Optional[Path] = None,
    incidents_root: Optional[Path] = None,
) -> LoadedHistory:
    """Walk the supplied roots and return a :class:`LoadedHistory`.

    The function never raises. Missing files become warnings;
    malformed JSON becomes a per-file warning attached to the
    affected record. Records are returned in chronological order
    (oldest first) when timestamps exist; records without a
    timestamp are appended at the end of their category.
    """

    history = LoadedHistory()

    # Reliability-impact bundles.
    roots = list(
        reliability_impact_roots or DEFAULT_RELIABILITY_IMPACT_ROOTS
    )
    for root in roots:
        history.reliability_impact.extend(
            _load_reliability_impact_under(root, history.warnings)
        )

    # Replay analytics history. The current canonical layout ships
    # one report per run id (the layer accepts a list of paths so
    # CI / fixtures can compose multiple snapshots).
    analytics_paths = (
        list(replay_analytics_paths)
        if replay_analytics_paths is not None
        else [DEFAULT_REPLAY_ANALYTICS_PATH]
    )
    for path in analytics_paths:
        record = _load_replay_analytics(path, history.warnings)
        if record is not None:
            history.replay_analytics.append(record)

    # Runtime qualification reports.
    runtime_root = runtime_evidence_root or DEFAULT_RUNTIME_EVIDENCE_ROOT
    history.runtime_qualification.extend(
        _load_runtime_qualification(runtime_root, history.warnings)
    )

    # Replay review reports (per incident).
    incidents_root_resolved = incidents_root or DEFAULT_INCIDENTS_ROOT
    history.replay_review.extend(
        _load_replay_reviews(incidents_root_resolved, history.warnings)
    )

    # Incident reports.
    history.incident.extend(
        _load_incidents(incidents_root_resolved, history.warnings)
    )

    # Sort each list chronologically (oldest first) by generated_at_utc;
    # records with no timestamp keep their discovery order and sort
    # to the end.
    for category in (
        history.reliability_impact,
        history.replay_analytics,
        history.runtime_qualification,
        history.replay_review,
        history.incident,
    ):
        category.sort(
            key=lambda r: (
                0 if r.generated_at_utc else 1,
                r.generated_at_utc or "",
                str(r.source_path),
            )
        )

    _flag_duplicates(history)
    return history


# ---------------------------------------------------------------------------
# Per-category loaders.
# ---------------------------------------------------------------------------


def _load_reliability_impact_under(
    root: Path, warnings: list[str]
) -> list[HistoryRecord]:
    out: list[HistoryRecord] = []
    if not root.exists():
        return out
    # Each reliability-impact bundle directory contains
    # impact-report.json. We walk the tree (one level deep + nested).
    candidates: list[Path] = []
    direct = root / "impact-report.json"
    if direct.is_file():
        candidates.append(direct)
    for sub in sorted(p for p in root.iterdir() if p.is_dir()):
        nested = sub / "impact-report.json"
        if nested.is_file():
            candidates.append(nested)
    for path in candidates:
        payload = _read_json(path, warnings)
        if payload is None:
            continue
        out.append(
            HistoryRecord(
                record_type="reliability_impact",
                source_path=path,
                payload=payload,
                generated_at_utc=str(payload.get("generated_at_utc", "")),
                record_id=_impact_record_id(payload, path),
            )
        )
    return out


def _load_replay_analytics(
    path: Path, warnings: list[str]
) -> Optional[HistoryRecord]:
    if not path.is_file():
        if path.parent.exists():
            warnings.append(f"replay analytics report missing: {path}")
        return None
    payload = _read_json(path, warnings)
    if payload is None:
        return None
    return HistoryRecord(
        record_type="replay_analytics",
        source_path=path,
        payload=payload,
        generated_at_utc=str(payload.get("generated_at_utc", "")),
        record_id=path.stem,
    )


def _load_runtime_qualification(
    runtime_root: Path, warnings: list[str]
) -> list[HistoryRecord]:
    out: list[HistoryRecord] = []
    if not runtime_root.exists():
        return out
    for run_dir in sorted(p for p in runtime_root.iterdir() if p.is_dir()):
        qual_path = run_dir / "qualification-summary.json"
        if not qual_path.is_file():
            continue
        payload = _read_json(qual_path, warnings)
        if payload is None:
            continue
        out.append(
            HistoryRecord(
                record_type="runtime_qualification",
                source_path=qual_path,
                payload=payload,
                generated_at_utc=str(payload.get("generated_at_utc", "")),
                record_id=str(
                    payload.get("run_id") or run_dir.name
                ),
            )
        )
    return out


def _load_replay_reviews(
    incidents_root: Path, warnings: list[str]
) -> list[HistoryRecord]:
    out: list[HistoryRecord] = []
    if not incidents_root.exists():
        return out
    for path in sorted(incidents_root.iterdir()):
        if not path.is_dir() or path.name in {"analytics", "comparisons"}:
            continue
        report = path / "replay-review-report.json"
        if not report.is_file():
            continue
        payload = _read_json(report, warnings)
        if payload is None:
            continue
        out.append(
            HistoryRecord(
                record_type="replay_review",
                source_path=report,
                payload=payload,
                generated_at_utc=str(payload.get("generated_at_utc", "")),
                record_id=str(payload.get("incident_id") or path.name),
            )
        )
    return out


def _load_incidents(
    incidents_root: Path, warnings: list[str]
) -> list[HistoryRecord]:
    out: list[HistoryRecord] = []
    if not incidents_root.exists():
        return out
    for path in sorted(incidents_root.iterdir()):
        if not path.is_dir() or path.name in {"analytics", "comparisons"}:
            continue
        report = path / "incident-report.json"
        if not report.is_file():
            continue
        payload = _read_json(report, warnings)
        if payload is None:
            continue
        out.append(
            HistoryRecord(
                record_type="incident",
                source_path=report,
                payload=payload,
                generated_at_utc=str(payload.get("generated_at_utc", "")),
                record_id=str(payload.get("incident_id") or path.name),
            )
        )
    return out


# ---------------------------------------------------------------------------
# Helpers.
# ---------------------------------------------------------------------------


def _impact_record_id(payload: dict, path: Path) -> str:
    head = payload.get("head_ref", "")
    base = payload.get("base_ref", "")
    if head:
        return f"{base or 'base'}..{head}"
    return path.parent.name or path.stem


def _read_json(path: Path, warnings: list[str]) -> Optional[dict]:
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
        warnings.append(f"{path} has unexpected shape ({type(payload).__name__})")
        return None
    return payload


def _flag_duplicates(history: LoadedHistory) -> None:
    """Annotate records that share a ``record_id`` within a category.

    Duplicate detection is informational — duplicates are not
    dropped, they are tagged in the ``notes`` field so the report
    can surface them.
    """

    for category in (
        history.reliability_impact,
        history.replay_analytics,
        history.runtime_qualification,
        history.replay_review,
        history.incident,
    ):
        seen: dict[str, int] = {}
        for record in category:
            if not record.record_id:
                continue
            seen[record.record_id] = seen.get(record.record_id, 0) + 1
        if not seen:
            continue
        dupes = {rid for rid, count in seen.items() if count > 1}
        if not dupes:
            continue
        history.warnings.append(
            "duplicate record_id(s) in "
            f"{category[0].record_type if category else 'unknown'}: "
            + ", ".join(sorted(dupes))
        )
        for record in category:
            if record.record_id in dupes:
                record.notes = tuple(list(record.notes) + ["duplicate_record_id"])
