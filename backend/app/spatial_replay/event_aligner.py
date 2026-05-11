"""Align rehearsal events with pose samples.

The aligner is purely temporal: each event's ``event_time_ns`` is
matched to the nearest sample's ``time_ns``. Events that fall
outside the configured tolerance produce an alignment with
``matched_sample_id`` empty and ``spatial_position = None`` — the UI
then renders the event in the timeline only.
"""

from __future__ import annotations

from typing import Iterable, Mapping

from .models import EventAlignment, PoseSample


# Default tolerance: 250 ms. Events further than this from any
# sample are not placed on the map.
DEFAULT_ALIGNMENT_TOLERANCE_NS: int = 250_000_000


def _nearest_sample(
    time_ns: int, samples: tuple[PoseSample, ...]
) -> tuple[PoseSample | None, int]:
    """Return (nearest_sample, delta_ns) or (None, 0) for empty input."""

    if not samples:
        return None, 0
    best: PoseSample | None = None
    best_delta: int | None = None
    for sample in samples:
        delta = abs(sample.time_ns - time_ns)
        if best_delta is None or delta < best_delta:
            best = sample
            best_delta = delta
    return best, (best_delta or 0)


def align_event(
    event: Mapping[str, object],
    samples: tuple[PoseSample, ...],
    *,
    tolerance_ns: int = DEFAULT_ALIGNMENT_TOLERANCE_NS,
) -> EventAlignment:
    """Align one event to its nearest pose sample.

    ``event`` is treated as a generic mapping so the aligner does not
    need to import the rehearsal event class; this keeps the package
    free of cross-package dependencies.
    """

    event_id = str(event.get("event_id") or "")
    deterministic_hash = str(event.get("deterministic_hash") or "")
    time_ns = int(event.get("event_time_ns", 0) or 0)
    nearest, delta = _nearest_sample(time_ns, samples)
    if nearest is None or delta > tolerance_ns:
        return EventAlignment(
            event_id=event_id,
            deterministic_hash=deterministic_hash,
            matched_sample_id="",
            spatial_position=None,
            delta_time_ns=delta,
            confidence="unaligned",
        )
    return EventAlignment(
        event_id=event_id,
        deterministic_hash=deterministic_hash,
        matched_sample_id=nearest.sample_id,
        spatial_position=(nearest.x_m, nearest.y_m),
        delta_time_ns=delta,
        confidence=nearest.confidence,
    )


def align_events(
    events: Iterable[Mapping[str, object]],
    samples: tuple[PoseSample, ...],
    *,
    tolerance_ns: int = DEFAULT_ALIGNMENT_TOLERANCE_NS,
) -> tuple[EventAlignment, ...]:
    """Return one alignment per event, in the same order as input."""

    return tuple(align_event(ev, samples, tolerance_ns=tolerance_ns) for ev in events)


__all__ = [
    "DEFAULT_ALIGNMENT_TOLERANCE_NS",
    "align_event",
    "align_events",
]
