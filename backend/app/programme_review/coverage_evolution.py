"""Coverage evolution tracker.

Walks the replay-review history in chronological order and emits a
:class:`CoverageEvolutionEntry` per record. Origin labels are
preserved verbatim; mixed-origin samples are surfaced via the
``origin_mix_label`` field so the report cannot silently aggregate
``static_only`` with ``bag_backed``.
"""

from __future__ import annotations

from typing import Optional

from app.programme_review.models import (
    CoverageEvolutionEntry,
    CoverageEvolutionReport,
    HistoryRecord,
    LoadedHistory,
)


def build_coverage_evolution(history: LoadedHistory) -> CoverageEvolutionReport:
    entries: list[CoverageEvolutionEntry] = []
    for record in history.replay_review:
        entries.append(_entry_from_record(record))
    origin_mix = _origin_mix_label(entries)
    notes: list[str] = []
    if not entries:
        notes.append("no replay-review reports loaded")
    return CoverageEvolutionReport(
        entries=entries,
        origin_mix_label=origin_mix,
        notes=tuple(notes),
    )


def _entry_from_record(record: HistoryRecord) -> CoverageEvolutionEntry:
    payload = record.payload
    return CoverageEvolutionEntry(
        timestamp=record.generated_at_utc,
        record_id=record.record_id,
        evidence_origin=str(payload.get("evidence_origin") or "unknown"),
        bag_status=str(payload.get("bag_status") or "unknown"),
        coverage_status=str(
            payload.get("coverage_status") or payload.get("replay_execution_status") or "unknown"
        ),
        review_completion_status=str(
            payload.get("review_completion_status") or "not_started"
        ),
        score=_score_from(payload),
    )


def _score_from(payload: dict) -> Optional[int]:
    score = payload.get("quality_score") or payload.get("score")
    if isinstance(score, (int, float)):
        return int(score)
    return None


def _origin_mix_label(entries: list[CoverageEvolutionEntry]) -> str:
    """Label the origin distribution explicitly.

    Returns one of:

    * ``unavailable`` — no entries;
    * ``static_only_only`` — every entry is ``scenario-evidence`` /
      ``static_only`` style;
    * ``bag_backed_only`` — every entry is ``bag-backed``;
    * ``mixed_origin`` — at least one of each, or any other mix.
    """

    if not entries:
        return "unavailable"
    origins = {e.evidence_origin for e in entries}
    if origins.issubset({"scenario-evidence", "runtime-evidence", "unknown"}):
        return "static_only_only"
    if origins == {"bag-backed"}:
        return "bag_backed_only"
    return "mixed_origin"
