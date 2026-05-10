"""Evidence freshness reporter.

Compares each artefact's recorded ``generated_at_utc`` against a
caller-supplied reference time. The layer never calls
``datetime.now()`` internally so tests are deterministic.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from app.programme_review.models import (
    FreshnessEntry,
    FreshnessReport,
    FreshnessStatus,
    HistoryRecord,
    LoadedHistory,
)


_DEFAULT_THRESHOLDS_SECONDS: dict[str, int] = {
    "reliability_impact": 14 * 24 * 3600,
    "replay_analytics": 14 * 24 * 3600,
    "runtime_qualification": 30 * 24 * 3600,
    "replay_review": 30 * 24 * 3600,
    "incident": 60 * 24 * 3600,
}


def assess_freshness(
    *,
    history: LoadedHistory,
    reference_time_utc: datetime,
    thresholds_seconds: Optional[dict[str, int]] = None,
) -> FreshnessReport:
    """Return per-artefact freshness entries.

    ``reference_time_utc`` is supplied by the caller. CI passes
    ``datetime.now(tz=timezone.utc)``; tests supply fixture
    timestamps so the report is deterministic.
    """

    if reference_time_utc.tzinfo is None:
        reference_time_utc = reference_time_utc.replace(tzinfo=timezone.utc)
    thresholds = dict(_DEFAULT_THRESHOLDS_SECONDS)
    if thresholds_seconds:
        thresholds.update(thresholds_seconds)

    entries: list[FreshnessEntry] = []
    notes: list[str] = []
    for record in history.all_records():
        threshold = thresholds.get(record.record_type, 30 * 24 * 3600)
        entry = _entry_for(
            record=record,
            reference_time_utc=reference_time_utc,
            threshold_seconds=threshold,
        )
        entries.append(entry)
    return FreshnessReport(
        reference_time_utc=reference_time_utc.isoformat(timespec="seconds"),
        entries=entries,
        notes=tuple(notes),
    )


def _entry_for(
    *,
    record: HistoryRecord,
    reference_time_utc: datetime,
    threshold_seconds: int,
) -> FreshnessEntry:
    age = _age_seconds(record.generated_at_utc, reference_time_utc)
    if age is None:
        return FreshnessEntry(
            record_type=record.record_type,
            record_id=record.record_id,
            source_path=str(record.source_path),
            generated_at_utc=record.generated_at_utc,
            age_seconds=None,
            threshold_seconds=threshold_seconds,
            status=FreshnessStatus.UNKNOWN,
            notes="no parseable generated_at_utc on record",
        )
    if age > threshold_seconds:
        return FreshnessEntry(
            record_type=record.record_type,
            record_id=record.record_id,
            source_path=str(record.source_path),
            generated_at_utc=record.generated_at_utc,
            age_seconds=age,
            threshold_seconds=threshold_seconds,
            status=FreshnessStatus.STALE,
            notes=(
                f"age {age}s exceeds threshold {threshold_seconds}s"
            ),
        )
    return FreshnessEntry(
        record_type=record.record_type,
        record_id=record.record_id,
        source_path=str(record.source_path),
        generated_at_utc=record.generated_at_utc,
        age_seconds=age,
        threshold_seconds=threshold_seconds,
        status=FreshnessStatus.FRESH,
    )


def _age_seconds(
    timestamp: str, reference_time_utc: datetime
) -> Optional[int]:
    if not timestamp:
        return None
    try:
        parsed = datetime.fromisoformat(timestamp)
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    delta = reference_time_utc - parsed
    seconds = int(delta.total_seconds())
    return max(seconds, 0)
